from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from .decorators import role_required 

from django.contrib import messages
from django.utils import timezone
from .models import (
    Society, Flat, ResidentProfile, GuardProfile,
    Visitor, Complaint, Facility, FacilityBooking,
    MaintenanceDue, SocietyExpense, Notice, EmergencyAlert
)
from .forms import (
    ResidentAddForm, ResidentEditForm, FlatForm, ComplaintUpdateForm, NoticeForm,
    MaintenanceDueForm, SocietyExpenseForm, FacilityForm, VisitorForm,
    ComplaintForm, FacilityBookingForm, EmergencyAlertForm, OTPVerifyForm
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

def booking(request):
    return render(request, "society/admin/booking.html")
    
def create_razorpay_order(request):
    #razorpay auth
    client = razorpay.Client(auth=("rzp_test_Sabuhwd8z6gOZE", "Almc4BKCwgbIqx4TulnDtkfe"))
    payment = client.order.create({
        "amount": 10000,  #100rs
        "currency": "INR",
        "payment_capture": "1"
    })
    return JsonResponse(payment)

def verify_razorpay_payment(request):
    client = razorpay.Client(auth=("rzp_test_Sabuhwd8z6gOZE", "Almc4BKCwgbIqx4TulnDtkfe"))
    params = {
        "razorpay_order_id": request.POST.get("razorpay_order_id"),
        "razorpay_payment_id": request.POST.get("razorpay_payment_id"),
        "razorpay_signature": request.POST.get("razorpay_signature"),
    }
    try:
        client.utility.verify_payment_signature(params)
        return JsonResponse({"status": "success"})
        #payment --> 3 data store...
    except:
        return JsonResponse({"status": "error"})
    
    

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
    context = {
        'profile'          : profile,
        'my_complaints'    : Complaint.objects.filter(resident=profile).order_by('-created_at')[:5],
        'my_bookings'      : FacilityBooking.objects.filter(resident=profile).order_by('-created_at')[:5],
        'my_dues'          : MaintenanceDue.objects.filter(resident=profile, status='unpaid'),
        'recent_notices'   : Notice.objects.filter(is_active=True).order_by('-created_at')[:5],
        'pending_visitors' : Visitor.objects.filter(resident=profile, status='pending').order_by('-created_at'),
        'active_alerts'    : EmergencyAlert.objects.filter(is_resolved=False).order_by('-created_at')[:3],
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
            visitor.status = 'pending'
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
            booking.save()
            messages.success(request, f"{facility.name} booked successfully!")
            return redirect('resident_my_bookings')
    else:
        form = FacilityBookingForm()
    return render(request, "society/resident/book_facility.html", {'facility': facility, 'form': form})


@role_required(allowed_roles=["resident"])
def residentMyBookingsView(request):
    profile  = request.user.resident_profile
    bookings = FacilityBooking.objects.filter(resident=profile).order_by('-created_at')
    return render(request, "society/resident/my_bookings.html", {'bookings': bookings})


# ── Financial ──
@role_required(allowed_roles=["resident"])
def residentDuesView(request):
    profile = request.user.resident_profile
    dues    = MaintenanceDue.objects.filter(resident=profile).order_by('-created_at')
    return render(request, "society/resident/dues.html", {'dues': dues})


@role_required(allowed_roles=["resident"])
def residentPayDueView(request, pk):
    due         = get_object_or_404(MaintenanceDue, pk=pk, resident=request.user.resident_profile)
    due.status  = 'paid'
    due.paid_on = timezone.now()
    due.save()
    messages.success(request, f"Payment of ₹{due.amount} for {due.month} recorded!")
    return redirect('resident_dues')


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
        'pending_visitors' : Visitor.objects.filter(status='pending').order_by('-created_at'),
        'approved_visitors': Visitor.objects.filter(status='approved').order_by('-created_at')[:10],
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
def guardVerifyOTPView(request):
    visitor = None
    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                visitor            = Visitor.objects.get(otp=otp, status='approved')
                visitor.entry_time = timezone.now()
                visitor.save()
                messages.success(request, f"✅ Entry allowed for {visitor.name}!")
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