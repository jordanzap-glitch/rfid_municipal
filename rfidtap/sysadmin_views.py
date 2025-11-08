from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid


def home(request):
    return render(request,'sys_admin/home.html')



def REGISTRATION_MEMBER(request):
    provinces = Province.objects.all()
    municipality = Municipality.objects.all()
    barangay = Barangay.objects.all()
    
    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        last_name = request.POST.get('last_name')
        first_name = request.POST.get('first_name')
        middle_name = request.POST.get('middle_name')
        name_extension = request.POST.get('name_extension')
        date_of_birth = request.POST.get('date_of_birth')
        place_of_birth = request.POST.get('place_of_birth')
        provinces_id = request.POST.get('province')
        municipality_id = request.POST.get('municipality')
        barangay_id = request.POST.get('barangay')
        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            ext = profile_pic.name.split('.')[-1]
            unique_name = f"member_{uuid.uuid4().hex}.{ext}"
            pic_path = default_storage.save(f'profile_pic/{unique_name}', ContentFile(profile_pic.read()))
            profile_pic = pic_path
        mobile_no = request.POST.get('mobile_no')
        gender = request.POST.get('gender')
        civil_status = request.POST.get('civil_status')
        occupation = request.POST.get('occupation')
        email = request.POST.get('email')
        # new fields
        age = request.POST.get('age')
        zone_street = request.POST.get('zone_street')
        
        if RfidAuth.objects.filter(rfid=rfid, status='invalid', in_use=True).exists():
            messages.error(request, 'RFID is already in use or invalid.')
            return redirect('sysadmin_register')
        
        if not RfidAuth.objects.filter(rfid=rfid).exists():
            messages.error(request, 'RFID is not registered in the system.')
            return redirect('sysadmin_register')
        else:
            try:
                # Normalize age to integer
                try:
                    age_val = int(age) if age not in (None, '') else 0
                except (ValueError, TypeError):
                    age_val = 0

                registration = Registration(
                    rfid=rfid,
                    last_name=last_name,
                    first_name=first_name,
                    middle_name=middle_name,
                    name_extension=name_extension,
                    date_of_birth=date_of_birth,
                    province_id=provinces_id,
                    municipality_id=municipality_id,
                    barangay_id=barangay_id,
                    profile_pic=profile_pic,
                    mobile_no=mobile_no,
                    gender=gender,
                    civil_status=civil_status,
                    occupation=occupation,
                    email=email,
                    place_of_birth=place_of_birth,
                    age=age_val,
                    zone_street=zone_street
                )
                registration.save()
                # Update RfidAuth status and in_use
                RfidAuth.objects.filter(rfid=rfid).update(status='invalid', in_use=True)
                messages.success(request, 'Member registered successfully.')
                return redirect('sysadmin_register')
            except IntegrityError:
                messages.error(request, 'Registration failed. Please try again.')
                return redirect('sysadmin_register')
    context = {
        'provinces': provinces,
        'municipality': municipality,
        'barangays': barangay,
    }
    return render(request, 'sys_admin/registration.html', context)



def get_municipalities(request):
    province_id = request.GET.get('province_id')
    municipalities = Municipality.objects.filter(province_id=province_id).values('id', 'municipality_name')
    return JsonResponse(list(municipalities), safe=False)

def get_barangays(request):
    municipality_id = request.GET.get('municipality_id')
    barangays = Barangay.objects.filter(municipality_id=municipality_id).values('id', 'barangay_name')
    return JsonResponse(list(barangays), safe=False)