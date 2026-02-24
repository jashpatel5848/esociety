from django.contrib import admin
from django.urls import path,include
#from views.import userSignupView
from .import views

urlpatterns = [
    path('signup/',views.userSignupView,name='signup')


]