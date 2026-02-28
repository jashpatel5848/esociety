from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from .decorators import role_required 

# Create your views here.
#@login_required(login_url="login")  #check in core.urls.py   ( login name should exist.....)
@role_required(allowed_roles=["admin"])    #check in core.urls.py   ( login name should exist.....)
def adminDashboardView(request):
    return render(request,"society/admin/admin_dashboard.html")

#@login_required(login_url="login")
@role_required(allowed_roles=["resident"])    #check in core.urls.py   ( login name should exist.....)
def residentDashBoard(request):
    return render(request,"society/resident/resident_dashboard.html")

#@login_required(login_url="login")
@role_required(allowed_roles=["guard"])     #check in core.urls.py   ( login name should exist.....)
def guardDashBoard(request):
    return render(request,"society/guard/guard_dashboard.html") 