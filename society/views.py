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
from core.models import User
import random
import string


# # Create your views here.
# #@login_required(login_url="login")  #check in core.urls.py   ( login name should exist.....)
# @role_required(allowed_roles=["admin"])    #check in core.urls.py   ( login name should exist.....)
# def adminDashboardView(request):
#     return render(request,"society/admin/admin_dashboard.html")

# #@login_required(login_url="login")
# @role_required(allowed_roles=["resident"])    #check in core.urls.py   ( login name should exist.....)
# def residentDashBoard(request):
#     return render(request,"society/resident/resident_dashboard.html")

# #@login_required(login_url="login")
# @role_required(allowed_roles=["guard"])     #check in core.urls.py   ( login name should exist.....)
# def guardDashBoard(request):
#     return render(request,"society/guard/guard_dashboard.html") 






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
    flats     = Flat.objects.filter(status='vacant')
    societies = Society.objects.all()
    if request.method == "POST":
        email      = request.POST.get('email')
        password   = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name  = request.POST.get('last_name')
        mobile     = request.POST.get('mobile')
        flat_id    = request.POST.get('flat')
        society_id = request.POST.get('society')
        flat       = Flat.objects.get(id=flat_id)
        society    = Society.objects.get(id=society_id)
        user = User.objects.create_user(
            email=email, password=password,
            first_name=first_name, last_name=last_name,
            mobile=mobile, role='resident'
        )
        ResidentProfile.objects.create(user=user, flat=flat, society=society)
        flat.status = 'occupied'
        flat.save()
        messages.success(request, "Resident added successfully!")
        return redirect('admin_resident_list')
    return render(request, "society/admin/add_resident.html", {
        'flats': flats, 'societies': societies
    })


@role_required(allowed_roles=["admin"])
def adminDeleteResidentView(request, pk):
    resident = get_object_or_404(ResidentProfile, pk=pk)
    if resident.flat:
        resident.flat.status = 'vacant'
        resident.flat.save()
    resident.user.delete()
    messages.success(request, "Resident removed.")
    return redirect('admin_resident_list')


# ── Flat Management ──
@role_required(allowed_roles=["admin"])
def adminFlatListView(request):
    flats = Flat.objects.select_related('society').all()
    return render(request, "society/admin/flat_list.html", {'flats': flats})


@role_required(allowed_roles=["admin"])
def adminAddFlatView(request):
    societies = Society.objects.all()
    if request.method == "POST":
        flat_number = request.POST.get('flat_number')
        floor       = request.POST.get('floor')
        society_id  = request.POST.get('society')
        society     = Society.objects.get(id=society_id)
        Flat.objects.create(flat_number=flat_number, floor=floor, society=society)
        messages.success(request, f"Flat {flat_number} added!")
        return redirect('admin_flat_list')
    return render(request, "society/admin/add_flat.html", {'societies': societies})


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
        complaint.status = request.POST.get('status')
        complaint.remark = request.POST.get('remark')
        complaint.save()
        messages.success(request, "Complaint updated!")
        return redirect('admin_complaint_list')
    return render(request, "society/admin/complaint_detail.html", {'complaint': complaint})


# ── Notice Board ──
@role_required(allowed_roles=["admin"])
def adminNoticeListView(request):
    notices = Notice.objects.order_by('-created_at')
    return render(request, "society/admin/notice_list.html", {'notices': notices})


@role_required(allowed_roles=["admin"])
def adminAddNoticeView(request):
    societies = Society.objects.all()
    if request.method == "POST":
        society_id = request.POST.get('society')
        society    = Society.objects.get(id=society_id)
        Notice.objects.create(
            society     = society,
            posted_by   = request.user,
            title       = request.POST.get('title'),
            content     = request.POST.get('content'),
            notice_type = request.POST.get('notice_type'),
        )
        messages.success(request, "Notice posted!")
        return redirect('admin_notice_list')
    return render(request, "society/admin/add_notice.html", {'societies': societies})


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
    residents = ResidentProfile.objects.select_related('user', 'flat').all()
    if request.method == "POST":
        resident_id = request.POST.get('resident')
        resident    = get_object_or_404(ResidentProfile, pk=resident_id)
        MaintenanceDue.objects.create(
            resident = resident,
            month    = request.POST.get('month'),
            amount   = request.POST.get('amount'),
            due_date = request.POST.get('due_date'),
        )
        messages.success(request, "Due added!")
        return redirect('admin_financial')
    return render(request, "society/admin/add_due.html", {'residents': residents})


@role_required(allowed_roles=["admin"])
def adminAddExpenseView(request):
    societies = Society.objects.all()
    if request.method == "POST":
        society_id = request.POST.get('society')
        society    = Society.objects.get(id=society_id)
        SocietyExpense.objects.create(
            society     = society,
            title       = request.POST.get('title'),
            category    = request.POST.get('category'),
            amount      = request.POST.get('amount'),
            date        = request.POST.get('date'),
            description = request.POST.get('description'),
            added_by    = request.user,
        )
        messages.success(request, "Expense added!")
        return redirect('admin_financial')
    return render(request, "society/admin/add_expense.html", {'societies': societies})


# ── Facility Management ──
@role_required(allowed_roles=["admin"])
def adminFacilityListView(request):
    facilities = Facility.objects.all()
    return render(request, "society/admin/facility_list.html", {'facilities': facilities})


@role_required(allowed_roles=["admin"])
def adminAddFacilityView(request):
    societies = Society.objects.all()
    if request.method == "POST":
        society_id = request.POST.get('society')
        society    = Society.objects.get(id=society_id)
        Facility.objects.create(
            society     = society,
            name        = request.POST.get('name'),
            description = request.POST.get('description'),
            capacity    = request.POST.get('capacity'),
            price       = request.POST.get('price'),
        )
        messages.success(request, "Facility added!")
        return redirect('admin_facility_list')
    return render(request, "society/admin/add_facility.html", {'societies': societies})


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
    profile = request.user.resident_profile
    if request.method == "POST":
        Visitor.objects.create(
            resident       = profile,
            name           = request.POST.get('name'),
            mobile         = request.POST.get('mobile'),
            purpose        = request.POST.get('purpose'),
            vehicle_number = request.POST.get('vehicle_number'),
            otp            = generate_otp(),
            status         = 'pending',
        )
        messages.success(request, "Visitor added! Guard will be notified.")
        return redirect('resident_visitor_list')
    return render(request, "society/resident/add_visitor.html")


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
    profile = request.user.resident_profile
    if request.method == "POST":
        Complaint.objects.create(
            resident    = profile,
            title       = request.POST.get('title'),
            category    = request.POST.get('category'),
            description = request.POST.get('description'),
            image       = request.FILES.get('image'),
        )
        messages.success(request, "Complaint submitted!")
        return redirect('resident_complaint_list')
    return render(request, "society/resident/add_complaint.html")


# ── Facility Booking ──
@role_required(allowed_roles=["resident"])
def residentFacilityListView(request):
    facilities = Facility.objects.filter(is_active=True)
    return render(request, "society/resident/facility_list.html", {'facilities': facilities})


@role_required(allowed_roles=["resident"])
def residentBookFacilityView(request, facility_id):
    facility = get_object_or_404(Facility, pk=facility_id)
    profile  = request.user.resident_profile
    if request.method == "POST":
        date       = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time   = request.POST.get('end_time')
        conflict   = FacilityBooking.objects.filter(
            facility=facility, date=date,
            start_time=start_time, status='confirmed'
        ).exists()
        if conflict:
            messages.error(request, "This slot is already booked!")
            return redirect('resident_book_facility', facility_id=facility_id)
        FacilityBooking.objects.create(
            resident    = profile,
            facility    = facility,
            date        = date,
            start_time  = start_time,
            end_time    = end_time,
            amount_paid = facility.price,
        )
        messages.success(request, f"{facility.name} booked successfully!")
        return redirect('resident_my_bookings')
    return render(request, "society/resident/book_facility.html", {'facility': facility})


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
        society = Society.objects.first()
        EmergencyAlert.objects.create(
            society     = society,
            raised_by   = request.user,
            alert_type  = request.POST.get('alert_type'),
            description = request.POST.get('description'),
        )
        messages.error(request, "🚨 Emergency alert raised!")
        return redirect('resident_dashboard')
    return render(request, "society/resident/raise_alert.html")


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
        otp = request.POST.get('otp')
        try:
            visitor            = Visitor.objects.get(otp=otp, status='approved')
            visitor.entry_time = timezone.now()
            visitor.save()
            messages.success(request, f"✅ Entry allowed for {visitor.name}!")
        except Visitor.DoesNotExist:
            messages.error(request, "❌ Invalid or expired OTP!")
    return render(request, "society/guard/verify_otp.html", {'visitor': visitor})


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
        society = Society.objects.first()
        EmergencyAlert.objects.create(
            society     = society,
            raised_by   = request.user,
            alert_type  = request.POST.get('alert_type'),
            description = request.POST.get('description'),
        )
        messages.error(request, "🚨 Emergency alert raised!")
        return redirect('guard_dashboard')
    return render(request, "society/guard/raise_alert.html")