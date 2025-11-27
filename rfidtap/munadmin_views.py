from django.views.decorators.http import require_GET
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Count
from django.db.models.functions import ExtractYear
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Bsrcenter, Bsrcenter_Burial, Peso_reap, Peso_tupad, Occupation, Academic_year, Semester, Medicines, Bsrcenter_meds
import csv
from django.utils.encoding import smart_str


def home(request):
    # show total registrations as total population
    registration_count = Registration.objects.count()
    # count registrations whose end_user_type_id == 1 (Senior Citizen)
    senior_count = Registration.objects.filter(end_user_type_id=1).count()
    # count registrations whose end_user_type_id == 2 (Students)
    student_count = Registration.objects.filter(end_user_type_id=2).count()
    # occupation-based counts (match by occupation name, case-insensitive)
    farmers_count = Registration.objects.filter(occupation__occupation_name__iexact='Farmer').count()
    construction_count = Registration.objects.filter(occupation__occupation_name__iexact='Construction Worker').count()
    plumber_count = Registration.objects.filter(occupation__occupation_name__iexact='Plumber').count()
    unemployed_count = Registration.objects.filter(occupation__occupation_name__iexact='Unemployed').count()
    # aggregated occupation counts: occupation name + registration count
    try:
        occ_qs = (
            Registration.objects
            .values('occupation__occupation_name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        occupation_counts = []
        for o in occ_qs:
            name = o.get('occupation__occupation_name') or 'Unspecified'
            occupation_counts.append({'name': name, 'count': o.get('count', 0)})
    except Exception:
        occupation_counts = []
    # analytics: compute department assistance totals for Center and PESO
    try:
        center_count = Bsrcenter.objects.count() + Bsrcenter_Burial.objects.count()
    except Exception:
        center_count = 0
    try:
        peso_count = Peso_reap.objects.count() + Peso_tupad.objects.count()
    except Exception:
        peso_count = 0
    # percentages for simple comparison (integers, sum may be 100 or off-by-1 due to rounding)
    try:
        total_departments = center_count + peso_count
        if total_departments:
            center_pct = int(round((center_count / total_departments) * 100))
            peso_pct = 100 - center_pct
        else:
            center_pct = 0
            peso_pct = 0
    except Exception:
        center_pct = 0
        peso_pct = 0
    # Assistance breakdown counts
    brscenter_medicals_count = Bsrcenter.objects.count()
    bsrcenter_burials_count = Bsrcenter_Burial.objects.count()
    peso_reap_count = Peso_reap.objects.count()
    peso_tupad_count = Peso_tupad.objects.count()

    context = { 'registration_count': registration_count, 'senior_count': senior_count, 'student_count': student_count }
    # add occupation counts to context
    context.update({
        'farmers_count': farmers_count,
        'construction_count': construction_count,
        'plumber_count': plumber_count,
        'unemployed_count': unemployed_count,
        'occupation_counts': occupation_counts,
        'center_count': center_count,
        'peso_count': peso_count,
        'center_pct': center_pct,
        'peso_pct': peso_pct,
        # assistance breakdown for template
        'brscenter_medicals_count': brscenter_medicals_count,
        'bsrcenter_burials_count': bsrcenter_burials_count,
        'peso_reap_count': peso_reap_count,
        'peso_tupad_count': peso_tupad_count,
    })
    return render(request, 'mun_admin/home.html', context)

def analytics_home(request):
    # Compute REAP release progress metrics for analytics card
    # Support optional filtering by Academic Year via GET param `academic_year`
    # include related Semester name so dropdown can show year + semester
    academic_years = []
    try:
        import datetime
        for ay in Academic_year.objects.select_related('semester').order_by('-year'):
            raw_year = getattr(ay, 'year', None)
            # Normalize to a short year label (e.g. '2024')
            year_label = ''
            try:
                if isinstance(raw_year, (datetime.date, datetime.datetime)):
                    year_label = str(raw_year.year)
                elif isinstance(raw_year, int):
                    year_label = str(raw_year)
                elif isinstance(raw_year, str):
                    # If stored as 'YYYY-MM-DD' or similar, take the first 4 chars or segment
                    if len(raw_year) >= 4 and raw_year[:4].isdigit():
                        year_label = raw_year[:4]
                    else:
                        year_label = raw_year
                else:
                    year_label = str(raw_year) if raw_year is not None else ''
            except Exception:
                year_label = str(raw_year) if raw_year is not None else ''

            academic_years.append({
                'id': getattr(ay, 'id', None),
                'year': year_label,
                'sem_name': getattr(getattr(ay, 'semester', None), 'sem_name', '')
            })
    except Exception:
        academic_years = []
    selected_academic_year = request.GET.get('academic_year')
    try:
        selected_academic_year_id = int(selected_academic_year) if selected_academic_year else None
    except Exception:
        selected_academic_year_id = None

    try:
        reap_qs = Peso_reap.objects.all()
        if selected_academic_year_id:
            reap_qs = reap_qs.filter(Academic_year_id=selected_academic_year_id)
        reap_total = reap_qs.count()
        reap_released = reap_qs.filter(is_released=True).count()
    except Exception:
        reap_total = 0
        reap_released = 0

    try:
        reap_released_pct = int(round((reap_released / reap_total) * 100)) if reap_total else 0
    except Exception:
        reap_released_pct = 0

    # single parent count: registration.civil_status_id == 3
    try:
        single_parent_count = Registration.objects.filter(civil_status_id=3).count()
    except Exception:
        single_parent_count = 0

    context = {
        'reap_total': reap_total,
        'reap_released': reap_released,
        'reap_released_pct': reap_released_pct,
        'academic_years': academic_years,
        'selected_academic_year_id': selected_academic_year_id,
    }

    # Build trend data: counts of Peso_reap per Academic_year (labelled by year + semester)
    try:
        # Map Academic_year_id -> count across all Peso_reap (or filtered set?)
        counts_qs = Peso_reap.objects.values('Academic_year_id').annotate(count=Count('id'))
        counts_map = {c['Academic_year_id']: c['count'] for c in counts_qs}
        reap_trend_labels = []
        reap_trend_data = []
        # Use the academic_years list (already ordered) to build labels in the same order
        for ay in academic_years:
            ay_id = ay.get('id')
            label = ay.get('year') or ''
            sem = ay.get('sem_name')
            if sem:
                label = f"{label} - {sem}"
            reap_trend_labels.append(label)
            reap_trend_data.append(counts_map.get(ay_id, 0))
    except Exception:
        reap_trend_labels = []
        reap_trend_data = []

    # add trend arrays to context
    context.update({
        'reap_trend_labels': reap_trend_labels,
        'reap_trend_data': reap_trend_data,
    })

    # Build top-barangay counts: count unique registrations per barangay
    try:
        # collect registration IDs referenced by any assistance model
        reg_ids = set()
        reg_ids.update(list(Bsrcenter.objects.values_list('registration_id', flat=True).exclude(registration_id__isnull=True)))
        reg_ids.update(list(Bsrcenter_Burial.objects.values_list('registration_id', flat=True).exclude(registration_id__isnull=True)))
        reg_ids.update(list(Peso_reap.objects.values_list('registration_id', flat=True).exclude(registration_id__isnull=True)))
        reg_ids.update(list(Peso_tupad.objects.values_list('registration_id', flat=True).exclude(registration_id__isnull=True)))

        barangay_labels = []
        barangay_data = []
        if reg_ids:
            # count unique registrations grouped by registration.barangay_id
            counts = (
                Registration.objects
                .filter(id__in=reg_ids)
                .values('barangay_id')
                .annotate(count=Count('id'))
                .order_by('-count')
            )
            ids = [c['barangay_id'] for c in counts if c.get('barangay_id')]
            name_map = {b['id']: b['barangay_name'] for b in Barangay.objects.filter(id__in=ids).values('id', 'barangay_name')}
            for c in counts[:10]:
                bid = c.get('barangay_id')
                if not bid:
                    continue
                barangay_labels.append(name_map.get(bid, 'Unknown'))
                barangay_data.append(c.get('count', 0))
    except Exception:
        barangay_labels = []
        barangay_data = []

    context.update({
        'barangay_labels': barangay_labels,
        'barangay_data': barangay_data,
    })

    # include single_parent_count in context
    try:
        context.update({'single_parent_count': single_parent_count})
    except Exception:
        context.update({'single_parent_count': 0})

    # Compute TUPAD release progress metrics for analytics card
    try:
        tupad_total = Peso_tupad.objects.count()
        tupad_released = Peso_tupad.objects.filter(is_released=True).count()
    except Exception:
        tupad_total = 0
        tupad_released = 0

    try:
        tupad_released_pct = int(round((tupad_released / tupad_total) * 100)) if tupad_total else 0
    except Exception:
        tupad_released_pct = 0

    # add TUPAD values to context
    context.update({
        'tupad_total': tupad_total,
        'tupad_released': tupad_released,
        'tupad_released_pct': tupad_released_pct,
    })

    # Build yearly trend for TUPAD based on date_issued year
    try:
        tupad_counts_qs = (
            Peso_tupad.objects
            .exclude(date_issued__isnull=True)
            .annotate(year=ExtractYear('date_issued'))
            .values('year')
            .annotate(count=Count('id'))
            .order_by('year')
        )
        tupad_trend_labels = []
        tupad_trend_data = []
        for r in tupad_counts_qs:
            year = r.get('year')
            tupad_trend_labels.append(str(year) if year is not None else '')
            tupad_trend_data.append(r.get('count', 0))
    except Exception:
        tupad_trend_labels = []
        tupad_trend_data = []

    context.update({
        'tupad_trend_labels': tupad_trend_labels,
        'tupad_trend_data': tupad_trend_data,
    })

    return render(request, 'mun_admin/analytics_home.html', context)


@login_required
def MEDICAL_TABLE(request):
    """Render the medicals table for municipal admin.

    Builds `bsrcenter_data` (same shape as center admin) but read-only.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    # Fetch Bsrcenter rows with related registration/status and prefetch medicines
    Bsrcenters = (
        Bsrcenter.objects
        .select_related('registration', 'status')
        .prefetch_related('bsrcenter_meds_set__medicines')
        .all()
        .order_by('id')
    )

    data = []
    for b in Bsrcenters:
        reg = getattr(b, 'registration', None)

        try:
            sid = getattr(b.status, 'id', None) if getattr(b, 'status', None) else None
            st = STATUS_MAP.get(sid) or (b.status.status_name if getattr(b, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

        # processed_by name
        processed_by_name = ''
        if getattr(b, 'processed_by', None):
            pb = b.processed_by
            processed_by_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

        # gather medicines for this Bsrcenter row
        med_list = []
        med_names = []
        for bm in b.bsrcenter_meds_set.all():
            m = getattr(bm, 'medicines', None)
            med_entry = {
                'bsrcenter_meds_id': getattr(bm, 'id', None),
                'medicine_id': getattr(m, 'id', None) if m else None,
                'medicine_name': getattr(m, 'medicine_name', None) if m else None,
                'amount': getattr(bm, 'amount', None) or getattr(b, 'amount', None),
                'date_claimed': str(getattr(bm, 'date_claimed', None)) if getattr(bm, 'date_claimed', None) else (str(getattr(b, 'date_claimed', None)) if getattr(b, 'date_claimed', None) else None),
                'date_claim_expiry': str(getattr(bm, 'date_claim_expiry', None)) if getattr(bm, 'date_claim_expiry', None) else (str(getattr(b, 'date_claim_expiry', None)) if getattr(b, 'date_claim_expiry', None) else None),
            }
            med_list.append(med_entry)
            if med_entry.get('medicine_name'):
                med_names.append(med_entry.get('medicine_name'))

        medicine_names = ', '.join(med_names)

        data.append({
            'id': getattr(b, 'id', None),
            'tracking_number': getattr(b, 'tracking_number', None),
            'registration_id': getattr(b, 'registration_id', None),
            'rfid': getattr(reg, 'rfid', None) if reg else None,
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'middle_name': getattr(reg, 'middle_name', None) if reg else None,
            'name_extension': getattr(reg, 'name_extension', None) if reg else None,
            'date_of_birth': getattr(reg, 'date_of_birth', None) if reg else None,
            'mobile_no': getattr(reg, 'mobile_no', None) if reg else None,
            'gender': getattr(reg, 'gender', None) if reg else None,
            'civil_status': getattr(reg, 'civil_status', None) if reg else None,
            'occupation': getattr(reg, 'occupation', None) if reg else None,
            'email': getattr(reg, 'email', None) if reg else None,
            'province': getattr(reg.province, 'province_name', '') if reg and getattr(reg, 'province', None) else (reg.province if reg else ''),
            'municipality': getattr(reg.municipality, 'municipality_name', '') if reg and getattr(reg, 'municipality', None) else (reg.municipality if reg else ''),
            'barangay': getattr(reg.barangay, 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
            'age': getattr(b, 'age', None),
            'amount': getattr(b, 'amount', None),
            'medicine': medicine_names,
            'medicine_list': med_list,
            'date_claim_expiry': str(getattr(b, 'date_claim_expiry', None)) if getattr(b, 'date_claim_expiry', None) else None,
            'date_claim_expiry_list': [str(getattr(bm, 'date_claim_expiry', None)) for bm in b.bsrcenter_meds_set.all() if getattr(bm, 'date_claim_expiry', None)] or ([str(getattr(b, 'date_claim_expiry', None))] if getattr(b, 'date_claim_expiry', None) else []),
            'status': st,
            'status_id': sid,
            'processed_by': processed_by_name,
        })

    return render(request, 'mun_admin/medical_table.html', {'bsrcenter_data': data})
@login_required
def BURIAL_TABLE(request):
    """Render the burials table for municipal admin (read-only).

    Builds `bsrcenter_data` with burial rows similar to center admin.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    rows = (
        Bsrcenter_Burial.objects
        .select_related('registration', 'status')
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

        processed_by_name = ''
        if getattr(r, 'processed_by', None):
            pb = r.processed_by
            processed_by_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

        data.append({
            'id': getattr(r, 'id', None),
            'tracking_number': getattr(r, 'tracking_number', None),
            'registration_id': getattr(r, 'registration_id', None),
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'mobile_no': getattr(reg, 'mobile_no', None) if reg else None,
            'barangay': getattr(reg.barangay, 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
            'deceased_name': getattr(r, 'deceased_name', None),
            'relationship': getattr(r, 'relationship', None),
            'amount': getattr(r, 'amount', None),
            'date_claim_expiry': str(getattr(r, 'date_claim_expiry', None)) if getattr(r, 'date_claim_expiry', None) else None,
            'date_claimed': str(getattr(r, 'date_claimed', None)) if getattr(r, 'date_claimed', None) else None,
            'cause_of_death': getattr(r, 'cause_of_death', None),
            'status': st,
            'status_id': sid,
            'processed_by': processed_by_name,
        })

    return render(request, 'mun_admin/burial_table.html', {'bsrcenter_data': data})
@login_required
def REAP_TABLE(request):
    """Render Peso_reap rows for municipal admin.

    Each row will include registration names, academic year id, semester name,
    status id/text, processed_by name, and is_released flag. The template
    `mun_admin/reap_table.html` will receive this data as `bsrcenter_data`.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    qs = (
        Peso_reap.objects
        .select_related('registration', 'status', 'processed_by', 'Academic_year__semester')
        .all()
        .order_by('id')
    )

    # Materialize queryset so we can inspect Academic_year.semester_id values
    objs = list(qs)

    # Collect semester IDs referenced by the related Academic_year objects
    semester_ids = set()
    for obj in objs:
        academic_obj = getattr(obj, 'Academic_year', None)
        if academic_obj is not None:
            sid_val = getattr(academic_obj, 'semester_id', None)
            if sid_val:
                semester_ids.add(sid_val)

    # Fetch semester names in one query and build a map
    sem_map = {}
    if semester_ids:
        for s in Semester.objects.filter(id__in=semester_ids).values('id', 'sem_name'):
            sem_map[s['id']] = s['sem_name']

    data = []
    for obj in objs:
        reg = getattr(obj, 'registration', None)
        try:
            sid = getattr(obj.status, 'id', None) if getattr(obj, 'status', None) else None
            st = STATUS_MAP.get(sid) or (obj.status.status_name if getattr(obj, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

        # academic year and semester — field name is `Academic_year` on the model
        academic_obj = getattr(obj, 'Academic_year', None)
        academic_year_id = getattr(academic_obj, 'id', None) if academic_obj else None
        academic_year = getattr(academic_obj, 'year', None) if academic_obj else None
        # prefer the pre-fetched semester when available via sem_map
        semester_name = ''
        if academic_obj is not None:
            sem_id = getattr(academic_obj, 'semester_id', None)
            if sem_id:
                semester_name = sem_map.get(sem_id, '')
            else:
                # fallback to related object attribute if present
                semester_name = getattr(getattr(academic_obj, 'semester', None), 'sem_name', '')

        processed_by_name = ''
        if getattr(obj, 'processed_by', None):
            pb = obj.processed_by
            processed_by_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

        data.append({
            'id': getattr(obj, 'id', None),
            'tracking_number': getattr(obj, 'tracking_number', None),
            'registration_id': getattr(obj, 'registration_id', None),
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'academic_year_id': academic_year_id,
            'academic_year': academic_year,
            'semester_name': semester_name,
            'status': st,
            'status_id': sid,
            'processed_by': processed_by_name,
            'is_released': getattr(obj, 'is_released', None),
            'date_added': str(getattr(obj, 'date_added', None)) if getattr(obj, 'date_added', None) else None,
        })

    return render(request, 'mun_admin/reap_table.html', {'bsrcenter_data': data})
@login_required
def TUPAD_TABLE(request):
    """Render Peso_tupad rows for municipal admin (read-only).

    Rows include registration names, beneficiary name, skills training name,
    status id/text, processed_by name, is_released, and date_claimed.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    qs = (
        Peso_tupad.objects
        .select_related('registration', 'status', 'processed_by', 'skills_training')
        .all()
        .order_by('id')
    )

    data = []
    for obj in qs:
        reg = getattr(obj, 'registration', None)
        try:
            sid = getattr(obj.status, 'id', None) if getattr(obj, 'status', None) else None
            st = STATUS_MAP.get(sid) or (obj.status.status_name if getattr(obj, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

        skills_name = ''
        if getattr(obj, 'skills_training', None):
            skills_name = getattr(obj.skills_training, 'Skills_name', '')

        processed_by_name = ''
        if getattr(obj, 'processed_by', None):
            pb = obj.processed_by
            processed_by_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

        data.append({
            'id': getattr(obj, 'id', None),
            'tracking_number': getattr(obj, 'tracking_number', None),
            'registration_id': getattr(obj, 'registration_id', None),
            'last_name': getattr(reg, 'last_name', None) if reg else None,
            'first_name': getattr(reg, 'first_name', None) if reg else None,
            'name_of_beneficiary': getattr(obj, 'name_of_beneficiary', None),
            'skills_training': skills_name,
            'status': st,
            'status_id': sid,
            'processed_by': processed_by_name,
            'is_released': bool(getattr(obj, 'is_released', False)),
            'date_claimed': str(getattr(obj, 'date_claimed', None)) if getattr(obj, 'date_claimed', None) else None,
            'date_issued': str(getattr(obj, 'date_issued', None)) if getattr(obj, 'date_issued', None) else None,
        })

    return render(request, 'mun_admin/tupad_table.html', {'bsrcenter_data': data})
@require_GET
@login_required
def EXPORT_MEDICALS(request):
    """Export Bsrcenter (Medicals) as CSV"""
    # prefetch related medicines through Bsrcenter_meds to avoid N+1 queries
    qs = Bsrcenter.objects.select_related('registration', 'processed_by', 'actioned_by').prefetch_related('bsrcenter_meds_set__medicines').all()
    # optional status filter from querystring (e.g. ?status=2 for approved)
    status = request.GET.get('status')
    filename_suffix = ''
    if status:
        try:
            status_int = int(status)
            qs = qs.filter(status_id=status_int)
            if status_int == 2:
                filename_suffix = '_approved'
        except Exception:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="medicals{filename_suffix}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tracking Number', 'Last Name', 'First Name', 'Barangay', 'Municipality', 'Date Claimed', 'Amount', 'Status', 'Processed By', 'Approved/Rejected By', 'Medicines'])
    for obj in qs:
        reg = obj.registration
        processed_by = ''
        if obj.processed_by:
            processed_by = f"{obj.processed_by.first_name} {obj.processed_by.last_name}".strip()
        actioned_by_name = ''
        actioned_by_obj = getattr(obj, 'actioned_by', None)
        if actioned_by_obj:
            actioned_by_name = f"{getattr(actioned_by_obj, 'first_name', '')} {getattr(actioned_by_obj, 'last_name', '')}".strip()
        # collect medicines for this bsrcenter (from Bsrcenter_meds)
        meds_qs = getattr(obj, 'bsrcenter_meds_set', None)
        meds_list = []
        if meds_qs is not None:
            for bm in meds_qs.all():
                if bm.medicines:
                    meds_list.append(bm.medicines.medicine_name)
        meds_str = ', '.join(meds_list)

        status_name = getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else ''
        writer.writerow([
            smart_str(obj.tracking_number or ''),
            smart_str(reg.last_name if reg else ''),
            smart_str(reg.first_name if reg else ''),
            smart_str(reg.barangay.barangay_name if reg and reg.barangay else ''),
            smart_str(reg.municipality.municipality_name if reg and reg.municipality else ''),
            smart_str(obj.date_claimed),
            smart_str(obj.amount),
            smart_str(status_name),
            smart_str(processed_by),
            smart_str(actioned_by_name),
            smart_str(meds_str),
        ])
    return response


@require_GET
@login_required
def EXPORT_BURIALS(request):
    """Export Bsrcenter_Burial as CSV"""
    qs = Bsrcenter_Burial.objects.select_related('registration', 'processed_by', 'actioned_by').all()
    # optional status filter from querystring
    status = request.GET.get('status')
    filename_suffix = ''
    if status:
        try:
            status_int = int(status)
            qs = qs.filter(status_id=status_int)
            if status_int == 2:
                filename_suffix = '_approved'
        except Exception:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="burials{filename_suffix}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tracking Number', 'Last Name', 'First Name', 'Deceased Name', 'Relationship', 'Date Claimed', 'Amount', 'Status', 'Processed By', 'Approved/Rejected By'])
    for obj in qs:
        reg = obj.registration
        processed_by = ''
        if obj.processed_by:
            processed_by = f"{obj.processed_by.first_name} {obj.processed_by.last_name}".strip()
        actioned_by_name = ''
        actioned_by_obj = getattr(obj, 'actioned_by', None)
        if actioned_by_obj:
            actioned_by_name = f"{getattr(actioned_by_obj, 'first_name', '')} {getattr(actioned_by_obj, 'last_name', '')}".strip()
        status_name = getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else ''
        writer.writerow([
            smart_str(obj.tracking_number or ''),
            smart_str(reg.last_name if reg else ''),
            smart_str(reg.first_name if reg else ''),
            smart_str(obj.deceased_name),
            smart_str(obj.relationship),
            smart_str(obj.date_claimed),
            smart_str(obj.amount),
            smart_str(status_name),
            smart_str(processed_by),
            smart_str(actioned_by_name),
        ])
    return response


@require_GET
@login_required
def EXPORT_REAPS(request):
    """Export Peso_reap as CSV"""
    # include Academic_year and its Semester to export human-readable year and semester
    qs = Peso_reap.objects.select_related('registration', 'processed_by', 'reap_type', 'Academic_year__semester', 'actioned_by').all()
    # optional status filter from querystring
    status = request.GET.get('status')
    filename_suffix = ''
    if status:
        try:
            status_int = int(status)
            qs = qs.filter(status_id=status_int)
            if status_int == 2:
                filename_suffix = '_approved'
        except Exception:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="reap{filename_suffix}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tracking Number', 'Last Name', 'First Name', 'Reap Type', 'Academic Year', 'Semester', 'Date Added', 'Is Released', 'Status', 'Processed By', 'Approved/Rejected By'])
    for obj in qs:
        reg = obj.registration
        processed_by = ''
        if obj.processed_by:
            processed_by = f"{obj.processed_by.first_name} {obj.processed_by.last_name}".strip()
        # academic year and semester
        academic_year = ''
        semester_name = ''
        academic_obj = getattr(obj, 'Academic_year', None)
        if academic_obj is not None:
            academic_year = getattr(academic_obj, 'year', '')
            # related Semester via select_related
            semester_name = getattr(getattr(academic_obj, 'semester', None), 'sem_name', '')
        status_name = getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else ''
        actioned_by_name = ''
        actioned_by_obj = getattr(obj, 'actioned_by', None)
        if actioned_by_obj:
            actioned_by_name = f"{getattr(actioned_by_obj, 'first_name', '')} {getattr(actioned_by_obj, 'last_name', '')}".strip()
        writer.writerow([
            smart_str(obj.tracking_number or ''),
            smart_str(reg.last_name if reg else ''),
            smart_str(reg.first_name if reg else ''),
            smart_str(obj.reap_type.type_name if obj.reap_type else ''),
            smart_str(academic_year),
            smart_str(semester_name),
            smart_str(obj.date_added),
            smart_str(obj.is_released),
            smart_str(status_name),
            smart_str(processed_by),
            smart_str(actioned_by_name),
        ])
    return response


@require_GET
@login_required
def EXPORT_TUPADS(request):
    """Export Peso_tupad as CSV"""
    qs = Peso_tupad.objects.select_related('registration', 'processed_by', 'skills_training', 'actioned_by').all()
    # optional status filter from querystring
    status = request.GET.get('status')
    filename_suffix = ''
    if status:
        try:
            status_int = int(status)
            qs = qs.filter(status_id=status_int)
            if status_int == 2:
                filename_suffix = '_approved'
        except Exception:
            pass

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="tupad{filename_suffix}.csv"'
    writer = csv.writer(response)
    writer.writerow(['Tracking Number', 'Last Name', 'First Name', 'Beneficiary Name', 'Skills Training', 'Date Issued', 'Is Released', 'Status', 'Processed By', 'Approved/Rejected By'])
    for obj in qs:
        reg = obj.registration
        processed_by = ''
        if obj.processed_by:
            processed_by = f"{obj.processed_by.first_name} {obj.processed_by.last_name}".strip()
        status_name = getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else ''
        actioned_by_name = ''
        actioned_by_obj = getattr(obj, 'actioned_by', None)
        if actioned_by_obj:
            actioned_by_name = f"{getattr(actioned_by_obj, 'first_name', '')} {getattr(actioned_by_obj, 'last_name', '')}".strip()
        writer.writerow([
            smart_str(obj.tracking_number or ''),
            smart_str(reg.last_name if reg else ''),
            smart_str(reg.first_name if reg else ''),
            smart_str(obj.name_of_beneficiary),
            smart_str(obj.skills_training.Skills_name if obj.skills_training else ''),
            smart_str(obj.date_issued),
            smart_str(obj.is_released),
            smart_str(status_name),
            smart_str(processed_by),
            smart_str(actioned_by_name),
        ])
    return response

