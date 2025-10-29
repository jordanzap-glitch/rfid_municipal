from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay


def home(request):
    return render(request,'center_admin/home.html')

def APPROVAL_TABLE(request):
    from app.models import bsrcenter, Registration
    bsrcenters = bsrcenter.objects.select_related('registration', 'medicines').all()
    data = []
    for b in bsrcenters:
        reg = b.registration
        data.append({
            'id': b.id,
            'rfid': reg.rfid,
            'last_name': reg.last_name,
            'first_name': reg.first_name,
            'middle_name': reg.middle_name,
            'name_extension': reg.name_extension,
            'date_of_birth': reg.date_of_birth,
            'mobile_no': reg.mobile_no,
            'gender': reg.gender,
            'civil_status': reg.civil_status,
            'occupation': reg.occupation,
            'email': reg.email,
            'province': reg.province.province_name if reg.province else '',
            'municipality': reg.municipality.municipality_name if reg.municipality else '',
            'barangay': reg.barangay.barangay_name if reg.barangay else '',
            'age': b.age,
            'amount': b.amount,
            'medicine': b.medicines.medicine_name,
            'date_claimed': b.date_claimed,
            'date_claim_expiry': b.date_claim_expiry,
            'status': b.status,
        })
    context = {'bsrcenter_data': data}
    return render(request,'center_admin/approval_table.html', context)

# AJAX endpoint to get bsrcenter info by id for modal
@require_GET
def GET_BSR_CENTER_INFO(request):
    from app.models import bsrcenter, Registration
    bsrcenter_id = request.GET.get('id')
    if not bsrcenter_id:
        return JsonResponse({'error': 'Missing id'}, status=400)
    try:
        b = bsrcenter.objects.select_related('registration', 'medicines').get(id=bsrcenter_id)
        reg = b.registration
        data = {
            'id': b.id,
            'rfid': reg.rfid,
            'last_name': reg.last_name,
            'first_name': reg.first_name,
            'middle_name': reg.middle_name,
            'name_extension': reg.name_extension,
            'date_of_birth': str(reg.date_of_birth),
            'mobile_no': reg.mobile_no,
            'gender': reg.gender,
            'civil_status': reg.civil_status,
            'occupation': reg.occupation,
            'email': reg.email,
            'province': reg.province.province_name if reg.province else '',
            'municipality': reg.municipality.municipality_name if reg.municipality else '',
            'barangay': reg.barangay.barangay_name if reg.barangay else '',
            'age': b.age,
            'amount': b.amount,
            'medicine': b.medicines.medicine_name,
            'date_claimed': str(b.date_claimed),
            'date_claim_expiry': str(b.date_claim_expiry),
            'status': b.status,
        }
        return JsonResponse(data)
    except bsrcenter.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

