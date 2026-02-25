from django.shortcuts import render
from django.contrib.auth.decorators import login_required 

# Create your views here.
@login_required(login_url="login")  #check in core.urls.py   ( login name should exist.....)
def adminDashboardView(request):
    return render(request,"society/admin_dashboard.html")

@login_required(login_url="login")
def residentDashBoard(request):
    return render(request,"society/resident_dashboard.html")

@login_required(login_url="login")
def guardDashBoard(request):
    return render(request,"society/guard_dashboard.html")