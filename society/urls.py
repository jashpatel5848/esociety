from django.urls import path
from . import views

urlpatterns = [
    path("admin/",views.adminDashboardView,name="admin_dashboard"),
    path("resident/",views.residentDashBoard,name="resident_dashboard"),
    path("guard/",views.guardDashBoard,name="guard_dashboard"),

    # ── ADMIN  ──
    path("admin/residents/", views.adminResidentListView, name="admin_resident_list"),
    path("admin/residents/add/", views.adminAddResidentView, name="admin_add_resident"),
    path("admin/residents/delete/<int:pk>/", views.adminDeleteResidentView, name="admin_delete_resident"),
    path("admin/residents/edit/<int:pk>/", views.adminEditResidentView, name="admin_edit_resident"),
    path("admin/flats/", views.adminFlatListView, name="admin_flat_list"),
    path("admin/flats/add/", views.adminAddFlatView, name="admin_add_flat"),
    path("admin/flats/edit/<int:pk>/", views.adminEditFlatView, name="admin_edit_flat"),
    path("admin/flats/delete/<int:pk>/", views.adminDeleteFlatView, name="admin_delete_flat"),
    path("admin/complaints/", views.adminComplaintListView, name="admin_complaint_list"),
    path("admin/complaints/<int:pk>/", views.adminComplaintUpdateView, name="admin_complaint_update"),
    path("admin/notices/", views.adminNoticeListView, name="admin_notice_list"),
    path("admin/notices/add/", views.adminAddNoticeView, name="admin_add_notice"),
    path("admin/notices/edit/<int:pk>/", views.adminEditNoticeView, name="admin_edit_notice"),
    path("admin/notices/delete/<int:pk>/", views.adminDeleteNoticeView, name="admin_delete_notice"),
    path("admin/financial/", views.adminFinancialView, name="admin_financial"),
    path("admin/financial/due/add/", views.adminAddDueView, name="admin_add_due"),
    path("admin/financial/due/edit/<int:pk>/", views.adminEditDueView, name="admin_edit_due"),
    path("admin/financial/due/delete/<int:pk>/", views.adminDeleteDueView, name="admin_delete_due"),
    path("admin/financial/expense/add/", views.adminAddExpenseView, name="admin_add_expense"),
    path("admin/financial/expense/edit/<int:pk>/", views.adminEditExpenseView, name="admin_edit_expense"),
    path("admin/financial/expense/delete/<int:pk>/", views.adminDeleteExpenseView, name="admin_delete_expense"),
    path("admin/facilities/", views.adminFacilityListView, name="admin_facility_list"),
    path("admin/facilities/add/", views.adminAddFacilityView, name="admin_add_facility"),
    path("admin/facilities/edit/<int:pk>/", views.adminEditFacilityView, name="admin_edit_facility"),
    path("admin/facilities/delete/<int:pk>/", views.adminDeleteFacilityView, name="admin_delete_facility"),
    path("admin/facility-bookings/", views.adminFacilityBookingListView, name="admin_facility_booking_list"),
    path("admin/facility-bookings/<int:pk>/<str:action>/", views.adminUpdateBookingStatusView, name="admin_update_booking"),
    path("admin/alerts/", views.adminAlertListView, name="admin_alert_list"),
    path("admin/alerts/resolve/<int:pk>/", views.adminResolveAlertView, name="admin_resolve_alert"),
    path("admin/visitors/", views.adminVisitorListView, name="admin_visitor_list"),
    path("admin/guards/", views.adminGuardListView, name="admin_guard_list"),
    path("admin/guards/add/", views.adminAddGuardView, name="admin_add_guard"),
    path("admin/guards/edit/<int:pk>/", views.adminEditGuardView, name="admin_edit_guard"),
    path("admin/guards/delete/<int:pk>/", views.adminDeleteGuardView, name="admin_delete_guard"),

    # ── RESIDENT  ──
    path("resident/visitors/", views.residentVisitorListView, name="resident_visitor_list"),
    path("resident/visitors/add/", views.residentAddVisitorView, name="resident_add_visitor"),
    path("resident/visitors/approve/<int:pk>/", views.residentApproveVisitorView, name="resident_approve_visitor"),
    path("resident/visitors/deny/<int:pk>/", views.residentDenyVisitorView, name="resident_deny_visitor"),
    path("resident/complaints/", views.residentComplaintListView, name="resident_complaint_list"),
    path("resident/complaints/add/", views.residentAddComplaintView, name="resident_add_complaint"),
    path("resident/facilities/", views.residentFacilityListView, name="resident_facility_list"),
    path("resident/facilities/book/<int:facility_id>/", views.residentBookFacilityView, name="resident_book_facility"),
    path("resident/bookings/", views.residentMyBookingsView, name="resident_my_bookings"),
    path("resident/dues/", views.residentDuesView, name="resident_dues"),
    path("resident/dues/pay/<int:pk>/", views.residentPayDueView, name="resident_pay_due"),
    path("resident/notices/", views.residentNoticeListView, name="resident_notice_list"),
    path("resident/alert/raise/", views.residentRaiseAlertView, name="resident_raise_alert"),

    # ── GUARD ──
    path("guard/visitors/", views.guardVisitorListView, name="guard_visitor_list"),
    path("guard/visitors/verify-otp/", views.guardVerifyOTPView, name="guard_verify_otp"),
    path("guard/visitors/approve/<int:pk>/", views.guardApproveEntryView, name="guard_approve_entry"),
    path("guard/visitors/add/", views.guardAddVisitorView, name="guard_add_visitor"),
    path("guard/visitors/exit/<int:pk>/", views.guardMarkExitView, name="guard_mark_exit"),
    path("guard/alert/raise/", views.guardRaiseAlertView, name="guard_raise_alert"),

    # ── PAYMENT ──
    path("create-order/", views.create_razorpay_order, name="create_order"),
    path("booking/", views.booking, name="booking"),
    path("verify-payment/", views.verify_razorpay_payment, name="verify_payment"),
    
]
