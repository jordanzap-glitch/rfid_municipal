from django.views.decorators.http import require_GET
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Status


def home(request):
    return render(request,'center_admin/home.html')

def APPROVAL_TABLE(request):
    """
    Build approval table using Bsrcenter and related Bsrcenter_meds and Status.

    - POST with registration_id will mark all Bsrcenter rows for that registration as approved (status id 2).
    - The template expects a context key `bsrcenter_data` (list of aggregated rows).
    """
    # Map status ids to canonical strings
    STATUS_MAP = {1: 'pending', 2: 'approved', 3: 'rejected'}

    # Handle POST: set status for a specific Bsrcenter row (preferred) or fallback to one row by registration
    if request.method == 'POST':
        # Prefer a specific bsrcenter row id so we only change one row even if multiple rows share the same registration
        bsrcenter_id = request.POST.get('bsrcenter_id')
        registration_id = request.POST.get('registration_id') or request.POST.get('id')
        try:
            target_status = int(request.POST.get('target_status') or 2)
        except Exception:
            target_status = 2

        try:
            if bsrcenter_id:
                # update only the specific row
                Bsrcenter.objects.filter(id=bsrcenter_id).update(status_id=target_status)
            elif registration_id:
                # fallback: update only one row for that registration (the earliest by id)
                one = Bsrcenter.objects.filter(registration_id=registration_id).order_by('id').first()
                if one:
                    Bsrcenter.objects.filter(id=one.id).update(status_id=target_status)
        except Exception:
            # tolerate errors and continue
            pass
        # Redirect after handling POST to avoid form re-submission on browser refresh (PRG pattern)
        return redirect(request.path)

    # Fetch Bsrcenter rows with registration and status; prefetch related medicines via Bsrcenter_meds
    Bsrcenters = (
        Bsrcenter.objects
        .select_related('registration', 'status')
        .prefetch_related('bsrcenter_meds_set__medicines')
        .all()
        .order_by('id')
    )

    # Build a flat list: one entry per Bsrcenter row (instead of aggregating by registration)
    data = []
    for b in Bsrcenters:
        reg = getattr(b, 'registration', None)

        # determine status string and id
        try:
            sid = getattr(b.status, 'id', None) if getattr(b, 'status', None) else None
            st = STATUS_MAP.get(sid) or (b.status.status_name if getattr(b, 'status', None) else '')
        except Exception:
            sid = None
            st = ''

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
        })

    context = {'bsrcenter_data': data}
    return render(request, 'center_admin/approval_meds_tbl.html', context)

# AJAX endpoint to get Bsrcenter info by id for modal
@require_GET
def GET_BSR_CENTER_INFO(request):
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    if not registration_id:
        return JsonResponse({'error': 'Missing registration_id'}, status=400)

    entries = (
        Bsrcenter.objects
        .select_related('registration', 'status')
        .prefetch_related('bsrcenter_meds_set__medicines')
        .filter(registration_id=registration_id)
    )
    if not entries.exists():
        return JsonResponse({'error': 'Not found'}, status=404)

    reg = entries[0].registration

    medicines_map = {}
    statuses = set()

    for b in entries:
        # collect status string
        try:
            sid = getattr(b.status, 'id', None)
            if sid == 2:
                statuses.add('approved')
            elif sid == 1:
                statuses.add('pending')
            elif sid == 3:
                statuses.add('rejected')
            else:
                # fallback to status_name
                statuses.add(b.status.status_name if b.status else '')
        except Exception:
            pass

        # collect medicines for this bsrcenter
        for bm in b.bsrcenter_meds_set.all():
            m = bm.medicines
            if not m:
                key = f"_none_{bm.id}"
                if key not in medicines_map:
                    medicines_map[key] = {
                        'id': None,
                        'name': '',
                        'amount': b.amount,
                        'date_claimed': str(b.date_claimed) if b.date_claimed else None,
                        'date_claim_expiry': str(b.date_claim_expiry) if b.date_claim_expiry else None,
                        'status': (b.status.status_name if b.status else ''),
                    }
                continue

            key = str(m.id)
            if key not in medicines_map:
                medicines_map[key] = {
                    'id': m.id,
                    'name': m.medicine_name,
                    'amount': b.amount,
                    'date_claimed': str(b.date_claimed) if b.date_claimed else None,
                    'date_claim_expiry': str(b.date_claim_expiry) if b.date_claim_expiry else None,
                    'status': (b.status.status_name if b.status else ''),
                }
            else:
                existing = medicines_map[key]
                try:
                    # prefer earliest expiry if present
                    if existing.get('date_claim_expiry') and b.date_claim_expiry:
                        if str(b.date_claim_expiry) < existing['date_claim_expiry']:
                            existing['date_claim_expiry'] = str(b.date_claim_expiry)
                    elif b.date_claim_expiry and not existing.get('date_claim_expiry'):
                        existing['date_claim_expiry'] = str(b.date_claim_expiry)
                except Exception:
                    pass

    medicines = list(medicines_map.values())

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
        'middle_name': reg.middle_name,
        'name_extension': reg.name_extension,
        'date_of_birth': str(reg.date_of_birth) if reg.date_of_birth else None,
        'mobile_no': reg.mobile_no,
        'gender': reg.gender,
        'civil_status': reg.civil_status,
        'occupation': reg.occupation,
        'email': reg.email,
        'province': reg.province.province_name if reg.province else '',
        'municipality': reg.municipality.municipality_name if reg.municipality else '',
        'barangay': reg.barangay.barangay_name if reg.barangay else '',
        'medicines': medicines,
        'status': agg_status,
    }
    return JsonResponse(data)


# New endpoint: return all Bsrcenter rows for a registration_id (raw rows + linked medicines)
@require_GET
def GET_BSRCENTER_BY_REGISTRATION(request):
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    if not registration_id:
        return JsonResponse({'error': 'Missing registration_id'}, status=400)

    entries = (
        Bsrcenter.objects
        .select_related('registration', 'status')
        .prefetch_related('bsrcenter_meds_set__medicines')
        .filter(registration_id=registration_id)
        .order_by('id')
    )

    if not entries.exists():
        return JsonResponse({'error': 'Not found'}, status=404)

    rows = []
    for b in entries:
        row = {
            'id': getattr(b, 'id', None),
            'registration_id': getattr(b, 'registration_id', None),
            'tracking_number': getattr(b, 'tracking_number', None),
            'amount': getattr(b, 'amount', None),
            'age': getattr(b, 'age', None),
            'diagnosis': getattr(b, 'diagnosis', None),
            'date_claimed': str(b.date_claimed) if getattr(b, 'date_claimed', None) else None,
            'date_claim_expiry': str(b.date_claim_expiry) if getattr(b, 'date_claim_expiry', None) else None,
            'status_id': getattr(b.status, 'id', None) if getattr(b, 'status', None) else None,
            'status_name': getattr(b.status, 'status_name', None) if getattr(b, 'status', None) else None,
        }

        meds = []
        for bm in b.bsrcenter_meds_set.all():
            m = getattr(bm, 'medicines', None)
            meds.append({
                'bsrcenter_meds_id': getattr(bm, 'id', None),
                'medicine_id': getattr(m, 'id', None) if m else None,
                'medicine_name': getattr(m, 'medicine_name', None) if m else None,
                'amount': getattr(bm, 'amount', None) or getattr(b, 'amount', None),
                'date_claimed': str(getattr(bm, 'date_claimed', None)) if getattr(bm, 'date_claimed', None) else (str(getattr(b, 'date_claimed', None)) if getattr(b, 'date_claimed', None) else None),
                'date_claim_expiry': str(getattr(bm, 'date_claim_expiry', None)) if getattr(bm, 'date_claim_expiry', None) else (str(getattr(b, 'date_claim_expiry', None)) if getattr(b, 'date_claim_expiry', None) else None),
            })

        row['medicines'] = meds
        rows.append(row)

    return JsonResponse({'entries': rows})

