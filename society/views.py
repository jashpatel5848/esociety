from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from .decorators import role_required 

from django.contrib import messages
from django.utils import timezone
from .models import (
    Society, Flat, ResidentProfile, GuardProfile,
    Visitor, Complaint, Facility, FacilityBooking,
    MaintenanceDue, SocietyExpense, Notice, EmergencyAlert, Transaction
)
from .forms import (
    ResidentAddForm, ResidentEditForm, FlatForm, ComplaintUpdateForm, NoticeForm,
    MaintenanceDueForm, SocietyExpenseForm, FacilityForm, VisitorForm,
    ComplaintForm, FacilityBookingForm, EmergencyAlertForm, OTPVerifyForm,
    GuardVisitorForm,
    GuardAddForm, GuardEditForm, FlatEditForm, FacilityEditForm,
    NoticeEditForm, DueEditForm, ExpenseEditForm
)
from core.models import User
import random
import string

import razorpay
from django.conf import settings
from django.http import JsonResponse



# ══════════════════════════════════════════
# payment
# ══════════════════════════════════════════

from django.views.decorators.csrf import csrf_exempt

def create_razorpay_order(request):
    # razorpay auth
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment = client.order.create({
        "amount": 10000,  # 100rs
        "currency": "INR",
        "payment_capture": 1
    })
    return JsonResponse(payment)

@csrf_exempt
def verify_razorpay_payment(request):
    import json
    # Try to get data from POST or JSON body
    data = {}
    if request.method == "POST":
        data = request.POST
        if not data:
            try:
                data = json.loads(request.body)
            except:
                data = {}
    else:
        return JsonResponse({"status": "error", "message": "Invalid request method"})

    params = {
        "razorpay_order_id": data.get("razorpay_order_id"),
        "razorpay_payment_id": data.get("razorpay_payment_id"),
        "razorpay_signature": data.get("razorpay_signature"),
    }

    if not all(params.values()):
        return JsonResponse({"status": "error", "message": f"Missing parameters: {[k for k,v in params.items() if not v]}"})

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    
    try:
        client.utility.verify_payment_signature(params)
        
        # Update Transaction record
        tx = Transaction.objects.get(order_id=params["razorpay_order_id"])
        tx.payment_id = params["razorpay_payment_id"]
        tx.status = 'success'
        tx.save()
        
        # Update linked Due
        if tx.due:
            tx.due.status = 'paid'
            tx.due.paid_on = timezone.now()
            tx.due.save()

        # Update linked Booking
        if tx.booking:
            tx.booking.status = 'confirmed'
            tx.booking.save()
            
        return JsonResponse({"status": "success"})
    except razorpay.errors.SignatureVerificationError as e:
        return JsonResponse({"status": "error", "message": "Invalid payment signature."})
    except Transaction.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Transaction record not found."})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})
    
    

# ══════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))


# ══════════════════════════════════════════
# ADMIN VIEWS
# ══════════════════════════════════════════

@role_required(allowed_roles=["admin"])
def adminDashboardView(request):
    # Auto-synchronize Flat statuses to guarantee accurate Vacant counts
    Flat.objects.filter(residents__isnull=True).update(status='vacant')
    Flat.objects.filter(residents__isnull=False).update(status='occupied')

    context = {
        'total_residents'  : ResidentProfile.objects.count(),
        'total_flats'      : Flat.objects.count(),
        'vacant_flats'     : Flat.objects.filter(status='vacant').count(),
        'open_complaints'  : Complaint.objects.filter(status='open').count(),
        'pending_dues'     : MaintenanceDue.objects.filter(status='unpaid').count(),
        'total_visitors'   : Visitor.objects.filter(status='approved').count(),
        'recent_complaints': Complaint.objects.order_by('-created_at')[:5],
        'recent_notices'   : Notice.objects.filter(is_active=True).order_by('-created_at')[:5],
        'recent_alerts'    : EmergencyAlert.objects.filter(is_resolved=False).order_by('-created_at')[:3],
    }
    return render(request, "society/admin/admin_dashboard.html", context)


# ── Resident Management ──
@role_required(allowed_roles=["admin"])
def adminResidentListView(request):
    residents = ResidentProfile.objects.select_related('user', 'flat', 'society').all()
    return render(request, "society/admin/resident_list.html", {'residents': residents})


@role_required(allowed_roles=["admin"])
def adminAddResidentView(request):
    if request.method == "POST":
        form = ResidentAddForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'], 
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'], 
                last_name=form.cleaned_data['last_name'],
                mobile=form.cleaned_data['mobile'], 
                role='resident'
            )
            flat = form.cleaned_data['flat']
            society = form.cleaned_data['society']
            ResidentProfile.objects.create(user=user, flat=flat, society=society)
            flat.status = 'occupied'
            flat.save()
            messages.success(request, "Resident added successfully!")
            return redirect('admin_resident_list')
    else:
        form = ResidentAddForm()
    return render(request, "society/admin/add_resident.html", {'form': form})


@role_required(allowed_roles=["admin"])
def adminDeleteResidentView(request, pk):
    resident = get_object_or_404(ResidentProfile, pk=pk)
    if resident.flat:
        resident.flat.status = 'vacant'
        resident.flat.save()
    resident.user.delete()
    messages.success(request, "Resident removed.")
    return redirect('admin_resident_list')

@role_required(allowed_roles=["admin"])
def adminEditResidentView(request, pk):
    resident = get_object_or_404(ResidentProfile, pk=pk)
    if request.method == "POST":
        form = ResidentEditForm(request.POST, instance=resident)
        if form.is_valid():
            old_resident = ResidentProfile.objects.get(pk=resident.pk)
            if old_resident.flat:
                old_flat = old_resident.flat
                old_flat.status = 'vacant'
                old_flat.save()
            new_flat = form.cleaned_data['flat']
            form.save()
            new_flat.status = 'occupied'
            new_flat.save()
            messages.success(request, f"Flat assigned!")
            return redirect('admin_resident_list')
    else:
        form = ResidentEditForm(instance=resident)
    return render(request, "society/admin/edit_resident.html", {
        'resident': resident,
        'form': form,
    })


# ── Flat Management ──
@role_required(allowed_roles=["admin"])
def adminFlatListView(request):
    # Auto-synchronize Flat statuses to guarantee accurate Vacant counts
    Flat.objects.filter(residents__isnull=True).update(status='vacant')
    Flat.objects.filter(residents__isnull=False).update(status='occupied')
    
    flats = Flat.objects.select_related('society').all()
    return render(request, "society/admin/flat_list.html", {'flats': flats})


@role_required(allowed_roles=["admin"])
def adminAddFlatView(request):
    if request.method == "POST":
        form = FlatForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Flat added!")
            return redirect('admin_flat_list')
    else:
        form = FlatForm()
    return render(request, "society/admin/add_flat.html", {'form': form})


# ── Complaint Management ──
@role_required(allowed_roles=["admin"])
def adminComplaintListView(request):
    status_filter = request.GET.get('status', '')
    complaints    = Complaint.objects.select_related('resident__user', 'resident__flat').order_by('-created_at')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    return render(request, "society/admin/complaint_list.html", {
        'complaints'   : complaints,
        'status_filter': status_filter,
    })


@role_required(allowed_roles=["admin"])
def adminComplaintUpdateView(request, pk):
    complaint = get_object_or_404(Complaint, pk=pk)
    if request.method == "POST":
        form = ComplaintUpdateForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, "Complaint updated!")
            return redirect('admin_complaint_list')
    else:
        form = ComplaintUpdateForm(instance=complaint)
    return render(request, "society/admin/complaint_detail.html", {'complaint': complaint, 'form': form})


# ── Notice Board ──
@role_required(allowed_roles=["admin"])
def adminNoticeListView(request):
    notices = Notice.objects.order_by('-created_at')
    return render(request, "society/admin/notice_list.html", {'notices': notices})


@role_required(allowed_roles=["admin"])
def adminAddNoticeView(request):
    if request.method == "POST":
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.posted_by = request.user
            notice.save()
            messages.success(request, "Notice posted!")
            return redirect('admin_notice_list')
    else:
        form = NoticeForm()
    return render(request, "society/admin/add_notice.html", {'form': form})


@role_required(allowed_roles=["admin"])
def adminDeleteNoticeView(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    notice.delete()
    messages.success(request, "Notice deleted.")
    return redirect('admin_notice_list')


# ── Financial Management ──
@role_required(allowed_roles=["admin"])
def adminFinancialView(request):
    dues     = MaintenanceDue.objects.select_related('resident__user', 'resident__flat').order_by('-created_at')
    expenses = SocietyExpense.objects.order_by('-date')
    total_collected = sum(d.amount for d in dues.filter(status='paid'))
    total_pending   = sum(d.amount for d in dues.filter(status='unpaid'))
    total_expenses  = sum(e.amount for e in expenses)
    context = {
        'dues'           : dues,
        'expenses'       : expenses,
        'total_collected': total_collected,
        'total_pending'  : total_pending,
        'total_expenses' : total_expenses,
        'balance'        : total_collected - total_expenses,
    }
    return render(request, "society/admin/financial.html", context)


@role_required(allowed_roles=["admin"])
def adminAddDueView(request):
    if request.method == "POST":
        form = MaintenanceDueForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Due added!")
            return redirect('admin_financial')
    else:
        form = MaintenanceDueForm()
    return render(request, "society/admin/add_due.html", {'form': form})


@role_required(allowed_roles=["admin"])
def adminAddExpenseView(request):
    if request.method == "POST":
        form = SocietyExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.added_by = request.user
            expense.save()
            messages.success(request, "Expense added!")
            return redirect('admin_financial')
    else:
        form = SocietyExpenseForm()
    return render(request, "society/admin/add_expense.html", {'form': form})


# ── Facility Management ──
@role_required(allowed_roles=["admin"])
def adminFacilityListView(request):
    facilities = Facility.objects.all()
    return render(request, "society/admin/facility_list.html", {'facilities': facilities})


@role_required(allowed_roles=["admin"])
def adminAddFacilityView(request):
    if request.method == "POST":
        form = FacilityForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Facility added!")
            return redirect('admin_facility_list')
    else:
        form = FacilityForm()
    return render(request, "society/admin/add_facility.html", {'form': form})


@role_required(allowed_roles=["admin"])
def adminFacilityBookingListView(request):
    bookings = FacilityBooking.objects.select_related('resident__user', 'facility').order_by('-created_at')
    return render(request, "society/admin/booking_list.html", {'bookings': bookings})


@role_required(allowed_roles=["admin"])
def adminUpdateBookingStatusView(request, pk, action):
    booking = get_object_or_404(FacilityBooking, pk=pk)
    if action == 'approve':
        booking.status = 'confirmed'
        messages.success(request, f"Booking for {booking.facility.name} confirmed!")
    elif action == 'reject':
        booking.status = 'cancelled'
        messages.warning(request, f"Booking for {booking.facility.name} rejected.")
    booking.save()
    return redirect('admin_facility_booking_list')


# ── Emergency Alerts ──
@role_required(allowed_roles=["admin"])
def adminAlertListView(request):
    alerts = EmergencyAlert.objects.order_by('-created_at')
    return render(request, "society/admin/alert_list.html", {'alerts': alerts})


@role_required(allowed_roles=["admin"])
def adminResolveAlertView(request, pk):
    alert             = get_object_or_404(EmergencyAlert, pk=pk)
    alert.is_resolved = True
    alert.resolved_at = timezone.now()
    alert.save()
    messages.success(request, "Alert marked as resolved.")
    return redirect('admin_alert_list')


# ── Visitor List (Admin) ──
@role_required(allowed_roles=["admin"])
def adminVisitorListView(request):
    visitors = Visitor.objects.select_related('resident__user', 'resident__flat').order_by('-created_at')
    return render(request, "society/admin/visitor_list.html", {'visitors': visitors})


# ── Flat Edit / Delete ──
@role_required(allowed_roles=["admin"])
def adminEditFlatView(request, pk):
    flat = get_object_or_404(Flat, pk=pk)
    if request.method == "POST":
        form = FlatEditForm(request.POST, instance=flat)
        if form.is_valid():
            form.save()
            messages.success(request, "Flat updated!")
            return redirect('admin_flat_list')
    else:
        form = FlatEditForm(instance=flat)
    return render(request, "society/admin/edit_flat.html", {'form': form, 'flat': flat})


@role_required(allowed_roles=["admin"])
def adminDeleteFlatView(request, pk):
    flat = get_object_or_404(Flat, pk=pk)
    flat.delete()
    messages.success(request, "Flat deleted.")
    return redirect('admin_flat_list')


# ── Facility Edit / Delete ──
@role_required(allowed_roles=["admin"])
def adminEditFacilityView(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == "POST":
        form = FacilityEditForm(request.POST, instance=facility)
        if form.is_valid():
            form.save()
            messages.success(request, "Facility updated!")
            return redirect('admin_facility_list')
    else:
        form = FacilityEditForm(instance=facility)
    return render(request, "society/admin/edit_facility.html", {'form': form, 'facility': facility})


@role_required(allowed_roles=["admin"])
def adminDeleteFacilityView(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    facility.delete()
    messages.success(request, "Facility deleted.")
    return redirect('admin_facility_list')


# ── Notice Edit ──
@role_required(allowed_roles=["admin"])
def adminEditNoticeView(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if request.method == "POST":
        form = NoticeEditForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated!")
            return redirect('admin_notice_list')
    else:
        form = NoticeEditForm(instance=notice)
    return render(request, "society/admin/edit_notice.html", {'form': form, 'notice': notice})


# ── Guard Management ──
@role_required(allowed_roles=["admin"])
def adminGuardListView(request):
    guards = GuardProfile.objects.select_related('user', 'society').all()
    return render(request, "society/admin/guard_list.html", {'guards': guards})


@role_required(allowed_roles=["admin"])
def adminAddGuardView(request):
    if request.method == "POST":
        form = GuardAddForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                mobile=form.cleaned_data['mobile'],
                role='guard',
                status='active',
                is_active=True,
            )
            GuardProfile.objects.create(
                user=user,
                society=form.cleaned_data['society'],
                shift=form.cleaned_data['shift'],
            )
            messages.success(request, "Guard added successfully!")
            return redirect('admin_guard_list')
    else:
        form = GuardAddForm()
    return render(request, "society/admin/add_guard.html", {'form': form})


@role_required(allowed_roles=["admin"])
def adminEditGuardView(request, pk):
    guard = get_object_or_404(GuardProfile, pk=pk)
    if request.method == "POST":
        form = GuardEditForm(request.POST, instance=guard)
        if form.is_valid():
            form.save()
            messages.success(request, "Guard shift updated!")
            return redirect('admin_guard_list')
    else:
        form = GuardEditForm(instance=guard)
    return render(request, "society/admin/edit_guard.html", {'form': form, 'guard': guard})


@role_required(allowed_roles=["admin"])
def adminDeleteGuardView(request, pk):
    guard = get_object_or_404(GuardProfile, pk=pk)
    guard.user.delete()
    messages.success(request, "Guard removed.")
    return redirect('admin_guard_list')


# ── Due Edit / Delete ──
@role_required(allowed_roles=["admin"])
def adminEditDueView(request, pk):
    due = get_object_or_404(MaintenanceDue, pk=pk)
    if request.method == "POST":
        form = DueEditForm(request.POST, instance=due)
        if form.is_valid():
            form.save()
            messages.success(request, "Due updated!")
            return redirect('admin_financial')
    else:
        form = DueEditForm(instance=due)
    return render(request, "society/admin/edit_due.html", {'form': form, 'due': due})


@role_required(allowed_roles=["admin"])
def adminDeleteDueView(request, pk):
    due = get_object_or_404(MaintenanceDue, pk=pk)
    due.delete()
    messages.success(request, "Due deleted.")
    return redirect('admin_financial')


# ── Expense Edit / Delete ──
@role_required(allowed_roles=["admin"])
def adminEditExpenseView(request, pk):
    expense = get_object_or_404(SocietyExpense, pk=pk)
    if request.method == "POST":
        form = ExpenseEditForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense updated!")
            return redirect('admin_financial')
    else:
        form = ExpenseEditForm(instance=expense)
    return render(request, "society/admin/edit_expense.html", {'form': form, 'expense': expense})


@role_required(allowed_roles=["admin"])
def adminDeleteExpenseView(request, pk):
    expense = get_object_or_404(SocietyExpense, pk=pk)
    expense.delete()
    messages.success(request, "Expense deleted.")
    return redirect('admin_financial')


# ══════════════════════════════════════════
# RESIDENT VIEWS
# ══════════════════════════════════════════


@role_required(allowed_roles=["resident"])
def residentDashBoard(request):
    try:
        profile = request.user.resident_profile
    except:
        return render(request, "society/resident/resident_dashboard.html", {
            'profile'         : None,
            'my_complaints'   : [],
            'my_bookings'     : [],
            'my_dues'         : [],
            'recent_notices'  : [],
            'pending_visitors': [],
            'active_alerts'   : [],
        })
    all_pending = Visitor.objects.filter(resident=profile, status='pending').order_by('-created_at')
    
    # Visitors added by Guard (Need resident approval)
    approval_requests = [v for v in all_pending if v.approved_by == 'guard']
    
    # Visitors pre-approved by Resident (Waiting at gate)
    expected_visitors = [v for v in all_pending if v.approved_by == 'resident']

    context = {
        'profile'          : profile,
        'my_complaints'    : Complaint.objects.filter(resident=profile).order_by('-created_at')[:5],
        'my_bookings'      : FacilityBooking.objects.filter(resident=profile).order_by('-created_at')[:5],
        'my_dues'          : MaintenanceDue.objects.filter(resident=profile, status='unpaid'),
        'recent_notices'   : Notice.objects.filter(is_active=True).order_by('-created_at')[:5],
        'approval_requests': approval_requests,
        'expected_visitors': expected_visitors,
        'active_alerts'    : EmergencyAlert.objects.filter(is_resolved=False).order_by('-created_at')[:3],
        'recent_entries'   : Visitor.objects.filter(resident=profile, entry_time__isnull=False).order_by('-entry_time')[:5],
    }
    return render(request, "society/resident/resident_dashboard.html", context)


# ── Visitor Management ──
@role_required(allowed_roles=["resident"])
def residentVisitorListView(request):
    profile  = request.user.resident_profile
    visitors = Visitor.objects.filter(resident=profile).order_by('-created_at')
    return render(request, "society/resident/visitor_list.html", {'visitors': visitors})


@role_required(allowed_roles=["resident"])
def residentAddVisitorView(request):
    if request.method == "POST":
        form = VisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            visitor.resident = request.user.resident_profile
            visitor.otp = generate_otp()
            visitor.status = 'pending' # Waiting for gate entry
            visitor.approved_by = 'resident' # Pre-authorized by resident
            visitor.save()
            messages.success(request, "Visitor added! Guard will be notified.")
            return redirect('resident_visitor_list')
    else:
        form = VisitorForm()
    return render(request, "society/resident/add_visitor.html", {'form': form})


@role_required(allowed_roles=["resident"])
def residentApproveVisitorView(request, pk):
    visitor        = get_object_or_404(Visitor, pk=pk, resident=request.user.resident_profile)
    visitor.status = 'approved'
    visitor.approved_by = 'resident'
    visitor.save()
    messages.success(request, f"{visitor.name} approved!")
    return redirect('resident_visitor_list')


@role_required(allowed_roles=["resident"])
def residentDenyVisitorView(request, pk):
    visitor        = get_object_or_404(Visitor, pk=pk, resident=request.user.resident_profile)
    visitor.status = 'denied'
    visitor.save()
    messages.warning(request, f"{visitor.name} denied.")
    return redirect('resident_visitor_list')


# ── Complaint ──
@role_required(allowed_roles=["resident"])
def residentComplaintListView(request):
    profile    = request.user.resident_profile
    complaints = Complaint.objects.filter(resident=profile).order_by('-created_at')
    return render(request, "society/resident/complaint_list.html", {'complaints': complaints})


@role_required(allowed_roles=["resident"])
def residentAddComplaintView(request):
    if request.method == "POST":
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.resident = request.user.resident_profile
            complaint.save()
            messages.success(request, "Complaint submitted!")
            return redirect('resident_complaint_list')
    else:
        form = ComplaintForm()
    return render(request, "society/resident/add_complaint.html", {'form': form})


# ── Facility Booking ──
@role_required(allowed_roles=["resident"])
def residentFacilityListView(request):
    facilities = Facility.objects.filter(is_active=True)
    return render(request, "society/resident/facility_list.html", {'facilities': facilities})


@role_required(allowed_roles=["resident"])
def residentBookFacilityView(request, facility_id):
    facility = get_object_or_404(Facility, pk=facility_id)
    if request.method == "POST":
        form = FacilityBookingForm(request.POST)
        if form.is_valid():
            date       = form.cleaned_data['date']
            start_time = form.cleaned_data['start_time']
            end_time   = form.cleaned_data['end_time']
            conflict   = FacilityBooking.objects.filter(
                facility=facility, date=date,
                start_time=start_time, status='confirmed'
            ).exists()
            if conflict:
                messages.error(request, "This slot is already booked!")
                return redirect('resident_book_facility', facility_id=facility_id)
            booking = form.save(commit=False)
            booking.resident = request.user.resident_profile
            booking.facility = facility
            booking.amount_paid = facility.price
            
            # All paid facility bookings start as pending
            if facility.price > 0:
                booking.status = 'pending'
            else:
                booking.status = 'confirmed'
                
            booking.save()
            messages.success(request, f"{facility.name} booking request submitted!")
            return redirect('resident_my_bookings')
    else:
        form = FacilityBookingForm()
    return render(request, "society/resident/book_facility.html", {'facility': facility, 'form': form})

@csrf_exempt
@role_required(allowed_roles=["resident"])
def residentPayBookingView(request, pk):
    try:
        resident_profile = getattr(request.user, 'resident_profile', None)
        if not resident_profile:
            return JsonResponse({"status": "error", "message": "Resident profile not found"})
            
        booking = get_object_or_404(FacilityBooking, pk=pk, resident=resident_profile)
    
        if booking.status == 'confirmed':
            return JsonResponse({"status": "error", "message": "Already confirmed"})

        # 1. Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # 2. Create Order (Amount in paise)
        amount_paise = int(booking.amount_paid * 100)
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        }
        razorpay_order = client.order.create(data=order_data)
        
        # 3. Save Transaction
        Transaction.objects.get_or_create(
            order_id=razorpay_order['id'],
            defaults={
                'resident': request.user.resident_profile,
                'booking': booking,
                'amount': booking.amount_paid,
                'status': 'pending'
            }
        )
        
        # 4. Return order details + keys for frontend
        response_data = {
            "status": "success",
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": razorpay_order['id'],
            "amount": amount_paise,
            "currency": "INR",
            "org_name": "e-Society",
            "description": f"Booking for {booking.facility.name}",
            "user_name": f"{request.user.first_name} {request.user.last_name}",
            "user_email": request.user.email,
            "user_mobile": str(request.user.mobile) if request.user.mobile else "9999999999",
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


@role_required(allowed_roles=["resident"])
def residentMyBookingsView(request):
    profile  = request.user.resident_profile
    bookings = FacilityBooking.objects.filter(resident=profile).order_by('-created_at')
    # Fetch history
    history = Transaction.objects.filter(resident=profile, booking__isnull=False, status='success').order_by('-created_at')
    return render(request, "society/resident/my_bookings.html", {'bookings': bookings, 'history': history})


# ── Financial ──
@role_required(allowed_roles=["resident"])
def residentDuesView(request):
    profile = request.user.resident_profile
    dues    = MaintenanceDue.objects.filter(resident=profile).order_by('-created_at')
    # Fetch history
    history = Transaction.objects.filter(resident=profile, due__isnull=False, status='success').order_by('-created_at')
    return render(request, "society/resident/dues.html", {'dues': dues, 'history': history})

@csrf_exempt
@role_required(allowed_roles=["resident"])
def residentPayDueView(request, pk):
    try:
        resident_profile = getattr(request.user, 'resident_profile', None)
        if not resident_profile:
            return JsonResponse({"status": "error", "message": "Resident profile not found"})
            
        due = get_object_or_404(MaintenanceDue, pk=pk, resident=resident_profile)
    
        if due.status == 'paid':
            return JsonResponse({"status": "error", "message": "Already paid"})

        # 1. Initialize Razorpay Client
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # 2. Create Order (Amount in paise)
        amount_paise = int(due.amount * 100)
        order_data = {
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        }
        razorpay_order = client.order.create(data=order_data)
        
        # 3. Save Transaction
        Transaction.objects.get_or_create(
            order_id=razorpay_order['id'],
            defaults={
                'resident': request.user.resident_profile,
                'due': due,
                'amount': due.amount,
                'status': 'pending'
            }
        )
        
        # 4. Return order details + keys for frontend
        response_data = {
            "status": "success",
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": razorpay_order['id'],
            "amount": amount_paise,
            "currency": "INR",
            "org_name": "e-Society",
            "description": f"Maintenance for {due.month}",
            "user_name": f"{request.user.first_name} {request.user.last_name}",
            "user_email": request.user.email,
            "user_mobile": str(request.user.mobile) if request.user.mobile else "9999999999",
        }
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})



# ── Notice ──
@role_required(allowed_roles=["resident"])
def residentNoticeListView(request):
    notices = Notice.objects.filter(is_active=True).order_by('-created_at')
    return render(request, "society/resident/notice_list.html", {'notices': notices})


# ── Emergency Alert ──
@role_required(allowed_roles=["resident"])
def residentRaiseAlertView(request):
    if request.method == "POST":
        form = EmergencyAlertForm(request.POST)
        if form.is_valid():
            society = Society.objects.first()
            alert = form.save(commit=False)
            alert.society = society
            alert.raised_by = request.user
            alert.save()
            messages.error(request, "🚨 Emergency alert raised!")
            return redirect('resident_dashboard')
    else:
        form = EmergencyAlertForm()
    return render(request, "society/resident/raise_alert.html", {'form': form})


# ══════════════════════════════════════════
# GUARD VIEWS
# ══════════════════════════════════════════

@role_required(allowed_roles=["guard"])
def guardDashBoard(request):
    context = {
        'pending_visitors' : Visitor.objects.filter(status__in=['pending', 'approved'], entry_time__isnull=True).order_by('-created_at'),
        'approved_visitors': Visitor.objects.filter(status='approved', entry_time__isnull=False).order_by('-created_at')[:10],
        'active_alerts'    : EmergencyAlert.objects.filter(is_resolved=False).order_by('-created_at'),
        'todays_visitors'  : Visitor.objects.filter(
            entry_time__date=timezone.now().date()
        ).count(),
    }
    return render(request, "society/guard/guard_dashboard.html", context)


@role_required(allowed_roles=["guard"])
def guardVisitorListView(request):
    visitors = Visitor.objects.select_related('resident__flat').order_by('-created_at')
    return render(request, "society/guard/visitor_list.html", {'visitors': visitors})


@role_required(allowed_roles=["guard"])
def guardApproveEntryView(request, pk):
    visitor = get_object_or_404(Visitor, pk=pk)
    visitor.status = 'approved'
    visitor.approved_by = 'guard'
    visitor.entry_time = timezone.now()
    visitor.save()
    messages.success(request, f"Entry authorized by Guard for {visitor.name}.")
    return redirect('guard_dashboard')


@role_required(allowed_roles=["guard"])
def guardAddVisitorView(request):
    if request.method == "POST":
        form = GuardVisitorForm(request.POST)
        if form.is_valid():
            visitor = form.save(commit=False)
            # No OTP needed for gate entry initiated by guard, but we'll set one for consistency
            visitor.otp = generate_otp()
            visitor.status = 'pending' # Requires resident approval
            visitor.save()
            messages.success(request, f"Entry request sent for {visitor.name}. Awaiting resident approval.")
            return redirect('guard_dashboard')
    else:
        form = GuardVisitorForm()
    return render(request, "society/guard/add_visitor.html", {'form': form})


@role_required(allowed_roles=["guard"])
def guardVerifyOTPView(request):
    visitor = None
    # Support quick-allow from dashboard
    otp_from_get = request.GET.get('otp')
    if otp_from_get:
        try:
            # We look for pending visitors pre-authorized by residents
            visitor = Visitor.objects.get(otp=otp_from_get, status='pending', approved_by='resident')
            visitor.entry_time = timezone.now()
            visitor.status = 'approved' # Entry granted
            visitor.save()
            messages.success(request, f"✅ Entry allowed for {visitor.name}!")
            return redirect('guard_dashboard')
        except Visitor.DoesNotExist:
            messages.error(request, "❌ Invalid or already entered!")
            return redirect('guard_dashboard')

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                visitor            = Visitor.objects.get(otp=otp, status='pending', approved_by='resident')
                visitor.entry_time = timezone.now()
                visitor.status = 'approved' # Entry granted
                visitor.save()
                messages.success(request, f"✅ Entry allowed for {visitor.name}!")
                return redirect('guard_dashboard')
            except Visitor.DoesNotExist:
                messages.error(request, "❌ Invalid or expired OTP!")
    else:
        form = OTPVerifyForm()
    return render(request, "society/guard/verify_otp.html", {'visitor': visitor, 'form': form})


@role_required(allowed_roles=["guard"])
def guardMarkExitView(request, pk):
    visitor           = get_object_or_404(Visitor, pk=pk)
    visitor.exit_time = timezone.now()
    visitor.status    = 'exited'
    visitor.save()
    messages.success(request, f"{visitor.name} marked as exited.")
    return redirect('guard_visitor_list')


@role_required(allowed_roles=["guard"])
def guardRaiseAlertView(request):
    if request.method == "POST":
        form = EmergencyAlertForm(request.POST)
        if form.is_valid():
            society = Society.objects.first()
            alert = form.save(commit=False)
            alert.society = society
            alert.raised_by = request.user
            alert.save()
            messages.error(request, "🚨 Emergency alert raised!")
            return redirect('guard_dashboard')
    else:
        form = EmergencyAlertForm()
    return render(request, "society/guard/raise_alert.html", {'form': form})