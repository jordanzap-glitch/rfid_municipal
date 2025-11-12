from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Q
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap, Skills_training, Peso_tupad
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
        # optional date fields from the assistance form
        date_claimed = request.POST.get('date_claimed')
        date_claim_expiry = request.POST.get('date_claim_expiry')

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'peso_staff/reap_form.html')

        # Prevent creating another REAP when there is an active assistance:
        # - a REAP that is not yet released (is_released == False), OR
        # - a pending/approved REAP (status 1 or 2) whose expiry is null or not yet passed.
        today = date.today()
        active_reap_exists = Peso_reap.objects.filter(registration=registration).filter(
            Q(is_released=False) |
            (Q(status_id__in=[1, 2]) & (Q(date_claim_expiry__isnull=True) | Q(date_claim_expiry__gte=today)))
        ).exists()
        if active_reap_exists:
            messages.error(request, 'Cannot save REAP: there is an existing active REAP (pending/approved or not released).')
            return render(request, 'peso_staff/reap_form.html')

        # Create the Peso_reap record
        from django.db import transaction, IntegrityError
        reap = None
        try:
            with transaction.atomic():
                # generate a unique tracking number similar to MED_FORM
                import uuid

                def _gen_tracking():
                    return f"PESO-R-{uuid.uuid4().hex[:10].upper()}"

                tracking = _gen_tracking()
                # ensure uniqueness
                while Peso_reap.objects.filter(tracking_number=tracking).exists():
                    tracking = _gen_tracking()

                # parse provided dates (if any) to date objects
                date_claimed_obj = None
                if date_claimed:
                    try:
                        date_claimed_obj = _dt.strptime(date_claimed, '%Y-%m-%d').date()
                    except Exception:
                        date_claimed_obj = None

                date_claim_expiry_obj = None
                if date_claim_expiry:
                    try:
                        date_claim_expiry_obj = _dt.strptime(date_claim_expiry, '%Y-%m-%d').date()
                    except Exception:
                        date_claim_expiry_obj = None

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
                    date_claimed=date_claimed_obj if date_claimed_obj else None,
                    date_claim_expiry=date_claim_expiry_obj if date_claim_expiry_obj else None,
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
                    'date_claimed': reap.date_claimed.strftime('%Y-%m-%d') if getattr(reap, 'date_claimed', None) else '',
                    'date_claim_expiry': reap.date_claim_expiry.strftime('%Y-%m-%d') if getattr(reap, 'date_claim_expiry', None) else '',
            }
            return redirect('reap_form')

        return render(request, 'peso_staff/reap_form.html')

    # GET
    # Pop recent_reap to show once if template uses it
    recent_reap = None
    if request.method != 'POST':
        recent_reap = request.session.pop('recent_reap', None)
    return render(request,'peso_staff/reap_form.html', {'recent_reap': recent_reap})

def TUPAD_FORM(request):
    skills = Skills_training.objects.all()
    """Handle TUPAD form for PESO staff.

    GET: render the form (template currently reuses tupad_form.html).
    POST: validate RFID, check for active TUPAD, create a new Peso_tupad record.
    """
    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        beneficiaries = request.POST.get('beneficiaries', '')
        skill_training_val = request.POST.get('skill_training', '')
        date_claimed = request.POST.get('date_claimed')
        date_claim_expiry = request.POST.get('date_claim_expiry')

        # Normalize beneficiaries into a single string (one per line -> comma separated)
        # Trim whitespace and collapse empty lines
        names = [n.strip() for n in beneficiaries.splitlines() if n.strip()]
        name_of_beneficiary = ', '.join(names)[:255] if names else ''

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # Prevent creating another TUPAD when there is an active assistance:
        # - a TUPAD that is not yet released (is_released == False), OR
        # - a pending/approved TUPAD (status 1 or 2) whose expiry is null or not yet passed.
        today = date.today()
        active_exists = Peso_tupad.objects.filter(registration=registration).filter(
            Q(is_released=False) |
            (Q(status_id__in=[1, 2]) & (Q(date_claim_expiry__isnull=True) | Q(date_claim_expiry__gte=today)))
        ).exists()
        if active_exists:
            messages.error(request, 'Cannot save TUPAD: there is an existing active TUPAD (pending/approved or not released).')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # Validate required fields (date_claim_expiry and skill)
        if not date_claim_expiry:
            messages.error(request, 'Date claim expiry is required.')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # parse dates
        date_claimed_obj = None
        if date_claimed:
            try:
                date_claimed_obj = _dt.strptime(date_claimed, '%Y-%m-%d').date()
            except Exception:
                date_claimed_obj = None

        date_claim_expiry_obj = None
        if date_claim_expiry:
            try:
                date_claim_expiry_obj = _dt.strptime(date_claim_expiry, '%Y-%m-%d').date()
            except Exception:
                date_claim_expiry_obj = None

        # Simplified skills handling:
        # Prefer the form to submit the Skills_training.id. We accept an id string
        # and use it directly (if present). If the provided value isn't an int or
        # the id doesn't exist, fall back to get_or_create by name.
        skill_id = None
        skill_name = ''
        if skill_training_val:
            sval = skill_training_val.strip()
            try:
                sid = int(sval)
                # only use if the id exists
                if Skills_training.objects.filter(id=sid).exists():
                    skill_id = sid
                    # fetch the name for session display
                    skill_name = Skills_training.objects.filter(id=sid).values_list('Skills_name', flat=True).first() or ''
                else:
                    # fallback to treat the value as a name and create/lookup
                    skill_obj, _ = Skills_training.objects.get_or_create(Skills_name=sval)
                    skill_id = skill_obj.id
                    skill_name = skill_obj.Skills_name
            except (ValueError, TypeError):
                # not an integer -> treat as name
                skill_obj, _ = Skills_training.objects.get_or_create(Skills_name=sval)
                skill_id = skill_obj.id
                skill_name = skill_obj.Skills_name

        # Create Peso_tupad record
        tupad = None
        try:
            with transaction.atomic():
                import uuid

                def _gen_tracking():
                    return f"PESO-T-{uuid.uuid4().hex[:10].upper()}"

                tracking = _gen_tracking()
                while Peso_tupad.objects.filter(tracking_number=tracking).exists():
                    tracking = _gen_tracking()

                tupad = Peso_tupad.objects.create(
                    registration=registration,
                    tracking_number=tracking,
                    # date_claimed field has auto_now_add but we still allow overriding
                    date_claimed=date_claimed_obj if date_claimed_obj else None,
                    date_claim_expiry=date_claim_expiry_obj if date_claim_expiry_obj else None,
                    name_of_beneficiary=name_of_beneficiary,
                    # insert FK by id when available to avoid extra object assignment
                    skills_training_id=skill_id if skill_id else None,
                    processed_by_id=request.user.id if request.user and request.user.is_authenticated else None,
                )
        except IntegrityError:
            messages.error(request, 'Database error while saving TUPAD.')

        if tupad:
            messages.success(request, 'TUPAD saved successfully.')
            request.session['recent_tupad'] = {
                'id': tupad.id,
                'tracking_number': tupad.tracking_number,
                'first_name': registration.first_name,
                'last_name': registration.last_name,
                'name_of_beneficiary': tupad.name_of_beneficiary,
                # use resolved skill_name (falls back to empty string)
                'skills_training': skill_name,
                'date_claimed': tupad.date_claimed.strftime('%Y-%m-%d') if getattr(tupad, 'date_claimed', None) else '',
                'date_claim_expiry': tupad.date_claim_expiry.strftime('%Y-%m-%d') if getattr(tupad, 'date_claim_expiry', None) else '',
            }
            return redirect('tupad_form')

        return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

    # GET
    recent_tupad = None
    if request.method != 'POST':
        recent_tupad = request.session.pop('recent_tupad', None)
    return render(request, 'peso_staff/tupad_form.html', {'recent_tupad': recent_tupad, 'skills': skills})

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

        # Return all previous REAP records as a list
        prev_qs = Peso_reap.objects.filter(registration=reg).order_by('-id')
        prev_list = []
        for prev in prev_qs:
            prev_list.append({
                'tracking_number': prev.tracking_number if hasattr(prev, 'tracking_number') else '',
                'biodata': bool(prev.biodata),
                'certificate_of_reg': bool(prev.certificate_of_reg),
                'certificate_of_grades': bool(prev.certificate_of_grades),
                'official_receipt': bool(prev.official_receipt),
                'barangay_indigency': bool(prev.barangay_indigency),
                'barangay_recidency': bool(prev.barangay_recidency),
                'date_added': prev.date_added.strftime('%Y-%m-%d') if getattr(prev, 'date_added', None) else '',
                'date_claimed': prev.date_claimed.strftime('%Y-%m-%d') if getattr(prev, 'date_claimed', None) else '',
                'date_claim_expiry': prev.date_claim_expiry.strftime('%Y-%m-%d') if getattr(prev, 'date_claim_expiry', None) else '',
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
            })
        data['previous_reap_assistance'] = prev_list

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@require_GET
@csrf_exempt
def GET_REGISTRATION_TUPAD(request, rfid):
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

        prev_qs = Peso_tupad.objects.filter(registration=reg).order_by('-id')
        prev_list = []
        for prev in prev_qs:
            prev_list.append({
                'tracking_number': prev.tracking_number if hasattr(prev, 'tracking_number') else '',
                'name_of_beneficiary': prev.name_of_beneficiary or '',
                'skills_training': prev.skills_training.Skills_name if getattr(prev, 'skills_training', None) else '',
                'date_claimed': prev.date_claimed.strftime('%Y-%m-%d') if getattr(prev, 'date_claimed', None) else '',
                'date_claim_expiry': prev.date_claim_expiry.strftime('%Y-%m-%d') if getattr(prev, 'date_claim_expiry', None) else '',
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
            })
        data['previous_tupad_assistance'] = prev_list

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)

   