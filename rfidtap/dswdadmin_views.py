from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap, Skills_training, Peso_tupad, Academic_year, Reap_type, Civil_status, Occupation, Dswd_senior
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import date, datetime as _dt
from decimal import Decimal, InvalidOperation



def home(request):
    # Compute DSWD Senior dashboard metrics
    try:
        senior_total = Dswd_senior.objects.count()
        senior_pending = Dswd_senior.objects.filter(status_id=1).count()
        senior_approved = Dswd_senior.objects.filter(status_id=2).count()
        senior_rejected = Dswd_senior.objects.filter(status_id=3).count()
        senior_released_count = Dswd_senior.objects.filter(is_released=True).count()
    except Exception:
        senior_total = senior_pending = senior_approved = senior_rejected = 0
        senior_released_count = 0

    try:
        senior_released_pct = int(round((senior_released_count / senior_total) * 100)) if senior_total else 0
    except Exception:
        senior_released_pct = 0

    context = {
        'senior_total': senior_total,
        'senior_pending': senior_pending,
        'senior_approved': senior_approved,
        'senior_rejected': senior_rejected,
        'senior_released_count': senior_released_count,
        'senior_released_pct': senior_released_pct,
    }
    return render(request,'dswd_admin/home.html', context)

def APPROVAL_TABLE_SENIOR(request):
    """
    Show approval table for `Dswd_senior` rows.

    - POST supports `dswd_id` to approve/reject a single row, or falls back to one row by `registration_id`.
    - Renders `dswd_admin/approval_table_senior.html` with `dswd_data` list.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    if request.method == 'POST':
        dswd_id = request.POST.get('dswd_id') or request.POST.get('senior_id')
        registration_id = request.POST.get('registration_id') or request.POST.get('id')
        try:
            target_status = int(request.POST.get('target_status') or 2)
        except Exception:
            target_status = 2

        user_id = getattr(request.user, 'id', None)
        actioned_at = timezone.now()

        try:
            # If approving, ensure the senior assistance is marked completed
            if dswd_id:
                obj = Dswd_senior.objects.filter(id=dswd_id).first()
                if obj and target_status == 2:
                    if not getattr(obj, 'is_completed', False):
                        messages.error(request, 'Cannot approve: assistance is not marked completed.')
                        return redirect(request.path)
                Dswd_senior.objects.filter(id=dswd_id).update(
                    status_id=target_status,
                    actioned_by_id=user_id,
                    actioned_at=actioned_at,
                )
            elif registration_id:
                one = Dswd_senior.objects.filter(registration_id=registration_id).order_by('id').first()
                if one:
                    if target_status == 2 and not getattr(one, 'is_completed', False):
                        messages.error(request, 'Cannot approve: assistance is not marked completed.')
                        return redirect(request.path)
                    Dswd_senior.objects.filter(id=one.id).update(
                        status_id=target_status,
                        actioned_by_id=user_id,
                        actioned_at=actioned_at,
                    )
        except Exception:
            # ignore failures during bulk update; let the page reload
            pass
        return redirect(request.path)

    # Fetch Dswd_senior rows
    rows = (
        Dswd_senior.objects
        .select_related('registration', 'status', 'processed_by')
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
            'date_issued': str(getattr(r, 'date_issued', None)) if getattr(r, 'date_issued', None) else None,
            'date_issued_expiry': str(getattr(r, 'date_issued_expiry', None)) if getattr(r, 'date_issued_expiry', None) else None,
            'processed_by_id': getattr(r.processed_by, 'id', None) if getattr(r, 'processed_by', None) else None,
            'processed_by_name': (f"{r.processed_by.first_name} {r.processed_by.last_name}" if getattr(r, 'processed_by', None) else None),
            'status': st,
            'status_id': sid,
            'is_released': getattr(r, 'is_released', None),
            'is_completed': getattr(r, 'is_completed', None),
        })

    return render(request, 'dswd_admin/approval_senior_tbl.html', {'dswd_data': data})