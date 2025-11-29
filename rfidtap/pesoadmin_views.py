from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap, Skills_training, Peso_tupad, Academic_year, Reap_type, Civil_status, Occupation
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date, datetime as _dt
from decimal import Decimal, InvalidOperation


@login_required(login_url='/')
def home(request):
    # Allow filtering REAP metrics by Academic Year (via GET ?academic_year=<id>)
    academic_year_param = request.GET.get('academic_year') or None
    try:
        selected_academic_year_id = int(academic_year_param) if academic_year_param else None
    except Exception:
        selected_academic_year_id = None

    # Build a list of academic years for the dropdown (display only year + semester)
    academic_years = []
    try:
        for ay in Academic_year.objects.select_related('semester').order_by('-id').all():
            ay_val = getattr(ay, 'year', None)
            # Normalize year display: prefer numeric year part if stored as date/string like 'YYYY-..'
            if ay_val is None:
                year_str = ''
            else:
                try:
                    if hasattr(ay_val, 'year'):
                        year_str = str(ay_val.year)
                    else:
                        s = str(ay_val)
                        year_str = s.split('-')[0] if '-' in s else s
                except Exception:
                    year_str = str(ay_val)

            sem_name = getattr(ay.semester, 'sem_name', '') if getattr(ay, 'semester', None) else ''
            display = f"{year_str} - {sem_name}" if sem_name else year_str
            academic_years.append({'id': getattr(ay, 'id', None), 'display': display})
    except Exception:
        academic_years = []

    # Base queryset for REAP; apply academic year filter if provided
    base_reap_qs = Peso_reap.objects.all()
    if selected_academic_year_id:
        try:
            base_reap_qs = base_reap_qs.filter(Academic_year_id=selected_academic_year_id)
        except Exception:
            base_reap_qs = base_reap_qs

    # Dashboard counts for REAP
    try:
        reap_total = base_reap_qs.count()
        reap_pending = base_reap_qs.filter(status_id=1).count()
        reap_approved = base_reap_qs.filter(status_id=2).count()
        reap_rejected = base_reap_qs.filter(status_id=3).count()
        # Count of REAP records that have been released (is_released == True)
        reap_released_count = base_reap_qs.filter(is_released=True).count()
        # TUPAD dashboard counts (unchanged, not filtered by academic year)
        tupad_total = Peso_tupad.objects.count()
        tupad_pending = Peso_tupad.objects.filter(status_id=1).count()
        tupad_approved = Peso_tupad.objects.filter(status_id=2).count()
        tupad_rejected = Peso_tupad.objects.filter(status_id=3).count()
        tupad_released_count = Peso_tupad.objects.filter(is_released=True).count()
    except Exception:
        # fallback to zeros if the model/table is unavailable
        reap_total = reap_pending = reap_approved = reap_rejected = 0
        tupad_total = tupad_pending = tupad_approved = tupad_rejected = 0
        tupad_released_count = 0

    # calculate released percentage safely
    try:
        reap_released_pct = int(round((reap_released_count / reap_total) * 100)) if reap_total else 0
    except Exception:
        reap_released_pct = 0

    try:
        tupad_released_pct = int(round((tupad_released_count / tupad_total) * 100)) if tupad_total else 0
    except Exception:
        tupad_released_pct = 0

    context = {
        'reap_total': reap_total,
        'reap_pending': reap_pending,
        'reap_approved': reap_approved,
        'reap_rejected': reap_rejected,
        'reap_released_count': reap_released_count,
        'reap_released_pct': reap_released_pct,
        'tupad_total': tupad_total,
        'tupad_pending': tupad_pending,
        'tupad_approved': tupad_approved,
        'tupad_rejected': tupad_rejected,
        'tupad_released_count': tupad_released_count,
        'tupad_released_pct': tupad_released_pct,
        'academic_years': academic_years,
        'selected_academic_year_id': selected_academic_year_id,
    }
    return render(request,'peso_admin/home.html', context)


@login_required(login_url='/')
def APPROVAL_TABLE_REAP(request):
    """
    Show approval table for `Peso_reap` rows.

    - POST supports `pesoreap_id` (preferred) to approve/reject a single row, or falls back to one row by `registration_id`.
    - Renders `peso_admin/approval_reap_tbl.html` with `pesoreap_data` list.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    if request.method == 'POST':
        pesoreap_id = request.POST.get('pesoreap_id') or request.POST.get('bsrcenter_id')
        registration_id = request.POST.get('registration_id') or request.POST.get('id')
        try:
            target_status = int(request.POST.get('target_status') or 2)
        except Exception:
            target_status = 2

        # record who actioned and when
        user_id = getattr(request.user, 'id', None)
        actioned_at = timezone.now()

        try:
            if pesoreap_id:
                Peso_reap.objects.filter(id=pesoreap_id).update(
                    status_id=target_status,
                    actioned_by_id=user_id,
                    actioned_at=actioned_at,
                )
            elif registration_id:
                one = Peso_reap.objects.filter(registration_id=registration_id).order_by('id').first()
                if one:
                    Peso_reap.objects.filter(id=one.id).update(
                        status_id=target_status,
                        actioned_by_id=user_id,
                        actioned_at=actioned_at,
                    )
        except Exception:
            pass
        return redirect(request.path)

    # Fetch peso_reap rows
    rows = (
        Peso_reap.objects
        .select_related('registration', 'status', 'Academic_year__semester', 'reap_type', 'processed_by')
        .all()
        .order_by('id')
    )

    data = []
    for r in rows:
        reg = getattr(r, 'registration', None)
        try:
            sid = getattr(r.status, 'id', None) if getattr(r, 'status', None) else None
            st = STATUS_MAP.get(sid) or (r.status.status_name if getattr(r, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

        academic_year_id = getattr(r.Academic_year, 'id', None) if getattr(r, 'Academic_year', None) else None
        # Friendly academic year display (use the DateField as YYYY or full date string)
        academic_year = ''
        try:
            if getattr(r, 'Academic_year', None) and getattr(r.Academic_year, 'year', None):
                # show year part only if it's a date string like 'YYYY-01-01' else full
                ay_val = r.Academic_year.year
                academic_year = str(ay_val) if ay_val is not None else ''
        except Exception:
            academic_year = ''

        semester_name = ''
        try:
            if getattr(r, 'Academic_year', None) and getattr(r.Academic_year, 'semester', None):
                semester_name = getattr(r.Academic_year.semester, 'sem_name', '')
        except Exception:
            semester_name = ''

        data.append({
            'id': getattr(r, 'id', None),
            'tracking_number': getattr(r, 'tracking_number', None),
            'registration_id': getattr(r, 'registration_id', None),
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'academic_year_id': academic_year_id,
            'academic_year': academic_year,
            'semester_name': semester_name,
            'reap_type_id': getattr(r.reap_type, 'id', None) if getattr(r, 'reap_type', None) else None,
            'reap_type_name': getattr(r.reap_type, 'type_name', None) if getattr(r, 'reap_type', None) else None,
            'processed_by_id': getattr(r.processed_by, 'id', None) if getattr(r, 'processed_by', None) else None,
            'processed_by_name': (f"{r.processed_by.first_name} {r.processed_by.last_name}" if getattr(r, 'processed_by', None) else None),
            'status': st,
            'status_id': sid,
            'date_added': str(getattr(r, 'date_added', None)) if getattr(r, 'date_added', None) else None,
            'is_released': getattr(r, 'is_released', None),
        })

    return render(request, 'peso_admin/approval_reap_tbl.html', {'pesoreap_data': data})


@require_GET
@login_required(login_url='/')
def GET_PESO_REAP_INFO(request):
    """AJAX GET endpoint: return Peso_reap rows for a registration_id."""
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    if not registration_id:
        return JsonResponse({'error': 'Missing registration_id'}, status=400)

    entries = (
        Peso_reap.objects
        .select_related('registration', 'status', 'Academic_year__semester', 'reap_type', 'processed_by')
        .filter(registration_id=registration_id)
        .order_by('id')
    )

    if not entries.exists():
        return JsonResponse({'error': 'Not found'}, status=404)

    reg = entries[0].registration

    rows = []
    statuses = set()
    for e in entries:
        sid = getattr(e.status, 'id', None) if getattr(e, 'status', None) else None
        if sid == 2:
            statuses.add('approved')
        elif sid == 1:
            statuses.add('pending')
        elif sid == 3:
            statuses.add('rejected')
        else:
            if getattr(e, 'status', None):
                statuses.add(e.status.status_name)

        semester_name = ''
        try:
            if getattr(e, 'Academic_year', None) and getattr(e.Academic_year, 'semester', None):
                semester_name = getattr(e.Academic_year.semester, 'sem_name', '')
        except Exception:
            semester_name = ''

        rows.append({
            'id': getattr(e, 'id', None),
            'registration_id': getattr(e, 'registration_id', None),
            'tracking_number': getattr(e, 'tracking_number', None),
            'date_added': str(getattr(e, 'date_added', None)) if getattr(e, 'date_added', None) else None,
            'is_released': getattr(e, 'is_released', None),
            'academic_year_id': getattr(e.Academic_year, 'id', None) if getattr(e, 'Academic_year', None) else None,
            'semester_name': semester_name,
            'reap_type_id': getattr(e.reap_type, 'id', None) if getattr(e, 'reap_type', None) else None,
            'reap_type_name': getattr(e.reap_type, 'type_name', None) if getattr(e, 'reap_type', None) else None,
            'processed_by_id': getattr(e.processed_by, 'id', None) if getattr(e, 'processed_by', None) else None,
            'processed_by_name': (f"{e.processed_by.first_name} {e.processed_by.last_name}" if getattr(e, 'processed_by', None) else None),
            'status_id': sid,
            'status_name': getattr(e.status, 'status_name', None) if getattr(e, 'status', None) else None,
        })

    if 'approved' in statuses:
        agg_status = 'approved'
    elif 'pending' in statuses:
        agg_status = 'pending'
    elif 'rejected' in statuses:
        agg_status = 'rejected'
    else:
        agg_status = ','.join([s for s in statuses if s]) if statuses else ''

    data = {
        'registration_id': reg.id,
        'rfid': reg.rfid,
        'last_name': reg.last_name,
        'first_name': reg.first_name,
        'mobile_no': getattr(reg, 'mobile_no', None),
        'barangay': getattr(reg.barangay, 'barangay_name', '') if getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'reap_rows': rows,
        'status': agg_status,
    }
    return JsonResponse(data)


@login_required(login_url='/')
def APPROVAL_TABLE_TUPAD(request):
    """
    Show approval table for `Peso_tupad` rows.

    - POST supports `pesotupad_id` to approve/reject a single row, or falls back to one row by `registration_id`.
    - Renders `peso_admin/approval_tupad_tbl.html` with `pesotupad_data` list.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    if request.method == 'POST':
        pesotupad_id = request.POST.get('pesotupad_id') or request.POST.get('bsrcenter_id')
        registration_id = request.POST.get('registration_id') or request.POST.get('id')
        try:
            target_status = int(request.POST.get('target_status') or 2)
        except Exception:
            target_status = 2

        # record who actioned and when
        user_id = getattr(request.user, 'id', None)
        actioned_at = timezone.now()

        try:
            if pesotupad_id:
                Peso_tupad.objects.filter(id=pesotupad_id).update(
                    status_id=target_status,
                    actioned_by_id=user_id,
                    actioned_at=actioned_at,
                )
            elif registration_id:
                one = Peso_tupad.objects.filter(registration_id=registration_id).order_by('id').first()
                if one:
                    Peso_tupad.objects.filter(id=one.id).update(
                        status_id=target_status,
                        actioned_by_id=user_id,
                        actioned_at=actioned_at,
                    )
        except Exception:
            pass
        return redirect(request.path)

    # Fetch peso_tupad rows
    rows = (
        Peso_tupad.objects
        .select_related('registration', 'status', 'skills_training', 'processed_by')
        .all()
        .order_by('id')
    )

    data = []
    for r in rows:
        reg = getattr(r, 'registration', None)
        try:
            sid = getattr(r.status, 'id', None) if getattr(r, 'status', None) else None
            st = STATUS_MAP.get(sid) or (r.status.status_name if getattr(r, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

        data.append({
            'id': getattr(r, 'id', None),
            'tracking_number': getattr(r, 'tracking_number', None),
            'registration_id': getattr(r, 'registration_id', None),
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'name_of_beneficiary': getattr(r, 'name_of_beneficiary', None),
            'skills_training_id': getattr(r.skills_training, 'id', None) if getattr(r, 'skills_training', None) else None,
            'skills_training_name': getattr(r.skills_training, 'Skills_name', None) if getattr(r, 'skills_training', None) else None,
            'processed_by_id': getattr(r.processed_by, 'id', None) if getattr(r, 'processed_by', None) else None,
            'processed_by_name': (f"{r.processed_by.first_name} {r.processed_by.last_name}" if getattr(r, 'processed_by', None) else None),
            'status': st,
            'status_id': sid,
            'date_issued': str(getattr(r, 'date_issued', None)) if getattr(r, 'date_issued', None) else None,
            'date_issued_expiry': str(getattr(r, 'date_issued_expiry', None)) if getattr(r, 'date_issued_expiry', None) else None,
            'is_released': getattr(r, 'is_released', None),
        })

    return render(request, 'peso_admin/approval_tupad_tbl.html', {'pesotupad_data': data})


@require_GET
@login_required(login_url='/')
def GET_PESO_TUPAD_INFO(request):
    """AJAX GET endpoint: return Peso_tupad rows for a registration_id."""
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    if not registration_id:
        return JsonResponse({'error': 'Missing registration_id'}, status=400)

    entries = (
        Peso_tupad.objects
        .select_related('registration', 'status', 'skills_training', 'processed_by')
        .filter(registration_id=registration_id)
        .order_by('id')
    )

    if not entries.exists():
        return JsonResponse({'error': 'Not found'}, status=404)

    reg = entries[0].registration

    rows = []
    statuses = set()
    for e in entries:
        sid = getattr(e.status, 'id', None) if getattr(e, 'status', None) else None
        if sid == 2:
            statuses.add('approved')
        elif sid == 1:
            statuses.add('pending')
        elif sid == 3:
            statuses.add('rejected')
        else:
            if getattr(e, 'status', None):
                statuses.add(e.status.status_name)

        rows.append({
            'id': getattr(e, 'id', None),
            'registration_id': getattr(e, 'registration_id', None),
            'tracking_number': getattr(e, 'tracking_number', None),
            'name_of_beneficiary': getattr(e, 'name_of_beneficiary', None),
            'skills_training_id': getattr(e.skills_training, 'id', None) if getattr(e, 'skills_training', None) else None,
            'skills_training_name': getattr(e.skills_training, 'Skills_name', None) if getattr(e, 'skills_training', None) else None,
            'processed_by_id': getattr(e.processed_by, 'id', None) if getattr(e, 'processed_by', None) else None,
            'processed_by_name': (f"{e.processed_by.first_name} {e.processed_by.last_name}" if getattr(e, 'processed_by', None) else None),
            'date_issued': str(getattr(e, 'date_issued', None)) if getattr(e, 'date_issued', None) else None,
            'date_issued_expiry': str(getattr(e, 'date_issued_expiry', None)) if getattr(e, 'date_issued_expiry', None) else None,
            'is_released': getattr(e, 'is_released', None),
            'status_id': sid,
            'status_name': getattr(e.status, 'status_name', None) if getattr(e, 'status', None) else None,
        })

    if 'approved' in statuses:
        agg_status = 'approved'
    elif 'pending' in statuses:
        agg_status = 'pending'
    elif 'rejected' in statuses:
        agg_status = 'rejected'
    else:
        agg_status = ','.join([s for s in statuses if s]) if statuses else ''

    data = {
        'registration_id': reg.id,
        'rfid': reg.rfid,
        'last_name': reg.last_name,
        'first_name': reg.first_name,
        'mobile_no': getattr(reg, 'mobile_no', None),
        'barangay': getattr(reg.barangay, 'barangay_name', '') if getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'tupad_rows': rows,
        'status': agg_status,
    }
    return JsonResponse(data)