from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime as _dt
from decimal import Decimal, InvalidOperation


def home(request):
    return render(request,'peso_staff/home.html')

def REAP_FORM(request):
    """Handle REAP form for PESO staff.

    GET: render the form.
    POST: validate RFID, check for existing unreleased REAP and create a new Peso_reap record.
    """
    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        # document checkboxes
        biodata = bool(request.POST.get('biodata'))
        cert_registration = bool(request.POST.get('cert_registration'))
        cert_grades = bool(request.POST.get('cert_grades'))
        official_receipt = bool(request.POST.get('official_receipt'))
        barangay_indigency = bool(request.POST.get('barangay_indigency'))
        barangay_recidency = bool(request.POST.get('barangay_recidency'))

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'peso_staff/reap_form.html')

        # Prevent creating another REAP when there is an unreleased one
        if Peso_reap.objects.filter(registration=registration, is_released=False).exists():
            messages.error(request, 'Cannot save REAP: there is an existing unreleased REAP for this registration.')
            return render(request, 'peso_staff/reap_form.html')

        # Create the Peso_reap record
        from django.db import transaction, IntegrityError
        reap = None
        try:
            with transaction.atomic():
                # generate a unique tracking number similar to MED_FORM
                import uuid

                def _gen_tracking():
                    return f"Peso-R-{uuid.uuid4().hex[:10].upper()}"

                tracking = _gen_tracking()
                # ensure uniqueness
                while Peso_reap.objects.filter(tracking_number=tracking).exists():
                    tracking = _gen_tracking()

                reap = Peso_reap.objects.create(
                    registration=registration,
                    tracking_number=tracking,
                    biodata=biodata,
                    certificate_of_reg=cert_registration,
                    certificate_of_grades=cert_grades,
                    barangay_indigency=barangay_indigency,
                    barangay_recidency=barangay_recidency,
                    official_receipt=official_receipt,
                    processed_by_id=request.user.id if request.user and request.user.is_authenticated else None,
                )
        except IntegrityError:
            messages.error(request, 'Database error while saving REAP.')

        if reap:
            messages.success(request, 'REAP saved successfully.')
            # store brief payload in session for optional modal use
            request.session['recent_reap'] = {
                'id': reap.id,
                'tracking_number': reap.tracking_number,
                'first_name': registration.first_name,
                'last_name': registration.last_name,
                'biodata': reap.biodata,
                'certificate_of_reg': reap.certificate_of_reg,
                'certificate_of_grades': reap.certificate_of_grades,
                'official_receipt': reap.official_receipt,
                'barangay_indigency': reap.barangay_indigency,
                'barangay_recidency': reap.barangay_recidency,
            }
            return redirect('reap_form')

        return render(request, 'peso_staff/reap_form.html')

    # GET
    # Pop recent_reap to show once if template uses it
    recent_reap = None
    if request.method != 'POST':
        recent_reap = request.session.pop('recent_reap', None)
    return render(request,'peso_staff/reap_form.html', {'recent_reap': recent_reap})

@require_GET
@csrf_exempt
def GET_REGISTRATION_REAP(request, rfid):
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
            'zone_street': reg.zone_street or '',
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

        # Get latest REAP record for this registration
        prev = Peso_reap.objects.filter(registration=reg).order_by('-id').first()
        if prev:
            data['previous_reap_assistance'] = {
                'tracking_number': prev.tracking_number if hasattr(prev, 'tracking_number') else '',
                'biodata': bool(prev.biodata),
                'certificate_of_reg': bool(prev.certificate_of_reg),
                'certificate_of_grades': bool(prev.certificate_of_grades),
                'official_receipt': bool(prev.official_receipt),
                'barangay_indigency': bool(prev.barangay_indigency),
                'barangay_recidency': bool(prev.barangay_recidency),
                'date_added': prev.date_added.strftime('%Y-%m-%d') if getattr(prev, 'date_added', None) else '',
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
            }
        else:
            data['previous_reap_assistance'] = None

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

   