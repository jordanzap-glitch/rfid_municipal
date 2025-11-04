from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request,'center_staff/home.html')

def MED_FORM(request):
    medicines = Medicines.objects.all()
    context = { 'medicines': medicines }
    # Implement PRG: if user was redirected after successful POST,
    # a `recent_bsr` dict will be stored in session. Pop it on GET
    # so the template can show the modal once without resubmitting.
    if request.method != 'POST':
        recent_bsr = request.session.pop('recent_bsr', None)
        if recent_bsr:
            context['recent_bsr'] = recent_bsr
    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        age = request.POST.get('age')
        amount = request.POST.get('amount')
        # checkbox fields and diagnosis
        barangay_indigency = bool(request.POST.get('barangay_indigency'))
        barangay_recidency = bool(request.POST.get('barangay_recidency'))
        diagnosis = request.POST.get('diagnosis')
        # multiple medicines can be submitted with the same name -> use getlist
        medicines_ids = request.POST.getlist('medicines')
        date_claimed = request.POST.get('date_claimed')
        date_claim_expiry = request.POST.get('date_claim_expiry')
        # Get registration object
        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'center_staff/form.html', context)

        if not medicines_ids:
            messages.error(request, 'No medicine selected.')
            return render(request, 'center_staff/form.html', context)

        from datetime import date
        from decimal import Decimal, InvalidOperation
        today = date.today()

        # If any existing assistance for this registration is still active
        # (date_claim_expiry >= today), prevent creating another assistance.
        active_bsr_exists = Bsrcenter.objects.filter(
            registration=registration,
            date_claim_expiry__gte=today
        ).exists()
        if active_bsr_exists:
            messages.error(request, 'Cannot save assistance: there is existing assistance that has not yet expired.')
            return render(request, 'center_staff/form.html', context)

        success_count = 0
        errors = []

        # normalize numeric input
        try:
            age_val = int(age) if age not in (None, '') else 0
        except (ValueError, TypeError):
            age_val = 0
        try:
            amount_val = Decimal(amount) if amount not in (None, '') else Decimal('0.00')
        except (InvalidOperation, TypeError):
            amount_val = Decimal('0.00')

        # Convert date_claim_expiry to date object if provided
        from datetime import datetime as _dt
        expiry_date_obj = None
        if date_claim_expiry:
            try:
                expiry_date_obj = _dt.strptime(date_claim_expiry, '%Y-%m-%d').date()
            except Exception:
                expiry_date_obj = None

        # Validate medicines and collect ones that can be saved
        valid_medicines = []
        for mid in medicines_ids:
            try:
                medicine = Medicines.objects.get(id=mid)
            except Medicines.DoesNotExist:
                errors.append(f'Medicine not found (id={mid}).')
                continue

            # Prevent duplicate assistance if not expired and approved
            existing = Bsrcenter_meds.objects.filter(
                medicines=medicine,
                bsrcenter__registration=registration,
                bsrcenter__status='approved',
                bsrcenter__date_claim_expiry__gte=today
            ).exists()
            if existing:
                errors.append(f'Cannot save assistance for "{medicine.medicine_name}": previous approved assistance is still active.')
                continue

            valid_medicines.append(medicine)

        if not valid_medicines:
            messages.error(request, 'No valid medicines to save.')
            for e in errors:
                messages.error(request, e)
            return render(request, 'center_staff/form.html', context)

        # Create a single Bsrcenter record and link all valid medicines to it
        from django.db import transaction
        bsr = None
        recent_bsr = None
        try:
            with transaction.atomic():
                # generate a unique tracking number like CC(XXXXXXXX)
                import uuid

                def _gen_tracking():
                    return f"CC-{uuid.uuid4().hex[:10].upper()}" #remember to change CC to other letters if needed

                tracking = _gen_tracking()
                # ensure uniqueness
                while Bsrcenter.objects.filter(tracking_number=tracking).exists():
                    tracking = _gen_tracking()

                bsr = Bsrcenter.objects.create(
                    registration=registration,
                    age=age_val,
                    amount=amount_val,
                    tracking_number=tracking,
                    # date_claimed is auto_now_add on the model; we only set expiry
                    date_claim_expiry=expiry_date_obj or date_claim_expiry,
                    status='pending',
                    barangay_indigency=barangay_indigency,
                    barangay_recidency=barangay_recidency,
                    diagnosis=diagnosis or ''
                )

                for medicine in valid_medicines:
                    Bsrcenter_meds.objects.create(
                        bsrcenter=bsr,
                        medicines=medicine
                    )

                success_count = len(valid_medicines)
                # prepare recent_bsr payload for template (use after commit)
                recent_bsr = {
                    'tracking_number': bsr.tracking_number,
                    'amount': str(bsr.amount) if bsr.amount is not None else '',
                    'date_claimed': bsr.date_claimed.strftime('%Y-%m-%d') if bsr.date_claimed else '',
                    'date_claim_expiry': bsr.date_claim_expiry.strftime('%Y-%m-%d') if bsr.date_claim_expiry else '',
                    'first_name': registration.first_name,
                    'last_name': registration.last_name,
                    'barangay_indigency': bool(bsr.barangay_indigency),
                    'barangay_recidency': bool(bsr.barangay_recidency),
                    'diagnosis': bsr.diagnosis or ''
                }
        except IntegrityError as ie:
            errors.append('Database error while saving assistance.')
            # fall through to show errors
        if success_count:
            messages.success(request, f'{success_count} assistance request(s) submitted and are pending approval.')
            # save the recent_bsr payload in session and redirect (PRG)
            # so refresh won't re-submit the POST. The GET will pop it
            # and the template will show the modal once.
            if recent_bsr:
                request.session['recent_bsr'] = recent_bsr
            return redirect('med_form')

        # show any errors encountered
        for e in errors:
            messages.error(request, e)

        # on error, re-render the form so messages are visible
        return render(request, 'center_staff/form.html', context)
    return render(request,'center_staff/form.html', context)


@require_GET
@csrf_exempt
def GET_REGISTRATION(request, rfid):
    try:
        reg = Registration.objects.select_related('province', 'municipality', 'barangay').get(rfid=rfid)
        data = {
            'rfid': reg.rfid,
            'last_name': reg.last_name,
            'first_name': reg.first_name,
            'middle_name': reg.middle_name,
            'name_extension': reg.name_extension,
            'date_of_birth': reg.date_of_birth.strftime('%Y-%m-%d') if reg.date_of_birth else '',
            'place_of_birth': reg.place_of_birth,
            'province_name': reg.province.province_name if reg.province else '',
            'municipality_name': reg.municipality.municipality_name if reg.municipality else '',
            'barangay_name': reg.barangay.barangay_name if reg.barangay else '',
            'mobile_no': reg.mobile_no,
            'gender': reg.gender,
            'civil_status': reg.civil_status,
            'occupation': reg.occupation,
            'email': reg.email,
            'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
        }
        # Get latest previous assistance for this registration
        prev = Bsrcenter.objects.filter(registration=reg).order_by('-id').first()
        if prev:
            # Get medicine names from the Bsrcenter_meds linking table
            meds_qs = Bsrcenter_meds.objects.filter(bsrcenter=prev).select_related('medicines')
            med_names = ', '.join([m.medicines.medicine_name for m in meds_qs]) if meds_qs.exists() else ''
            data['previous_assistance'] = {
                'amount': str(prev.amount) if prev.amount is not None else '',
                'medicine_name': med_names,
                'date_claimed': prev.date_claimed.strftime('%Y-%m-%d') if prev.date_claimed else '',
                'date_claim_expiry': prev.date_claim_expiry.strftime('%Y-%m-%d') if prev.date_claim_expiry else '',
            }
        else:
            data['previous_assistance'] = None
        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)