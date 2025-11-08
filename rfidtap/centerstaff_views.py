from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Q
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime as _dt
from decimal import Decimal, InvalidOperation

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
            return render(request, 'center_staff/med_form.html', context)

        if not medicines_ids:
            messages.error(request, 'No medicine selected.')
            return render(request, 'center_staff/med_form.html', context)

        today = date.today()

        # Prevent creating a new medicine assistance when there is an approved,
        # still-active assistance (date_claim_expiry >= today). Allow creation
        # if the previous assistance has expired or is not approved.
        # Block creation if there is any pending(1) or approved(2) assistance
        # that either has no expiry set or hasn't expired yet.
        active_bsr_exists = Bsrcenter.objects.filter(
            registration=registration,
            status_id__in=[1, 2],
        ).filter(Q(date_claim_expiry__isnull=True) | Q(date_claim_expiry__gte=today)).exists()
        if active_bsr_exists:
            messages.error(request, 'Cannot save assistance: there is an approved assistance that has not yet expired.')
            return render(request, 'center_staff/med_form.html', context)

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
            # Prevent duplicate assistance for the same medicine when there is any
            # pending(1) or approved(2) bsrcenter for this registration that
            # either has no expiry set or hasn't expired yet.
            existing = Bsrcenter_meds.objects.filter(
                medicines=medicine,
                bsrcenter__registration=registration,
                bsrcenter__status_id__in=[1, 2],
            ).filter(Q(bsrcenter__date_claim_expiry__isnull=True) | Q(bsrcenter__date_claim_expiry__gte=today)).exists()
            if existing:
                errors.append(f'Cannot save assistance for "{medicine.medicine_name}": previous approved assistance is still active.')
                continue

            valid_medicines.append(medicine)

        if not valid_medicines:
            messages.error(request, 'No valid medicines to save.')
            for e in errors:
                messages.error(request, e)
            return render(request, 'center_staff/med_form.html', context)

        # Create a single Bsrcenter record and link all valid medicines to it
        bsr = None
        recent_bsr = None
        try:
            with transaction.atomic():
                # generate a unique tracking number like CC(XXXXXXXX)
                import uuid

                def _gen_tracking():
                    return f"CC-M-{uuid.uuid4().hex[:10].upper()}" #remember to change CC to other letters if needed

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
                    status_id=1,
                    processed_by_id=request.user.id if request.user and request.user.is_authenticated else None,
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
                    # include the present medicines saved for this BSR (names)
                    'medicines': [m.medicine_name for m in valid_medicines],
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
        return render(request, 'center_staff/med_form.html', context)
    return render(request,'center_staff/med_form.html', context)


def BURIAL_FORM(request):
    # Provide medicines list for template JS (safe placeholder)
    medicines = Medicines.objects.all()
    context = {'medicines': medicines}

    # PRG: pop recent_bsr from session on GET so template can show modal once
    if request.method != 'POST':
        recent_bsr = request.session.pop('recent_bsr', None)
        if recent_bsr:
            context['recent_bsr'] = recent_bsr

    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        deceased_name = request.POST.get('deceased_name')
        relationship = request.POST.get('relationship')
        cause_of_death = request.POST.get('cause_of_death')
        death_certificate = bool(request.POST.get('death_certificate'))
        amount = request.POST.get('amount')
        date_claimed = request.POST.get('date_claimed')
        # accept either name coming from template: date_claim_expiry or date_claimed_expiry
        date_claim_expiry = request.POST.get('date_claim_expiry') or request.POST.get('date_claimed_expiry')

        # Look up registration by RFID
        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'center_staff/burial_form.html', context)


        today = date.today()

        # Prevent creating a new burial assistance when there is an approved,
        # still-active burial (date_claim_expiry >= today). Allow creation
        # if the previous burial has expired or is not approved.
        # Block creation if there is any pending(1) or approved(2) burial
        # that either has no expiry set or hasn't expired yet.
        active_exists = Bsrcenter_Burial.objects.filter(
            registration=registration,
            status_id__in=[1, 2],
        ).filter(Q(date_claim_expiry__isnull=True) | Q(date_claim_expiry__gte=today)).exists()
        if active_exists:
            messages.error(request, 'Cannot save burial assistance: there is an approved burial assistance that has not yet expired.')
            return render(request, 'center_staff/burial_form.html', context)

        # normalize amount
        try:
            amount_val = Decimal(amount) if amount not in (None, '') else Decimal('0.00')
        except (InvalidOperation, TypeError):
            amount_val = Decimal('0.00')

        # Convert date_claim_expiry to date object if provided
        expiry_date_obj = None
        if date_claim_expiry:
            try:
                expiry_date_obj = _dt.strptime(date_claim_expiry, '%Y-%m-%d').date()
            except Exception:
                expiry_date_obj = None

        # Create burial record
        burial = None
        recent_bsr = None
        try:
            with transaction.atomic():
                import uuid

                def _gen_tracking():
                    return f"CC-B-{uuid.uuid4().hex[:10].upper()}"

                tracking = _gen_tracking()
                while Bsrcenter_Burial.objects.filter(tracking_number=tracking).exists():
                    tracking = _gen_tracking()

                burial = Bsrcenter_Burial.objects.create(
                    registration=registration,
                    deceased_name=deceased_name or '',
                    relationship=relationship or '',
                    tracking_number=tracking,
                    date_claim_expiry=expiry_date_obj or date_claim_expiry,
                    status_id=1,
                    processed_by_id=request.user.id if request.user and request.user.is_authenticated else None,
                    death_certificate=death_certificate,
                    cause_of_death=cause_of_death or '',
                    amount=amount_val,
                )

                # prepare recent_bsr payload for template
                recent_bsr = {
                    'tracking_number': burial.tracking_number,
                    'amount': str(burial.amount) if burial.amount is not None else '',
                    'date_claimed': burial.date_claimed.strftime('%Y-%m-%d') if burial.date_claimed else '',
                    'date_claim_expiry': burial.date_claim_expiry.strftime('%Y-%m-%d') if burial.date_claim_expiry else '',
                    'deceased_name': burial.deceased_name,
                    'relationship': burial.relationship,
                    'cause_of_death': burial.cause_of_death or '',
                    'death_certificate': bool(burial.death_certificate),
                    # include registration name to show in the modal when helpful
                    'first_name': registration.first_name if registration else '',
                    'last_name': registration.last_name if registration else '',
                }
        except IntegrityError:
            messages.error(request, 'Database error while saving burial assistance.')

        if burial:
            messages.success(request, 'Burial assistance submitted and is pending approval.')
            if recent_bsr:
                request.session['recent_bsr'] = recent_bsr
            return redirect('burial_form')

        return render(request, 'center_staff/burial_form.html', context)

    return render(request,'center_staff/burial_form.html', context)



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
            'age': reg.age,
            'province_name': reg.province.province_name if reg.province else '',
            'municipality_name': reg.municipality.municipality_name if reg.municipality else '',
            'barangay_name': reg.barangay.barangay_name if reg.barangay else '',
            'mobile_no': reg.mobile_no,
            'gender': reg.gender,
            'civil_status': reg.civil_status,
            'occupation': reg.occupation,
            'email': reg.email,
            'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
            'zone_street': reg.zone_street or '',
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


@require_GET
@csrf_exempt
def GET_REGISTRATION_BURIALS(request, rfid):
    """Return registration info plus latest burial assistance (if any).

    JSON keys:
      - registration fields (rfid, names, etc.)
      - previous_burial_assistance: { deceased_name, cause_of_death, relationship, amount, date_claimed, date_claim_expiry }
    """
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
            'age': reg.age,
            'province_name': reg.province.province_name if reg.province else '',
            'municipality_name': reg.municipality.municipality_name if reg.municipality else '',
            'barangay_name': reg.barangay.barangay_name if reg.barangay else '',
            'mobile_no': reg.mobile_no,
            'gender': reg.gender,
            'civil_status': reg.civil_status,
            'occupation': reg.occupation,
            'email': reg.email,
            'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
            'zone_street': reg.zone_street or '',
        }

        prev = Bsrcenter_Burial.objects.filter(registration=reg).order_by('-id').first()
        if prev:
            data['previous_burial_assistance'] = {
                'deceased_name': prev.deceased_name,
                'cause_of_death': prev.cause_of_death or '',
                'relationship': prev.relationship or '',
                'amount': str(prev.amount) if prev.amount is not None else '',
                'date_claimed': prev.date_claimed.strftime('%Y-%m-%d') if prev.date_claimed else '',
                'date_claim_expiry': prev.date_claim_expiry.strftime('%Y-%m-%d') if prev.date_claim_expiry else '',
            }
        else:
            data['previous_burial_assistance'] = None

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)
    
