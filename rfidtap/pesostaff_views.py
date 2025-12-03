from django.views.decorators.http import require_GET, require_POST
from django.shortcuts import render,redirect, HttpResponse, get_object_or_404
from django.contrib.auth import authenticate, logout, login, get_user_model
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from django.db.models import Q
from app.models import CustomUser, Registration, RfidAuth, Province, Municipality, Barangay, Medicines, Bsrcenter, Bsrcenter_meds, Bsrcenter_Burial, Peso_reap, Skills_training, Peso_tupad, Academic_year, Reap_type, Civil_status, Occupation
from django.views.decorators.csrf import csrf_exempt
from datetime import date, datetime as _dt
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import json, uuid, logging


@login_required(login_url='/')
def home(request):
    return render(request, 'peso_staff/home.html')

@login_required(login_url='/')
def REAP_FORM(request):
    """Handle REAP form for PESO staff.

    GET: render the form.
    POST: validate RFID, check for existing unreleased REAP and create a new Peso_reap record.
    """
    # get currently active academic year (with semester) for display
    active_ay = Academic_year.objects.select_related('semester').filter(is_active=True).first()

    # fetch available reap types for the template
    reap_types = Reap_type.objects.all()

    if request.method == 'POST':
        rfid = request.POST.get('rfid')
        # document checkboxes
        biodata = bool(request.POST.get('biodata'))
        cert_registration = bool(request.POST.get('cert_registration'))
        cert_grades = bool(request.POST.get('cert_grades'))
        official_receipt = bool(request.POST.get('official_receipt'))
        barangay_indigency = bool(request.POST.get('barangay_indigency'))
        barangay_recidency = bool(request.POST.get('barangay_recidency'))
        # (date fields removed) no longer accept date_claimed/date_claim_expiry from form

        # reap type selection (optional) - read raw then normalize
        reap_type_raw = request.POST.get('reap_type')
        reap_type_id = None
        if reap_type_raw:
            try:
                rid = int(reap_type_raw)
                if Reap_type.objects.filter(id=rid).exists():
                    reap_type_id = rid
            except (ValueError, TypeError):
                reap_type_id = None

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            reap_type_display = ''
            if reap_type_raw:
                try:
                    reap_type_display = Reap_type.objects.filter(id=reap_type_raw).values_list('type_name', flat=True).first() or ''
                except Exception:
                    reap_type_display = ''
            return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types, 'selected_reap_type': reap_type_raw, 'reap_type_display': reap_type_display})

        # If no reap_type selected, choose default based on previous assistance: New if none, Renew if exists
        if not reap_type_id:
            try:
                # use id-based filter to avoid extra joins
                prev_exists = Peso_reap.objects.filter(registration_id=registration.id).exists()
                desired = 'New' if not prev_exists else 'Renew'
                rt = Reap_type.objects.filter(type_name__iexact=desired).first()
                if not rt:
                    rt = Reap_type.objects.filter(type_name__icontains=desired).first()
                if rt:
                    reap_type_id = rt.id
                    reap_type_raw = str(rt.id)
            except Exception:
                pass

        # compute display name for template context
        reap_type_display = ''
        if reap_type_id:
            try:
                reap_type_display = Reap_type.objects.filter(id=reap_type_id).values_list('type_name', flat=True).first() or ''
            except Exception:
                reap_type_display = ''

        # Support follow-up: if a hidden `reap_id` is provided, update that record
        # We handle this early so follow-up updates are not blocked by the
        # "existing unreleased REAP" creation checks that follow.
        existing_reap_id = request.POST.get('reap_id') or request.POST.get('existing_reap_id')
        if existing_reap_id:
            try:
                reap_obj = Peso_reap.objects.get(pk=int(existing_reap_id))
                # ensure the reap belongs to the scanned registration
                if getattr(reap_obj.registration, 'id', None) != registration.id:
                    messages.error(request, 'Referenced REAP does not belong to this registration.')
                    return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types})

                # update document fields and completion flag
                reap_obj.biodata = biodata
                reap_obj.certificate_of_reg = cert_registration
                reap_obj.certificate_of_grades = cert_grades
                reap_obj.official_receipt = official_receipt
                reap_obj.barangay_indigency = barangay_indigency
                reap_obj.barangay_recidency = barangay_recidency
                try:
                    if request.user and request.user.is_authenticated:
                        reap_obj.processed_by_id = request.user.id
                except Exception:
                    pass
                # set completion flags if model has them
                try:
                    reap_obj.is_completed = bool(biodata and cert_registration and cert_grades and official_receipt and barangay_indigency and barangay_recidency)
                except Exception:
                    pass
                try:
                    reap_obj.is_complete = bool(biodata and cert_registration and cert_grades and official_receipt and barangay_indigency and barangay_recidency)
                except Exception:
                    pass
                reap_obj.save()
                messages.success(request, 'REAP updated successfully.')
                # update session payload for modal if needed
                request.session['recent_reap'] = {
                    'id': reap_obj.id,
                    'tracking_number': getattr(reap_obj, 'tracking_number', ''),
                    'first_name': registration.first_name,
                    'last_name': registration.last_name,
                    'biodata': reap_obj.biodata,
                    'certificate_of_reg': reap_obj.certificate_of_reg,
                    'certificate_of_grades': reap_obj.certificate_of_grades,
                    'official_receipt': reap_obj.official_receipt,
                    'barangay_indigency': reap_obj.barangay_indigency,
                    'barangay_recidency': reap_obj.barangay_recidency,
                    'academic_year': ((reap_obj.Academic_year.year.strftime('%Y') if getattr(reap_obj.Academic_year, 'year', None) else '') + (f" ({reap_obj.Academic_year.semester.sem_name})" if getattr(reap_obj.Academic_year, 'semester', None) else "")) if getattr(reap_obj, 'Academic_year', None) else '',
                }
                return redirect('reap_form')
            except Peso_reap.DoesNotExist:
                messages.error(request, 'Referenced REAP not found for update.')
                return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types})

        # Prevent creating another REAP when there is an active assistance:
        # Rules:
        # - Always block if there is an unreleased REAP (is_released == False).
        # - If there is an active academic year, block if there's an existing REAP
        #   in that same academic year with status == 1 (pending).
        # - Allow submission if the existing REAP in the same AY has status 2 (approved)
        #   or 3 (rejected) so the user can resubmit.
        # Check unreleased first (use id-based filter)
        if Peso_reap.objects.filter(registration_id=registration.id, is_released=False).exists():
            messages.error(request, 'Cannot save REAP: there is an unreleased REAP for this registration.')
            return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types})

        # If there's an active academic year, check for pending (status=1) submissions
        if active_ay:
            # use id-based lookups to avoid unnecessary joins
            pending_same_ay = Peso_reap.objects.filter(registration_id=registration.id, Academic_year_id=active_ay.id, status_id=1).exists()
            if pending_same_ay:
                messages.error(request, 'Cannot save REAP: a pending REAP already exists for the active academic year.')
                return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types})

        # Determine if all required documents are present -> mark completed
        all_docs_present = bool(biodata and cert_registration and cert_grades and official_receipt and barangay_indigency and barangay_recidency)

        

        # Create the Peso_reap record
        reap = None
        MAX_ATTEMPTS = 5
        try:
            for attempt in range(MAX_ATTEMPTS):
                try:
                    with transaction.atomic():
                        def _gen_tracking():
                            return f"PESO-R-{uuid.uuid4().hex[:10].upper()}"

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
                            Academic_year_id=(active_ay.id if active_ay else (request.POST.get('academic_year_id') or None)),
                            reap_type_id=(reap_type_id or None),
                            # set completion flag on creation if all docs present
                            **({'is_completed': True} if all_docs_present else {}),
                        )
                    break  # success
                except IntegrityError:
                    # likely tracking collision — retry
                    reap = None
                    if attempt == MAX_ATTEMPTS - 1:
                        raise
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
                # include academic year display for modal/print
                'academic_year': ((reap.Academic_year.year.strftime('%Y') if getattr(reap.Academic_year, 'year', None) else '') + (f" ({reap.Academic_year.semester.sem_name})" if getattr(reap.Academic_year, 'semester', None) else "")) if getattr(reap, 'Academic_year', None) else '',
            }
            return redirect('reap_form')

        return render(request, 'peso_staff/reap_form.html', {'active_ay': active_ay, 'reap_types': reap_types})

    # GET
    # Pop recent_reap to show once if template uses it
    recent_reap = None
    if request.method != 'POST':
        recent_reap = request.session.pop('recent_reap', None)
    return render(request,'peso_staff/reap_form.html', {'recent_reap': recent_reap, 'active_ay': active_ay, 'reap_types': reap_types})

@login_required(login_url='/')
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
        # form field names updated: use `date_issued` / `date_issued_expiry` on the form,
        # but store them on the model's `date_claimed` / `date_claim_expiry` fields.
        date_issued = request.POST.get('date_issued')
        date_issued_expiry = request.POST.get('date_issued_expiry')

        # Normalize beneficiaries into a single string (one per line -> comma separated)
        # Trim whitespace and collapse empty lines
        names = [n.strip() for n in beneficiaries.splitlines() if n.strip()]
        name_of_beneficiary = ', '.join(names)[:255] if names else ''

        try:
            registration = Registration.objects.get(rfid=rfid)
        except Registration.DoesNotExist:
            messages.error(request, 'Registration not found for RFID.')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # Support follow-up: if a hidden `tupad_id` is provided, update that record
        # Handle this early so updates aren't blocked by the active_exists creation checks below.
        existing_tupad_id = request.POST.get('tupad_id') or request.POST.get('existing_tupad_id')
        if existing_tupad_id:
            try:
                tupad_obj = Peso_tupad.objects.get(pk=int(existing_tupad_id))
                # ensure the tupad belongs to the scanned registration
                if getattr(tupad_obj.registration, 'id', None) != registration.id:
                    messages.error(request, 'Referenced TUPAD does not belong to this registration.')
                    return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

                # parse dates for update
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

                # Resolve skill id/name similar to create flow
                skill_id = None
                skill_name = ''
                if skill_training_val:
                    sval = skill_training_val.strip()
                    try:
                        sid = int(sval)
                        if Skills_training.objects.filter(id=sid).exists():
                            skill_id = sid
                            skill_name = Skills_training.objects.filter(id=sid).values_list('Skills_name', flat=True).first() or ''
                        else:
                            skill_obj, _ = Skills_training.objects.get_or_create(Skills_name=sval)
                            skill_id = skill_obj.id
                            skill_name = skill_obj.Skills_name
                    except (ValueError, TypeError):
                        skill_obj, _ = Skills_training.objects.get_or_create(Skills_name=sval)
                        skill_id = skill_obj.id
                        skill_name = skill_obj.Skills_name

                # Update fields
                tupad_obj.name_of_beneficiary = name_of_beneficiary
                tupad_obj.skills_training_id = skill_id if skill_id else None
                tupad_obj.date_issued = date_issued_obj if date_issued_obj else None
                tupad_obj.date_issued_expiry = date_issued_expiry_obj if date_issued_expiry_obj else None
                try:
                    if request.user and request.user.is_authenticated:
                        tupad_obj.processed_by_id = request.user.id
                except Exception:
                    pass
                tupad_obj.save()
                messages.success(request, 'TUPAD updated successfully.')
                # update session payload for modal if needed
                request.session['recent_tupad'] = {
                    'id': tupad_obj.id,
                    'tracking_number': getattr(tupad_obj, 'tracking_number', ''),
                    'first_name': registration.first_name,
                    'last_name': registration.last_name,
                    'name_of_beneficiary': tupad_obj.name_of_beneficiary,
                    'skills_training': skill_name,
                    'date_issued': tupad_obj.date_issued.strftime('%Y-%m-%d') if getattr(tupad_obj, 'date_issued', None) else '',
                    'date_issued_expiry': tupad_obj.date_issued_expiry.strftime('%Y-%m-%d') if getattr(tupad_obj, 'date_issued_expiry', None) else '',
                }
                return redirect('tupad_form')
            except Peso_tupad.DoesNotExist:
                messages.error(request, 'Referenced TUPAD not found for update.')
                return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # Prevent creating another TUPAD when there is an active assistance:
        # - a TUPAD that is not yet released (is_released == False), OR
        # - a pending/approved TUPAD (status 1 or 2) whose expiry is null or not yet passed.
        today = date.today()
        active_exists = Peso_tupad.objects.filter(registration=registration).filter(
            Q(is_released=False) |
            (Q(status_id__in=[1, 2]) & (Q(date_issued_expiry__isnull=True) | Q(date_issued_expiry__gte=today)))
        ).exists()
        if active_exists:
            messages.error(request, 'Cannot save TUPAD: there is an existing active TUPAD (pending/approved or not released).')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # Validate required fields (date_issued_expiry and skill)
        if not date_issued_expiry:
            messages.error(request, 'Date claim expiry is required.')
            return render(request, 'peso_staff/tupad_form.html', {'skills': skills})

        # parse dates
        # parse provided issued dates into date objects (map to model fields)
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
        MAX_ATTEMPTS = 5
        try:
            for attempt in range(MAX_ATTEMPTS):
                try:
                    with transaction.atomic():
                        def _gen_tracking():
                            return f"PESO-T-{uuid.uuid4().hex[:10].upper()}"

                        tracking = _gen_tracking()
                        tupad = Peso_tupad.objects.create(
                            registration=registration,
                            tracking_number=tracking,
                            date_issued=date_issued_obj if date_issued_obj else None,
                            date_issued_expiry=date_issued_expiry_obj if date_issued_expiry_obj else None,
                            name_of_beneficiary=name_of_beneficiary,
                            skills_training_id=skill_id if skill_id else None,
                            processed_by_id=request.user.id if request.user and request.user.is_authenticated else None,
                        )
                    break
                except IntegrityError:
                    tupad = None
                    if attempt == MAX_ATTEMPTS - 1:
                        raise
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
                # store under the new "issued" keys for template convenience
                'date_issued': tupad.date_issued.strftime('%Y-%m-%d') if getattr(tupad, 'date_issued', None) else '',
                'date_issued_expiry': tupad.date_issued_expiry.strftime('%Y-%m-%d') if getattr(tupad, 'date_issued_expiry', None) else '',
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
@login_required(login_url='/')
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
            'civil_status': reg.civil_status_id,
            'civil_status_name': reg.civil_status.civil_status_name if reg.civil_status else '',
            'occupation': reg.occupation_id,
            'occupation_name': reg.occupation.occupation_name if reg.occupation else '',
            'email': reg.email,
            'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
        }

        # Return all previous REAP records as a list
        prev_qs = Peso_reap.objects.filter(registration=reg).order_by('-id')
        prev_list = []
        for prev in prev_qs:
            # Build academic year display using the single `year` DateField (show year only)
            ay_display = ''
            ay_year_str = ''
            ay_sem = ''
            if getattr(prev, 'Academic_year', None):
                ay_obj = prev.Academic_year
                if getattr(ay_obj, 'year', None):
                    try:
                        ay_year_str = ay_obj.year.strftime('%Y')
                    except Exception:
                        # fallback if year is stored as string
                        ay_year_str = str(ay_obj.year)
                ay_sem = ay_obj.semester.sem_name if getattr(ay_obj, 'semester', None) else ''
                ay_display = (ay_year_str + (f" ({ay_sem})" if ay_sem else ''))

            prev_list.append({
                'tracking_number': prev.tracking_number if hasattr(prev, 'tracking_number') else '',
                'rfid': reg.rfid,
                'first_name': reg.first_name,
                'last_name': reg.last_name,
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
                'civil_status_name': reg.civil_status.civil_status_name if reg.civil_status else '',
                'occupation_name': reg.occupation.occupation_name if reg.occupation else '',
                'email': reg.email,
                'profile_pic_url': reg.profile_pic.url if reg.profile_pic else '',
                'biodata': bool(prev.biodata),
                'certificate_of_reg': bool(prev.certificate_of_reg),
                'certificate_of_grades': bool(prev.certificate_of_grades),
                'official_receipt': bool(prev.official_receipt),
                'barangay_indigency': bool(prev.barangay_indigency),
                'barangay_recidency': bool(prev.barangay_recidency),
                'is_completed': bool(prev.is_completed) if hasattr(prev, 'is_completed') else (bool(prev.is_complete) if hasattr(prev, 'is_complete') else False),
                'reap_type_id': getattr(prev, 'reap_type_id', None) or getattr(prev, 'Reap_type_id', None),
                'reap_type_name': (prev.reap_type.type_name if getattr(prev, 'reap_type', None) and getattr(prev.reap_type, 'type_name', None) else (getattr(prev, 'reap_type', '') or '')),
                'date_added': prev.date_added.strftime('%Y-%m-%d') if getattr(prev, 'date_added', None) else '',
                'academic_year': ay_display,
                'academic_year_id': prev.Academic_year.id if getattr(prev, 'Academic_year', None) else None,
                'academic_year_start': ay_year_str,
                'academic_year_end': ay_year_str,
                'academic_year_semester': ay_sem,
                'id': prev.id,
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
                'next': bool(prev.next) if hasattr(prev, 'next') else False,
                'released_by_id': prev.released_by.id if getattr(prev, 'released_by', None) else None,
                'released_by_first_name': prev.released_by.first_name if getattr(prev, 'released_by', None) else '',
                'released_by_last_name': prev.released_by.last_name if getattr(prev, 'released_by', None) else '',
                'released_by_name': (f"{prev.released_by.first_name} {prev.released_by.last_name}".strip()) if getattr(prev, 'released_by', None) else '',
                'released_at': prev.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(prev, 'released_at', None) else '',
            })
        data['previous_reap_assistance'] = prev_list

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)



@login_required(login_url='/')
def REAP_RELEASE(request):
    return render(request, 'peso_staff/reap_release.html')

@require_POST
@login_required(login_url='/')
def RELEASE_REAP(request):
    """Handle REAP release POST: expects JSON {tracking: <tracking_number>} or {id: <reap_id>}.

    Marks Peso_reap.is_released = True for the matching record.
    Returns JSON success or error status.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    tracking = payload.get('tracking')
    reap_id = payload.get('id')

    if not tracking and not reap_id:
        # allow academic_year_id + rfid as alternative identifier
        academic_year_id = payload.get('academic_year_id')
        rfid = payload.get('rfid')
        if not (academic_year_id and rfid):
            return JsonResponse({'error': 'missing_identifier'}, status=400)

    reap = None
    try:
        if reap_id:
            reap = Peso_reap.objects.get(pk=reap_id)
        elif tracking:
            reap = Peso_reap.objects.get(tracking_number=tracking)
        else:
            # find by registration RFID + academic_year_id
            reg = Registration.objects.get(rfid=rfid)
            reap = Peso_reap.objects.get(registration=reg, Academic_year_id=academic_year_id)
    except (Peso_reap.DoesNotExist, Registration.DoesNotExist):
        return JsonResponse({'error': 'not_found'}, status=404)

    if getattr(reap, 'is_released', False):
        return JsonResponse({'error': 'already_released'}, status=400)
    # Do not allow releasing when the record is Pending (1) or Rejected (3)
    try:
        status_id = getattr(reap, 'status_id', None)
    except Exception:
        status_id = None
    if status_id in (1, 3):
        # Return a clearer message for clients indicating the record
        # is not releasable because it's either Pending (1) or Rejected (3).
        status_label = 'Pending' if status_id == 1 else ('Rejected' if status_id == 3 else 'Unknown')
        return JsonResponse({
            'error': 'cannot_release_status',
            'message': f'Record cannot be released because status is {status_label}.',
            'status_id': status_id,
        }, status=400)
    # Mark this REAP as released and update previous REAP records for the
    # same registration so they are flagged with `next = True`.
    try:
        with transaction.atomic():
            reap.is_released = True
            # Do not overwrite processed_by_id on release. Instead record who
            # released this REAP and when using `released_by` and `released_at`.
            try:
                if request.user and request.user.is_authenticated:
                    reap.released_by_id = request.user.id
                reap.released_at = timezone.now()
            except Exception:
                # If the model doesn't have these fields, skip silently but
                # continue with the release to avoid breaking the flow.
                pass
            reap.save()

            # Set `next = True` on previous REAPs for the same registration.
            # We consider "previous" as records with smaller primary key (id).
            try:
                Peso_reap.objects.filter(registration_id=reap.registration_id, id__lt=reap.id).update(next=True)
            except Exception:
                # Don't fail the release if updating the `next` flag fails;
                # log to console for debugging.
               
                logging.exception('Failed to update previous Peso_reap.next flags')
    except Exception:
        return JsonResponse({'error': 'db_error'}, status=500)

    # Return release metadata for client convenience
    released_by_id = reap.released_by.id if getattr(reap, 'released_by', None) else None
    released_by_first_name = reap.released_by.first_name if getattr(reap, 'released_by', None) else ''
    released_by_last_name = reap.released_by.last_name if getattr(reap, 'released_by', None) else ''
    released_by_name = (f"{released_by_first_name} {released_by_last_name}".strip()) if (released_by_first_name or released_by_last_name) else ''
    released_at = reap.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(reap, 'released_at', None) else ''

    return JsonResponse({
        'success': True,
        'released_by_id': released_by_id,
        'released_by_first_name': released_by_first_name,
        'released_by_last_name': released_by_last_name,
        'released_by_name': released_by_name,
        'released_at': released_at,
    })


@login_required(login_url='/')
def TUPAD_RELEASE(request):
    return render(request, 'peso_staff/tupad_release.html')


@require_GET
@csrf_exempt
@login_required(login_url='/')
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
            'civil_status': reg.civil_status_id,
            'civil_status_name': reg.civil_status.civil_status_name if reg.civil_status else '',
            'occupation': reg.occupation_id,
            'occupation_name': reg.occupation.occupation_name if reg.occupation else '',
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
                'date_issued': prev.date_issued.strftime('%Y-%m-%d') if getattr(prev, 'date_issued', None) else '',
                'date_issued_expiry': prev.date_issued_expiry.strftime('%Y-%m-%d') if getattr(prev, 'date_issued_expiry', None) else '',
                'is_released': bool(prev.is_released) if hasattr(prev, 'is_released') else False,
                'id': prev.id,
                'released_by_id': prev.released_by.id if getattr(prev, 'released_by', None) else None,
                'released_by_first_name': prev.released_by.first_name if getattr(prev, 'released_by', None) else '',
                'released_by_last_name': prev.released_by.last_name if getattr(prev, 'released_by', None) else '',
                'released_by_name': (f"{prev.released_by.first_name} {prev.released_by.last_name}".strip()) if getattr(prev, 'released_by', None) else '',
                'released_at': prev.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(prev, 'released_at', None) else '',
            })
        data['previous_tupad_assistance'] = prev_list

        return JsonResponse(data)
    except Registration.DoesNotExist:
        return JsonResponse({'error': 'Not found'}, status=404)


@require_POST
@login_required(login_url='/')
def RELEASE_TUPAD(request):
    """Handle TUPAD release POST: expects JSON {tracking: <tracking_number>} or {id: <tupad_id>}.

    Marks Peso_tupad.is_released = True for the matching record.
    Returns JSON success or error status.
    """
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        return JsonResponse({'error': 'invalid_json'}, status=400)

    tracking = payload.get('tracking')
    tupad_id = payload.get('id')

    if not tracking and not tupad_id:
        return JsonResponse({'error': 'missing_identifier'}, status=400)

    tupad = None
    try:
        if tupad_id:
            tupad = Peso_tupad.objects.get(pk=tupad_id)
        elif tracking:
            tupad = Peso_tupad.objects.get(tracking_number=tracking)
    except Peso_tupad.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)

    if getattr(tupad, 'is_released', False):
        return JsonResponse({'error': 'already_released'}, status=400)

    # Do not allow releasing when the record is Pending (1) or Rejected (3)
    try:
        status_id = getattr(tupad, 'status_id', None)
    except Exception:
        status_id = None
    if status_id in (1, 3):
        status_label = 'Pending' if status_id == 1 else ('Rejected' if status_id == 3 else 'Unknown')
        return JsonResponse({
            'error': 'cannot_release_status',
            'message': f'Record cannot be released because status is {status_label}.',
            'status_id': status_id,
        }, status=400)

    tupad.is_released = True
    # Similar to REAP: record who released the TUPAD and when, do not
    # overwrite `processed_by_id` at release time.
    try:
        if request.user and request.user.is_authenticated:
            tupad.released_by_id = request.user.id
        tupad.released_at = timezone.now()
    except Exception:
        pass
    tupad.save()
    # Return release metadata for client convenience
    released_by_id = tupad.released_by.id if getattr(tupad, 'released_by', None) else None
    released_by_first_name = tupad.released_by.first_name if getattr(tupad, 'released_by', None) else ''
    released_by_last_name = tupad.released_by.last_name if getattr(tupad, 'released_by', None) else ''
    released_by_name = (f"{released_by_first_name} {released_by_last_name}".strip()) if (released_by_first_name or released_by_last_name) else ''
    released_at = tupad.released_at.strftime('%Y-%m-%d %H:%M:%S') if getattr(tupad, 'released_at', None) else ''

    return JsonResponse({
        'success': True,
        'released_by_id': released_by_id,
        'released_by_first_name': released_by_first_name,
        'released_by_last_name': released_by_last_name,
        'released_by_name': released_by_name,
        'released_at': released_at,
    })

