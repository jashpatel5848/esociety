from django.urls import path
from . import views

urlpatterns = [
    path("admin/",views.adminDashboardView,name="admin_dashboard"),
    path("resident/",views.residentDashBoard,name="resident_dashboard"),
    path("guard/",views.guardDashBoard,name="guard_dashboard")
    
]
