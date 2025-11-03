from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, bsrcenter
from django.views.decorators.csrf import csrf_exempt

def home(request):
    return render(request,'center_staff/home.html')

def MED_FORM(request):
    medicines = Medicines.objects.all()
    context = { 'medicines': medicines }
    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        age = request.POST.get('age')
        amount = request.POST.get('amount')
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
        today = date.today()

        success_count = 0
        errors = []

        for mid in medicines_ids:
            try:
                medicine = Medicines.objects.get(id=mid)
            except Medicines.DoesNotExist:
                errors.append(f'Medicine not found (id={mid}).')
                continue

            # Prevent duplicate assistance if not expired and approved
            existing = bsrcenter.objects.filter(
                registration=registration,
                medicines=medicine,
                status='approved',
                date_claim_expiry__gte=today
            ).first()
            if existing:
                errors.append(f'Cannot save assistance for "{medicine.medicine_name}": previous approved assistance is still active.')
                continue

            # Insert into bsrcenter for this medicine
            bsrcenter.objects.create(
                registration=registration,
                age=age or 0,
                amount=amount or 0,
                medicines=medicine,
                date_claimed=date_claimed,
                date_claim_expiry=date_claim_expiry,
                status='pending'
            )
            success_count += 1

        if success_count:
            # clearer message that the assistance entries are created and pending approval
            messages.success(request, f'{success_count} assistance request(s) submitted and are pending approval.')
        # show any errors encountered
        for e in errors:
            messages.error(request, e)

        # redirect back to form (messages persist) so user can see results
        return redirect('med_form')
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
        prev = bsrcenter.objects.filter(registration=reg).order_by('-id').first()
        if prev:
            data['previous_assistance'] = {
                'amount': prev.amount,
                'medicine_name': prev.medicines.medicine_name if prev.medicines else '',
                'date_claimed': prev.date_claimed.strftime('%Y-%m-%d') if prev.date_claimed else '',
                'date_claim_expiry': prev.date_claim_expiry.strftime('%Y-%m-%d') if prev.date_claim_expiry else '',
            }
        else:
            data['previous_assistance'] = None
        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)