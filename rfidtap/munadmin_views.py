from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from django.db.models import Count
from django.db.models.functions import ExtractYear
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Bsrcenter, Bsrcenter_Burial, Peso_reap, Peso_tupad, Occupation, Academic_year, Semester, Medicines, Bsrcenter_meds, Dswd_senior
import csv
import json
import logging
from django.utils.encoding import smart_str


@login_required(login_url='/')
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
    # indicate whether any PESO staff currently have can_release enabled
    try:
        pesostaff_release_enabled = CustomUser.objects.filter(user_type='7', can_release=True).exists()
    except Exception:
        pesostaff_release_enabled = False
    context.update({'pesostaff_release_enabled': pesostaff_release_enabled})
    return render(request, 'mun_admin/home.html', context)


@require_POST
@login_required(login_url='/')
def TOGGLE_PESO_RELEASE(request):
    """Toggle the `can_release` flag for all PESO staff users.

    Expects JSON {"enable": true|false} in the request body.
    Only municipal admins (user_type == '3') may perform this action.
    """
    # simple permission check for municipal admin
    try:
        if getattr(request.user, 'user_type', None) != '3':
            return JsonResponse({'error': 'forbidden'}, status=403)
    except Exception:
        return JsonResponse({'error': 'forbidden'}, status=403)

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    enable = payload.get('enable')
    if enable is None:
        return JsonResponse({'error': 'missing_enable'}, status=400)

    try:
        # user_type '7' corresponds to PESO staff and '9' to DSWD staff in CustomUser.USER mapping
        updated = CustomUser.objects.filter(user_type__in=['7', '9']).update(can_release=bool(enable))
        return JsonResponse({'success': True, 'enabled': bool(enable), 'updated_count': updated})
    except Exception as e:
        logging.exception('Failed to toggle peso release')
        return JsonResponse({'error': 'db_error', 'message': str(e)}, status=500)

@login_required(login_url='/')
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
                'sem_name': getattr(getattr(ay, 'semester', None), 'sem_name', ''),
                'is_active': getattr(ay, 'is_active', 0),
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
    reap_academic_years = []
    try:
        # Determine academic years referenced by the (possibly filtered) Peso_reap queryset
        reap_year_ids = list(reap_qs.exclude(Academic_year_id__isnull=True).values_list('Academic_year_id', flat=True).distinct())
        reap_academic_years = []
        import datetime
        if reap_year_ids:
            for ay in Academic_year.objects.select_related('semester').filter(id__in=reap_year_ids).exclude(is_active=1).order_by('-year'):
                raw_year = getattr(ay, 'year', None)
                year_label = ''
                try:
                    if isinstance(raw_year, (datetime.date, datetime.datetime)):
                        year_label = str(raw_year.year)
                    elif isinstance(raw_year, int):
                        year_label = str(raw_year)
                    elif isinstance(raw_year, str):
                        if len(raw_year) >= 4 and raw_year[:4].isdigit():
                            year_label = raw_year[:4]
                        else:
                            year_label = raw_year
                    else:
                        year_label = str(raw_year) if raw_year is not None else ''
                except Exception:
                    year_label = str(raw_year) if raw_year is not None else ''

                reap_academic_years.append({
                    'id': getattr(ay, 'id', None),
                    'year': year_label,
                    'sem_name': getattr(getattr(ay, 'semester', None), 'sem_name', '')
                })

        # Count based directly on the Peso_reap table grouped by Academic_year_id
        # This ensures the chart reflects counts keyed by peso_reap.Academic_year_id
        counts_qs = Peso_reap.objects.values('Academic_year_id').annotate(count=Count('id'))
        counts_map = {c['Academic_year_id']: c['count'] for c in counts_qs}

        reap_trend_labels = []
        reap_trend_data = []
        # Build labels using the full academic_years list so all academic years are shown
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

    # Build REAP status series (Active / Inactive) per Academic_year
    try:
        # Build Active / Inactive maps from the Peso_reap table (grouped by Academic_year_id)
        active_qs = Peso_reap.objects.filter(next=1).values('Academic_year_id').annotate(count=Count('id'))
        inactive_qs = Peso_reap.objects.exclude(next=1).values('Academic_year_id').annotate(count=Count('id'))

        active_map = {c['Academic_year_id']: c['count'] for c in active_qs}
        inactive_map = {c['Academic_year_id']: c['count'] for c in inactive_qs}

        reap_status_active = []
        reap_status_inactive = []
        # Exclude academic years flagged as `is_active==1` from the Active/Inactive series
        filtered_academic_years = [ay for ay in academic_years if not ay.get('is_active')]
        for ay in filtered_academic_years:
            ay_id = ay.get('id')
            reap_status_active.append(active_map.get(ay_id, 0))
            reap_status_inactive.append(inactive_map.get(ay_id, 0))
        # Build labels for the REAP status chart aligned with the filtered academic years
        reap_status_labels = []
        for ay in filtered_academic_years:
            label = ay.get('year') or ''
            sem = ay.get('sem_name')
            if sem:
                label = f"{label} - {sem}"
            reap_status_labels.append(label)
    except Exception:
        reap_status_active = []
        reap_status_inactive = []
        reap_status_labels = []

    # add trend arrays and REAP status series to context
    context.update({
        'reap_trend_labels': reap_trend_labels,
        'reap_trend_data': reap_trend_data,
        'reap_status_active': reap_status_active,
        'reap_status_inactive': reap_status_inactive,
        'reap_status_labels': reap_status_labels,
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

    # Compute Senior (DSWD) release progress metrics for analytics card
    try:
        senior_total = Dswd_senior.objects.count()
        senior_released = Dswd_senior.objects.filter(is_released=True).count()
    except Exception:
        senior_total = 0
        senior_released = 0

    try:
        senior_released_pct = int(round((senior_released / senior_total) * 100)) if senior_total else 0
    except Exception:
        senior_released_pct = 0

    context.update({
        'senior_total': senior_total,
        'senior_released': senior_released,
        'senior_released_pct': senior_released_pct,
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

    # Build Senior (DSWD) yearly trend based on date_issued year
    try:
        senior_counts_qs = (
            Dswd_senior.objects
            .exclude(date_issued__isnull=True)
            .annotate(year=ExtractYear('date_issued'))
            .values('year')
            .annotate(count=Count('id'))
            .order_by('year')
        )
        senior_trend_labels = []
        senior_trend_data = []
        for r in senior_counts_qs:
            year = r.get('year')
            senior_trend_labels.append(str(year) if year is not None else '')
            senior_trend_data.append(r.get('count', 0))
    except Exception:
        senior_trend_labels = []
        senior_trend_data = []

    context.update({
        'tupad_trend_labels': tupad_trend_labels,
        'tupad_trend_data': tupad_trend_data,
        'senior_trend_labels': senior_trend_labels,
        'senior_trend_data': senior_trend_data,
    })

    return render(request, 'mun_admin/analytics_home.html', context)


@login_required(login_url='/')
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


@require_GET
@login_required(login_url='/')
def GET_BSR_CENTER_INFO_MEDS(request):
    """Return JSON details for a Bsrcenter medical row for the modal.

    Accepts query param `registration_id` which may be either the
    `Bsrcenter.id` or a `Registration.id`. Attempts to find a matching
    Bsrcenter record then returns basic registration fields plus a
    `medicines` array of {name, date_claim_expiry} objects.
    """
    reg_id = request.GET.get('registration_id')
    if not reg_id:
        return JsonResponse({'error': 'missing registration_id'}, status=400)

    b = None
    try:
        # Try to treat param as Bsrcenter.id first
        b = (
            Bsrcenter.objects
            .select_related('registration', 'status')
            .prefetch_related('bsrcenter_meds_set__medicines')
            .get(id=int(reg_id))
        )
    except Exception:
        # Fallback: try to find latest Bsrcenter row for a registration_id
        try:
            b = (
                Bsrcenter.objects
                .select_related('registration', 'status')
                .prefetch_related('bsrcenter_meds_set__medicines')
                .filter(registration_id=int(reg_id))
                .order_by('-id')
                .first()
            )
        except Exception:
            b = None

    if not b:
        return JsonResponse({'error': 'not_found'}, status=404)

    reg = getattr(b, 'registration', None)
    # basic registration fields
    resp = {
        'rfid': getattr(reg, 'rfid', '') if reg else '',
        'last_name': getattr(reg, 'last_name', '') if reg else '',
        'first_name': getattr(reg, 'first_name', '') if reg else '',
        'mobile_no': getattr(reg, 'mobile_no', '') if reg else '',
        'barangay': getattr(reg.barangay, 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'status': getattr(b.status, 'status_name', '') if getattr(b, 'status', None) else '',
        'medicines': [],
    }

    # collect medicines info from related Bsrcenter_meds
    try:
        for bm in b.bsrcenter_meds_set.all():
            # preferred relation is `medicines` (prefetched); the Medicines model uses `medicine_name`
            med_obj = getattr(bm, 'medicines', None)
            med_name = None
            if med_obj is not None:
                med_name = getattr(med_obj, 'medicine_name', None) or getattr(med_obj, 'name', None)
            # fallbacks on the bsrcenter_meds row
            if not med_name:
                med_name = getattr(bm, 'medicine_name', None) or getattr(bm, 'name', None) or ''

            resp['medicines'].append({
                'name': med_name,
                'date_claim_expiry': str(getattr(bm, 'date_claim_expiry', None)) if getattr(bm, 'date_claim_expiry', None) else None,
            })
    except Exception:
        # if anything goes wrong collecting medicines, return what we have
        pass

    return JsonResponse(resp)


@require_GET
@login_required(login_url='/')
def GET_BSR_CENTER_INFO_BURIALS(request):
    """Return JSON burial details for the modal.

    Accepts `registration_id` which may be a Bsrcenter_Burial.id or a
    Registration.id. Returns registration fields plus `deceased_rows` —
    a list of burial rows for the registration (most recent first).
    """
    reg_id = request.GET.get('registration_id')
    if not reg_id:
        return JsonResponse({'error': 'missing registration_id'}, status=400)

    b = None
    try:
        # try as Bsrcenter_Burial id first
        b = (
            Bsrcenter_Burial.objects
            .select_related('registration', 'status')
            .get(id=int(reg_id))
        )
    except Exception:
        try:
            # fallback: get latest burial for a registration id
            b = (
                Bsrcenter_Burial.objects
                .select_related('registration', 'status')
                .filter(registration_id=int(reg_id))
                .order_by('-id')
                .first()
            )
        except Exception:
            b = None

    if not b:
        return JsonResponse({'error': 'not_found'}, status=404)

    reg = getattr(b, 'registration', None)
    reg_pk = getattr(reg, 'id', None) if reg else getattr(b, 'registration_id', None)

    resp = {
        'last_name': getattr(reg, 'last_name', '') if reg else '',
        'first_name': getattr(reg, 'first_name', '') if reg else '',
        'mobile_no': getattr(reg, 'mobile_no', '') if reg else '',
        'barangay': getattr(reg.barangay, 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'status': getattr(b.status, 'status_name', '') if getattr(b, 'status', None) else '',
        'deceased_rows': [],
    }

    try:
        qs = Bsrcenter_Burial.objects.select_related('registration', 'status').filter(registration_id=reg_pk).order_by('-id')
        for r in qs:
            resp['deceased_rows'].append({
                'deceased_name': getattr(r, 'deceased_name', None),
                'relationship': getattr(r, 'relationship', None),
                'date_claimed': str(getattr(r, 'date_claimed', None)) if getattr(r, 'date_claimed', None) else None,
                'date_claim_expiry': str(getattr(r, 'date_claim_expiry', None)) if getattr(r, 'date_claim_expiry', None) else None,
                'cause_of_death': getattr(r, 'cause_of_death', None),
                'amount': getattr(r, 'amount', None),
            })
    except Exception:
        # return what we have if something fails
        pass

    return JsonResponse(resp)

@login_required(login_url='/')
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
@require_GET
@login_required(login_url='/')
def GET_PESO_REAP_INFO(request):
    """Return JSON details for a Peso_reap row for the modal.

    Accepts query param `reap_id` which may be either the `Peso_reap.id`
    or a `Registration.id`. Attempts to find a matching Peso_reap record
    then returns basic registration fields plus REAP-specific fields.
    """
    # Support both `reap_id` (Peso_reap id or registration id) and
    # `tracking_number` (tracking number used in approval UI).
    tracking = request.GET.get('tracking_number')
    rid = request.GET.get('reap_id')

    # If tracking_number provided, return a `reap_rows` array similar to admin view
    if tracking:
        rows = []
        try:
            qs = (
                Peso_reap.objects
                .select_related('registration', 'reap_type', 'Academic_year__semester', 'processed_by', 'status')
                .filter(tracking_number=str(tracking))
                .order_by('-id')
            )
            # attempt to capture registration-level fields from the most recent row
            first_reg = None
            if qs:
                first_obj = qs[0]
                first_reg = getattr(first_obj, 'registration', None)
            for r in qs:
                # processed by name
                proc_name = ''
                if getattr(r, 'processed_by', None):
                    pb = r.processed_by
                    proc_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

                # reap type name — prefer related object's fields but accept several possible names
                reap_type_name = ''
                try:
                    rt = getattr(r, 'reap_type', None)
                    reap_type_name = (
                        (getattr(rt, 'reap_type_name', None) if rt is not None else None)
                        or (getattr(rt, 'type_name', None) if rt is not None else None)
                        or (getattr(rt, 'name', None) if rt is not None else None)
                        or getattr(r, 'reap_type_name', None)
                        or ''
                    )
                except Exception:
                    reap_type_name = ''

                # semester name
                sem_name = ''
                try:
                    ay = getattr(r, 'Academic_year', None)
                    if ay:
                        sem = getattr(ay, 'semester', None)
                        if sem:
                            sem_name = getattr(sem, 'sem_name', '')
                except Exception:
                    sem_name = ''

                rows.append({
                    'tracking_number': getattr(r, 'tracking_number', ''),
                    'reap_type_name': reap_type_name,
                    'semester_name': sem_name,
                    'processed_by_name': proc_name,
                    'date_added': str(getattr(r, 'date_added', None)) if getattr(r, 'date_added', None) else None,
                    'status_name': getattr(getattr(r, 'status', None), 'status_name', '') or getattr(r, 'status_name', ''),
                })
        except Exception:
            rows = []

        resp = {'reap_rows': rows}
        # attach top-level registration fields if available so modal shows names/contact/status
        if first_reg is not None:
            resp.update({
                'last_name': getattr(first_reg, 'last_name', '') or '',
                'first_name': getattr(first_reg, 'first_name', '') or '',
                'mobile_no': getattr(first_reg, 'mobile_no', '') or '',
                'barangay': getattr(getattr(first_reg, 'barangay', None), 'barangay_name', '') or getattr(first_reg, 'barangay', '') or '',
            })
        # if rows present, also include a summary status from the most recent row
        if rows:
            resp.setdefault('status', rows[0].get('status_name', ''))

        return JsonResponse(resp)

    # Fallback: handle single-object requests via reap_id (existing behavior)
    if not rid:
        return JsonResponse({'error': 'missing reap_id_or_tracking_number'}, status=400)

    obj = None
    try:
        # try to interpret as Peso_reap.id first
        obj = (
            Peso_reap.objects
            .select_related('registration', 'Academic_year__semester', 'status', 'processed_by')
            .get(id=int(rid))
        )
    except Exception:
        try:
            # fallback: latest Peso_reap row for a registration_id
            obj = (
                Peso_reap.objects
                .select_related('registration', 'Academic_year__semester', 'status', 'processed_by')
                .filter(registration_id=int(rid))
                .order_by('-id')
                .first()
            )
        except Exception:
            obj = None

    if not obj:
        return JsonResponse({'error': 'not_found'}, status=404)

    reg = getattr(obj, 'registration', None)
    resp = {
        'last_name': getattr(reg, 'last_name', '') if reg else '',
        'first_name': getattr(reg, 'first_name', '') if reg else '',
        'mobile_no': getattr(reg, 'mobile_no', '') if reg else '',
        'barangay': getattr(reg.barangay, 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'status': getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else '',
        'academic_year': getattr(getattr(obj, 'Academic_year', None), 'year', '') if getattr(obj, 'Academic_year', None) else '',
        'semester_name': '',
        'processed_by': '',
        'reap_type_name': '',
        'is_released': bool(getattr(obj, 'is_released', False)),
        'date_added': str(getattr(obj, 'date_added', None)) if getattr(obj, 'date_added', None) else None,
    }

    # try to resolve semester name
    try:
        ay = getattr(obj, 'Academic_year', None)
        if ay:
            sem = getattr(ay, 'semester', None)
            if sem:
                resp['semester_name'] = getattr(sem, 'sem_name', '')
    except Exception:
        pass

    # processed_by display
    try:
        if getattr(obj, 'processed_by', None):
            pb = obj.processed_by
            resp['processed_by'] = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()
    except Exception:
        pass

    # try to resolve reap type name for single-object requests
    try:
        rt = getattr(obj, 'reap_type', None)
        resp['reap_type_name'] = (
            (getattr(rt, 'reap_type_name', None) if rt is not None else None)
            or (getattr(rt, 'type_name', None) if rt is not None else None)
            or (getattr(rt, 'name', None) if rt is not None else None)
            or getattr(obj, 'reap_type_name', None)
            or ''
        )
    except Exception:
        pass

    return JsonResponse(resp)


@require_GET
@login_required(login_url='/')
def GET_PESO_TUPAD_INFO(request):
    """Return Peso_tupad rows and registration info for modal.

    Accepts `registration_id` or `tracking_number` (preferred). Returns
    registration fields and `tupad_rows` array mirroring `pesoadmin_views.GET_PESO_TUPAD_INFO`.
    """
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    tracking_number = request.GET.get('tracking_number')

    if not registration_id and not tracking_number:
        return JsonResponse({'error': 'missing registration_id_or_tracking_number'}, status=400)

    base_qs = (
        Peso_tupad.objects
        .select_related('registration', 'status', 'skills_training', 'processed_by')
        .order_by('id')
    )

    if tracking_number:
        entries = base_qs.filter(tracking_number=tracking_number)
    else:
        try:
            entries = base_qs.filter(registration_id=int(registration_id))
        except Exception:
            entries = base_qs.none()

    if not entries.exists():
        return JsonResponse({'error': 'not_found'}, status=404)

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
            'processed_by_name': (f"{getattr(e.processed_by, 'first_name', '')} {getattr(e.processed_by, 'last_name', '')}".strip() if getattr(e, 'processed_by', None) else None),
            'date_issued': str(getattr(e, 'date_issued', None)) if getattr(e, 'date_issued', None) else None,
            'date_issued_expiry': str(getattr(e, 'date_issued_expiry', None)) if getattr(e, 'date_issued_expiry', None) else None,
            'is_released': getattr(e, 'is_released', None),
            'is_completed': getattr(e, 'is_completed', None),
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
        'registration_id': getattr(reg, 'id', None),
        'rfid': getattr(reg, 'rfid', None),
        'last_name': getattr(reg, 'last_name', None),
        'first_name': getattr(reg, 'first_name', None),
        'mobile_no': getattr(reg, 'mobile_no', None),
        'barangay': getattr(getattr(reg, 'barangay', None), 'barangay_name', '') if getattr(reg, 'barangay', None) else (getattr(reg, 'barangay', '') if reg else ''),
        'tupad_rows': rows,
        'status': agg_status,
    }

    return JsonResponse(data)
@login_required(login_url='/')
def SENIOR_TABLE(request):
    """Render Dswd_senior rows for municipal admin (read-only).

    Builds a `bsrcenter_data` list similar to dswd admin approval table but read-only.
    """
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    qs = (
        Dswd_senior.objects
        .select_related('registration', 'status', 'processed_by')
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
            'date_issued': str(getattr(obj, 'date_issued', None)) if getattr(obj, 'date_issued', None) else None,
            'date_issued_expiry': str(getattr(obj, 'date_issued_expiry', None)) if getattr(obj, 'date_issued_expiry', None) else None,
            'processed_by': processed_by_name,
            'status': st,
            'status_id': sid,
            'is_released': getattr(obj, 'is_released', None),
            'is_completed': getattr(obj, 'is_completed', None),
        })

    return render(request, 'mun_admin/senior_table.html', {'bsrcenter_data': data})


@require_GET
@login_required(login_url='/')
def GET_DSWD_SENIOR_INFO(request):
    """Return JSON details for Dswd_senior rows for the modal.

    Accepts `dswd_id` (Dswd_senior.id or registration id) or `tracking_number`.
    Returns top-level registration fields plus `dswd_rows` array.
    """
    tracking = request.GET.get('tracking_number')
    sid = request.GET.get('dswd_id') or request.GET.get('registration_id') or request.GET.get('id')

    if tracking:
        rows = []
        first_reg = None
        try:
            qs = (
                Dswd_senior.objects
                .select_related('registration', 'status', 'processed_by')
                .filter(tracking_number=str(tracking))
                .order_by('-id')
            )
            if qs:
                first_reg = getattr(qs[0], 'registration', None)
            for r in qs:
                proc_name = ''
                if getattr(r, 'processed_by', None):
                    pb = r.processed_by
                    proc_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

                rows.append({
                    'tracking_number': getattr(r, 'tracking_number', ''),
                    'date_issued': str(getattr(r, 'date_issued', None)) if getattr(r, 'date_issued', None) else None,
                    'date_issued_expiry': str(getattr(r, 'date_issued_expiry', None)) if getattr(r, 'date_issued_expiry', None) else None,
                    'processed_by_name': proc_name,
                    'status_name': getattr(getattr(r, 'status', None), 'status_name', '') or getattr(r, 'status_name', ''),
                })
        except Exception:
            rows = []

        resp = {'dswd_rows': rows}
        if first_reg is not None:
            resp.update({
                'last_name': getattr(first_reg, 'last_name', '') or '',
                'first_name': getattr(first_reg, 'first_name', '') or '',
                'mobile_no': getattr(first_reg, 'mobile_no', '') or '',
                'barangay': getattr(getattr(first_reg, 'barangay', None), 'barangay_name', '') or getattr(first_reg, 'barangay', '') or '',
            })
        if rows:
            resp.setdefault('status', rows[0].get('status_name', ''))
        return JsonResponse(resp)

    if not sid:
        return JsonResponse({'error': 'missing dswd_id_or_tracking_number'}, status=400)

    obj = None
    try:
        obj = (
            Dswd_senior.objects
            .select_related('registration', 'status', 'processed_by')
            .get(id=int(sid))
        )
    except Exception:
        try:
            obj = (
                Dswd_senior.objects
                .select_related('registration', 'status', 'processed_by')
                .filter(registration_id=int(sid))
                .order_by('-id')
                .first()
            )
        except Exception:
            obj = None

    if not obj:
        return JsonResponse({'error': 'not_found'}, status=404)

    reg = getattr(obj, 'registration', None)
    resp = {
        'last_name': getattr(reg, 'last_name', '') if reg else '',
        'first_name': getattr(reg, 'first_name', '') if reg else '',
        'mobile_no': getattr(reg, 'mobile_no', '') if reg else '',
        'barangay': getattr(getattr(reg, 'barangay', None), 'barangay_name', '') if reg and getattr(reg, 'barangay', None) else (reg.barangay if reg else ''),
        'status': getattr(obj.status, 'status_name', '') if getattr(obj, 'status', None) else '',
        'dswd_rows': [],
    }

    try:
        qs = Dswd_senior.objects.select_related('registration', 'status', 'processed_by').filter(registration_id=getattr(reg, 'id', None)).order_by('-id')
        for r in qs:
            proc_name = ''
            if getattr(r, 'processed_by', None):
                pb = r.processed_by
                proc_name = f"{getattr(pb, 'first_name', '')} {getattr(pb, 'last_name', '')}".strip()

            resp['dswd_rows'].append({
                'tracking_number': getattr(r, 'tracking_number', None),
                'date_issued': str(getattr(r, 'date_issued', None)) if getattr(r, 'date_issued', None) else None,
                'date_issued_expiry': str(getattr(r, 'date_issued_expiry', None)) if getattr(r, 'date_issued_expiry', None) else None,
                'processed_by_name': proc_name,
                'status_name': getattr(getattr(r, 'status', None), 'status_name', '') or getattr(r, 'status_name', ''),
            })
    except Exception:
        pass

    return JsonResponse(resp)
@login_required(login_url='/')
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
@login_required(login_url='/')
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
@login_required(login_url='/')
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
@login_required(login_url='/')
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
@login_required(login_url='/')
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
@login_required(login_url='/')
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

