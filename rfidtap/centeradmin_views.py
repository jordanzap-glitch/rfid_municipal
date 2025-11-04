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
    from app.models import Bsrcenter, Registration

    # Handle approval POST: accept registration_id and approve all Bsrcenter entries for that registration
    if request.method == 'POST':
        registration_id = request.POST.get('registration_id') or request.POST.get('id')
        if registration_id:
            try:
                entries = Bsrcenter.objects.filter(registration_id=registration_id)
                for b in entries:
                    # create an approved record per medicine if not exists
                    exists = Bsrcenter.objects.filter(
                        registration=b.registration,
                        medicines=b.medicines,
                        status='approved'
                    ).exists()
                    if not exists:
                        Bsrcenter.objects.create(
                            registration=b.registration,
                            medicines=b.medicines,
                            age=b.age,
                            amount=b.amount,
                            date_claimed=b.date_claimed,
                            date_claim_expiry=b.date_claim_expiry,
                            status='approved'
                        )
            except Exception:
                # keep behavior tolerant; ignore issues and continue
                pass

    # Aggregate Bsrcenter rows by registration
    Bsrcenters = Bsrcenter.objects.select_related('registration', 'medicines').all().order_by('registration_id')
    grouped = {}
    for b in Bsrcenters:
        reg = b.registration
        key = reg.id
        if key not in grouped:
            grouped[key] = {
                'registration_id': reg.id,
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
                'amounts': [],
                'medicines': [],
                'date_claim_expiries': [],
                'statuses': set(),
            }
        # append medicine info, avoid duplicates
        m_id = b.medicines.id if b.medicines else None
        m_name = b.medicines.medicine_name if b.medicines else ''
        if m_id and not any(m['id'] == m_id for m in grouped[key]['medicines']):
            grouped[key]['medicines'].append({'id': m_id, 'name': m_name})
        grouped[key]['amounts'].append(b.amount)
        grouped[key]['date_claim_expiries'].append(b.date_claim_expiry)
        grouped[key]['statuses'].add(b.status)

    # Build final list for template
    data = []
    for key, g in grouped.items():
        # Determine aggregated status: approved > pending > rejected > other
        statuses = g['statuses']
        if 'approved' in statuses:
            agg_status = 'approved'
        elif 'pending' in statuses:
            agg_status = 'pending'
        elif 'rejected' in statuses:
            agg_status = 'rejected'
        else:
            agg_status = ','.join(statuses) if statuses else ''

        medicine_names = ', '.join([m['name'] for m in g['medicines']])
        data.append({
            'registration_id': g['registration_id'],
            'rfid': g['rfid'],
            'last_name': g['last_name'],
            'first_name': g['first_name'],
            'middle_name': g['middle_name'],
            'name_extension': g['name_extension'],
            'date_of_birth': g['date_of_birth'],
            'mobile_no': g['mobile_no'],
            'gender': g['gender'],
            'civil_status': g['civil_status'],
            'occupation': g['occupation'],
            'email': g['email'],
            'province': g['province'],
            'municipality': g['municipality'],
            'barangay': g['barangay'],
            'age': g['age'],
            'amount': g['amounts'][0] if g['amounts'] else None,
            'medicine': medicine_names,
            'medicine_list': g['medicines'],
            'date_claim_expiry': g['date_claim_expiries'][0] if g['date_claim_expiries'] else None,
            'date_claim_expiry_list': g['date_claim_expiries'],
            'status': agg_status,
        })

    context = {'Bsrcenter_data': data}
    return render(request,'center_admin/approval_table.html', context)

# AJAX endpoint to get Bsrcenter info by id for modal
@require_GET
def GET_BSR_CENTER_INFO(request):
    from app.models import Bsrcenter, Registration
    registration_id = request.GET.get('registration_id') or request.GET.get('id')
    if not registration_id:
        return JsonResponse({'error': 'Missing registration_id'}, status=400)
    entries = Bsrcenter.objects.select_related('registration', 'medicines').filter(registration_id=registration_id)
    if not entries.exists():
        return JsonResponse({'error': 'Not found'}, status=404)
    reg = entries[0].registration
    # build unique medicines by medicine id to avoid duplicates in the modal
    medicines_map = {}
    statuses = set()
    for b in entries:
        m = b.medicines
        statuses.add(b.status)
        if not m:
            # include entries without medicine id using a generated key
            key = f"_none_{b.id}"
            if key not in medicines_map:
                medicines_map[key] = {
                    'id': None,
                    'name': '',
                    'amount': b.amount,
                    'date_claimed': str(b.date_claimed) if b.date_claimed else None,
                    'date_claim_expiry': str(b.date_claim_expiry) if b.date_claim_expiry else None,
                    'status': b.status,
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
                'status': b.status,
            }
        else:
            # if duplicate medicine appears, prefer earliest expiry (if present) and keep first name/amount
            existing = medicines_map[key]
            try:
                # compare expiries if both present
                if existing.get('date_claim_expiry') and b.date_claim_expiry:
                    # choose earliest non-null expiry
                    if b.date_claim_expiry and str(b.date_claim_expiry) < existing['date_claim_expiry']:
                        existing['date_claim_expiry'] = str(b.date_claim_expiry)
                elif b.date_claim_expiry and not existing.get('date_claim_expiry'):
                    existing['date_claim_expiry'] = str(b.date_claim_expiry)
            except Exception:
                pass

    medicines = list(medicines_map.values())

    # aggregated status
    if 'approved' in statuses:
        agg_status = 'approved'
    elif 'pending' in statuses:
        agg_status = 'pending'
    elif 'rejected' in statuses:
        agg_status = 'rejected'
    else:
        agg_status = ','.join(statuses) if statuses else ''

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

