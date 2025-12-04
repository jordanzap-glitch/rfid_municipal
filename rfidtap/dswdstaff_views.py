from django.views.decorators.http import require_GET, require_POST
import json
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Q
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap, Skills_training, Academic_year, Reap_type, Civil_status, Occupation, Dswd_senior
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date, datetime as _dt
from decimal import Decimal, InvalidOperation
import uuid


def home(request):
    return render(request,'dswd_staff/home.html')


@login_required(login_url='/')
def SENIOR_FORM(request):
    recent_dswd = None
    if request.method == 'POST':
        # accept hidden field names for DSWD follow-up
        existing_id = request.POST.get('dswd_id') or request.POST.get('existing_dswd_id')
        rfid = request.POST.get('rfid')
        barangay_indigency = bool(request.POST.get('barangay_indigency'))
        date_issued = request.POST.get('date_issued')
        date_issued_expiry = request.POST.get('date_issued_expiry')

        # basic validation
        if not rfid:
            messages.error(request, 'Please provide RFID.')
            return redirect('senior_form')

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for the provided RFID.')
            return redirect('senior_form')

        # Prevent creating another active DSWD senior assistance
        today = date.today()
        active_exists = Dswd_senior.objects.filter(registration=registration).filter(
            Q(is_released=False) |
            (Q(status_id__in=[1, 2]) & (Q(date_issued_expiry__isnull=True) | Q(date_issued_expiry__gte=today)))
        ).exists()
        if active_exists and not existing_id:
            messages.error(request, 'There is already an active DSWD senior assistance for this registration.')
            return redirect('senior_form')

        if not date_issued_expiry:
            messages.error(request, 'Please provide the expiry date for the assistance.')
            return redirect('senior_form')

        try:
            # create or update
            # parse dates into date objects if provided
            date_issued_obj = None
            if date_issued:
                try:
                    date_issued_obj = _dt.strptime(date_issued, '%Y-%m-%d').date()
                except Exception:
                    date_issued_obj = None

            date_issued_expiry_obj = None
            if date_issued_expiry:
                try:
                    date_issued_expiry_obj = _dt.strptime(date_issued_expiry, '%Y-%m-%d').date()
                except Exception:
                    date_issued_expiry_obj = None

            if existing_id:
                try:
                    ds = Dswd_senior.objects.get(pk=int(existing_id))
                except Exception:
                    ds = None
            else:
                ds = None

            if ds:
                ds.barangay_indigency = barangay_indigency
                ds.date_issued = date_issued_obj if date_issued_obj else ds.date_issued
                ds.date_issued_expiry = date_issued_expiry_obj if date_issued_expiry_obj else ds.date_issued_expiry
                # mark as completed when required fields present (similar to REAP logic)
                try:
                    ds.is_completed = bool(barangay_indigency and (ds.date_issued) and (ds.date_issued_expiry))
                except Exception:
                    ds.is_completed = False
                ds.processed_by = request.user if request.user.is_authenticated else None
                ds.save()
            else:
                # Create with a generated tracking number (retry on collision)
                MAX_ATTEMPTS = 5
                created = None
                try:
                    for attempt in range(MAX_ATTEMPTS):
                        try:
                            with transaction.atomic():
                                def _gen_tracking():
                                    return f"DSWD-S-{uuid.uuid4().hex[:10].upper()}"

                                tracking = _gen_tracking()
                                # determine completion state similar to REAP: require barangay_indigency and both dates
                                is_completed_flag = bool(barangay_indigency and date_issued_obj and date_issued_expiry_obj)
                                created = Dswd_senior.objects.create(
                                    registration=registration,
                                    tracking_number=tracking,
                                    barangay_indigency=barangay_indigency,
                                    date_issued=date_issued_obj if date_issued_obj else None,
                                    date_issued_expiry=date_issued_expiry_obj if date_issued_expiry_obj else None,
                                    processed_by=(request.user if request.user.is_authenticated else None),
                                    is_completed=is_completed_flag,
                                )
                            break
                        except IntegrityError:
                            created = None
                            if attempt == MAX_ATTEMPTS - 1:
                                raise
                except IntegrityError:
                    messages.error(request, 'Database error while saving DSWD assistance. Please try again.')
                    return redirect('senior_form')

                ds = created

            # store for modal/confirmation
            request.session['recent_dswd'] = ds.id
            messages.success(request, 'DSWD senior assistance saved successfully.')
            return redirect('senior_form')
        except IntegrityError:
            messages.error(request, 'Failed to save assistance. Please try again.')
            return redirect('senior_form')

    # GET
    if request.method != 'POST':
        recent_dswd = None
        rid = request.session.pop('recent_dswd', None)
        if rid:
            try:
                recent_dswd = Dswd_senior.objects.get(pk=rid)
            except Exception:
                recent_dswd = None

    return render(request, 'dswd_staff/senior_form.html', {'recent_dswd': recent_dswd})


@require_GET
@csrf_exempt
@login_required(login_url='/')
def GET_REGISTRATION_SENIOR(request, rfid):
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
            'civil_status': reg.civil_status_id,
            'civil_status_name': reg.civil_status.civil_status_name if reg.civil_status else '',
            'occupation': reg.occupation_id,
            'occupation_name': reg.occupation.occupation_name if reg.occupation else '',
            'email': reg.email,
            'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
            'ncsc_rrn': reg.ncsc_rrn or '',
            'osca_no': reg.osca_no or '',
        }

        prev_qs = Dswd_senior.objects.filter(registration=reg).order_by('-id')
        prev_list = []
        for prev in prev_qs:
            prev_list.append({
                'id': prev.id,
                'tracking_number': prev.tracking_number or '',
                'barangay_indigency': bool(prev.barangay_indigency),
                'date_issued': prev.date_issued.strftime('%Y-%m-%d') if getattr(prev, 'date_issued', None) else '',
                'date_issued_expiry': prev.date_issued_expiry.strftime('%Y-%m-%d') if getattr(prev, 'date_issued_expiry', None) else '',
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
                'is_completed': bool(getattr(prev, 'is_completed', False)),
                'is_complete': bool(getattr(prev, 'is_completed', False)),
                'released_by_id': prev.released_by.id if getattr(prev, 'released_by', None) else None,
                'released_by_first_name': prev.released_by.first_name if getattr(prev, 'released_by', None) else '',
                'released_by_last_name': prev.released_by.last_name if getattr(prev, 'released_by', None) else '',
                'released_by_name': (f"{prev.released_by.first_name} {prev.released_by.last_name}".strip()) if getattr(prev, 'released_by', None) else '',
                'released_at': prev.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(prev, 'released_at', None) else '',
            })
        data['previous_dswd_assistance'] = prev_list

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@login_required(login_url='/')
def SENIOR_RELEASE(request):
    return render(request, 'dswd_staff/senior_release.html')


@require_POST
@login_required(login_url='/')
def RELEASE_SENIOR(request):
    """Handle DSWD senior release POST: expects JSON {tracking: <tracking_number>} or {id: <dswd_id>}.

    Marks Dswd_senior.is_released = True for the matching record.
    Returns JSON success or error status.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    tracking = payload.get('tracking')
    dswd_id = payload.get('id')

    if not tracking and not dswd_id:
        return JsonResponse({'error': 'missing_identifier'}, status=400)

    # Authorization: ensure the current user is allowed to release assistance
    try:
        can_release_flag = bool(getattr(request.user.customuser, 'can_release', False))
    except Exception:
        can_release_flag = False
    if not can_release_flag:
        return JsonResponse({'error': 'permission_denied', 'message': 'User not authorized to release.'}, status=403)

    ds = None
    try:
        if dswd_id:
            ds = Dswd_senior.objects.get(pk=dswd_id)
        elif tracking:
            ds = Dswd_senior.objects.get(tracking_number=tracking)
    except Dswd_senior.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    if getattr(ds, 'is_released', False):
        return JsonResponse({'error': 'already_released'}, status=400)

    # Do not allow releasing when the record is Pending (1) or Rejected (3)
    try:
        status_id = getattr(ds, 'status_id', None)
    except Exception:
        status_id = None
    if status_id in (1, 3):
        status_label = 'Pending' if status_id == 1 else ('Rejected' if status_id == 3 else 'Unknown')
        return JsonResponse({
            'error': 'cannot_release_status',
            'message': f'Record cannot be released because status is {status_label}.',
            'status_id': status_id,
        }, status=400)

    ds.is_released = True
    try:
        if request.user and request.user.is_authenticated:
            ds.released_by_id = request.user.id
        ds.released_at = timezone.now()
    except Exception:
        pass
    ds.save()

    released_by_id = ds.released_by.id if getattr(ds, 'released_by', None) else None
    released_by_first_name = ds.released_by.first_name if getattr(ds, 'released_by', None) else ''
    released_by_last_name = ds.released_by.last_name if getattr(ds, 'released_by', None) else ''
    released_by_name = (f"{released_by_first_name} {released_by_last_name}".strip()) if (released_by_first_name or released_by_last_name) else ''
    released_at = ds.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(ds, 'released_at', None) else ''

    return JsonResponse({
        'success': True,
        'released_by_id': released_by_id,
        'released_by_first_name': released_by_first_name,
        'released_by_last_name': released_by_last_name,
        'released_by_name': released_by_name,
        'released_at': released_at,
    })
