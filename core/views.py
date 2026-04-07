from django.shortcuts import render, redirect, HttpResponse
from .forms import UserSignupForm,UserLoginForm 
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import os
import random
import string
from django.utils import timezone
from society.models import ResidentProfile, GuardProfile, Society

# Create your views here.
def userSignupView(request): 
    if request.user.is_authenticated:
        if request.user.role == "admin":
            return redirect("admin_dashboard")
        elif request.user.role == "resident":
            return redirect("resident_dashboard")
        elif request.user.role == "guard":
            return redirect("guard_dashboard")
        
    if request.method == "POST":
        if 'otp' in request.POST:
            email = request.session.get('registration_email')
            otp_input = request.POST.get('otp')
            try:
                from core.models import User
                user = User.objects.get(email=email)
                if user.otp == otp_input:
                    user.status = 'active'
                    user.otp = None
                    user.save()
                    
                    # Send welcome email now
                    html_content = render_to_string(
                        'core/welcome_email.html',
                        {'email': email}
                    )
                    email_msg = EmailMultiAlternatives(
                        subject="Welcome to eSociety",
                        body="Thank you for registering with e-Society.",
                        from_email=settings.EMAIL_HOST_USER,
                        to=[email]
                    )
                    email_msg.attach_alternative(html_content, "text/html")
                    
                    image_path = os.path.join(settings.BASE_DIR, 'static/images/welcome.png')
                    if os.path.exists(image_path):
                        email_msg.attach_file(image_path)
                    
                    email_msg.send()
                    del request.session['registration_email']
                    return redirect("login")
                else:
                    return render(request, 'core/signup.html', {'show_otp_popup': True, 'error': 'Invalid OTP', 'email': email, 'form': UserSignupForm()})
            except Exception as e:
                return render(request, 'core/signup.html', {'show_otp_popup': True, 'error': 'Something went wrong.', 'email': email, 'form': UserSignupForm()})

        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            user.status = 'inactive'
            otp_val = str(random.randint(100000, 999999))
            user.otp = otp_val
            user.save()
            

            # Role ke hisaab se profile banao
            society = Society.objects.first()

            if user.role == 'resident':
                ResidentProfile.objects.create(
                    user=user,
                    society=society,
                )
            elif user.role == 'guard':
                GuardProfile.objects.create(
                    user=user,
                    society=society,
                )
           
            #email send
            email = form.cleaned_data['email']
            
            # Send OTP email
            html_content = render_to_string(
                'core/otp_email.html',
                {'email': email, 'otp': otp_val}
            )
            email_msg = EmailMultiAlternatives(
                subject="Verify your eSociety Account",
                body=f"Your OTP for registration is {otp_val}.",
                from_email=settings.EMAIL_HOST_USER,
                to=[email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()

            request.session['registration_email'] = email
            return render(request, 'core/signup.html', {'show_otp_popup': True, 'email': email, 'form': form})
        else:  
            return render(request, 'core/signup.html', {'form': form})    
    else:
        form = UserSignupForm()
    return render(request, 'core/signup.html', {'form': form})


def userLoginView(request):
    # Agar already logged in hai toh redirect 
    if request.user.is_authenticated:
        if request.user.role == "admin":
            return redirect("admin_dashboard")
        elif request.user.role == "resident":
            return redirect("resident_dashboard")
        elif request.user.role == "guard":
            return redirect("guard_dashboard")
        
    if request.method =="POST":  
        form = UserLoginForm(request.POST or None)
        if form.is_valid():
            print(form.cleaned_data)
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request,email=email,password=password)   #it will check iin database....
            if user:
                login(request,user)
                print("user....",user)
                print("role...",user.role)
                if user.role == "admin":
                    return redirect("admin_dashboard")   #society > urls.py <-- file to 
                elif user.role == "resident":
                    return redirect("resident_dashboard")
                elif user.role == "guard":
                    return redirect("guard_dashboard")

            else:
                return render(request,'core/login.html', {'form': form, 'error': 'Invalid email or password!'})

    else: 
        form = UserLoginForm()
        return render(request,'core/login.html',{'form': form}) 


    
def userLogoutView(request):
    logout(request)             #user ka sessio clear
    return redirect('home')


def userHomepageView(request):
    if request.user.is_authenticated:
        if request.user.role == "admin":
            return redirect("admin_dashboard")
        elif request.user.role == "resident":
            return redirect("resident_dashboard")
        elif request.user.role == "guard":
            return redirect("guard_dashboard")  
    return render(request, 'home.html')
