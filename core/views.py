from django.shortcuts import render, redirect
from .forms import UserSignupForm,UserLoginForm, UserProfileUpdateForm
from django.contrib.auth import authenticate,login,logout, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail,EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.contrib import messages
import os
import random
import string
from django.utils import timezone
from society.models import ResidentProfile, GuardProfile, Society
from core.models import User

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
                user = User.objects.get(email=email)
                if user.otp == otp_input:
                    user.status = 'active'
                    user.is_active = True  # Activate account on OTP success
                    user.otp = None
                    user.save()
                    
                    # Send welcome email now
                    homepage_url = request.build_absolute_uri('/')
                    html_content = render_to_string(
                        'core/welcome_email.html',
                        {'email': email, 'homepage_url': homepage_url}
                    )
                    email_msg = EmailMultiAlternatives(
                        subject="Welcome to eSociety",
                        body="Thank you for registering with e-Society.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
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
                    messages.error(request, 'Invalid OTP')
                    return render(request, 'core/signup.html', {'show_otp_popup': True, 'email': email, 'form': UserSignupForm()})
            except Exception as e:
                messages.error(request, 'Something went wrong.')
                return render(request, 'core/signup.html', {'show_otp_popup': True, 'email': email, 'form': UserSignupForm()})

        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            user.status = 'inactive'
            
            # OTP mandatory only for non-admins
            if user.role != 'admin':
                user.is_active = False
            
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
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email]
            )
            email_msg.attach_alternative(html_content, "text/html")
            email_msg.send()

            request.session['registration_email'] = email
            return render(request, 'core/signup.html', {'show_otp_popup': True, 'email': email, 'form': form})
        else:  
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
            return render(request, 'core/signup.html', {'form': form})    
    else:
        # GET Request: Check if there's a pending registration in session
        email = request.session.get('registration_email')
        if email:
            user = User.objects.filter(email=email).first()
            if user and not user.is_active:
                return render(request, 'core/signup.html', {
                    'show_otp_popup': True, 
                    'email': email, 
                    'form': UserSignupForm()
                })
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
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, email=email, password=password)
            if user:
                login(request, user)
                if user.role == "admin":
                    return redirect("admin_dashboard")   
                elif user.role == "resident":
                    return redirect("resident_dashboard")
                elif user.role == "guard":
                    return redirect("guard_dashboard")
            else:
                user_check = User.objects.filter(email=email).first()
                if user_check and user_check.check_password(password) and not user_check.is_active:
                    request.session['registration_email'] = email
                    return redirect('signup')
                
                messages.error(request, 'Invalid email or password!')
                # Let it fall through to the final return
    else: 
        form = UserLoginForm()
    
    return render(request, 'core/login.html', {'form': form})


    
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


@login_required
def userProfileView(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            # Redirect back to the same page where modal was opened
            next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'home'))
            return redirect(next_url)
    else:
        form = UserProfileUpdateForm(instance=request.user)
    
    return render(request, 'core/profile.html', {'form': form})


@login_required
def changePasswordView(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Password updated successfully!')
            update_session_auth_hash(request, user)  # Important to keep the user logged in
            return redirect('profile')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'core/change_password.html', {'form': form})


# ──────────────────────────────────────────────
#  FORGOT PASSWORD FLOW
# ──────────────────────────────────────────────

def forgotPasswordView(request):
    """Step 1 – Enter email to receive OTP."""

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'core/forgot_password.html')

        # Generate & save OTP
        otp_val = str(random.randint(100000, 999999))
        user.otp = otp_val
        user.otp_created_at = timezone.now()
        user.save()

        # Send OTP email
        html_content = render_to_string(
            'core/forgot_password_otp_email.html',
            {'email': email, 'otp': otp_val}
        )
        email_msg = EmailMultiAlternatives(
            subject="Password Reset OTP — e-Society",
            body=f"Your password reset OTP is {otp_val}. It expires in 10 minutes.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        request.session['reset_email'] = email
        messages.success(request, f'OTP sent to {email}. Please check your inbox.')
        return redirect('verify_reset_otp')

    return render(request, 'core/forgot_password.html')


def verifyResetOtpView(request):
    """Step 2 – Verify the OTP received on email."""

    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        otp_input = request.POST.get('otp', '').strip()
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')

        # Check expiry (10 minutes)
        if user.otp_created_at:
            elapsed = timezone.now() - user.otp_created_at
            if elapsed.total_seconds() > 600:
                messages.error(request, 'OTP has expired. Please request a new one.')
                return redirect('forgot_password')

        if user.otp == otp_input:
            # Clear OTP, grant reset session flag
            user.otp = None
            user.otp_created_at = None
            user.save()
            request.session['reset_verified'] = True
            return redirect('reset_password')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    return render(request, 'core/verify_reset_otp.html', {'email': email})


def resetPasswordView(request):
    """Step 3 – Set new password."""

    email = request.session.get('reset_email')
    verified = request.session.get('reset_verified', False)

    if not email or not verified:
        messages.error(request, 'Unauthorized access. Please start again.')
        return redirect('forgot_password')

    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if len(new_password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'core/reset_password.html')

        if new_password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'core/reset_password.html')

        user = User.objects.filter(email=email).first()
        if not user:
            messages.error(request, 'User not found.')
            return redirect('forgot_password')

        user.set_password(new_password)
        user.save()

        # Clean session
        del request.session['reset_email']
        del request.session['reset_verified']

        messages.success(request, 'Password reset successfully! Please log in.')
        return redirect('login')

    return render(request, 'core/reset_password.html')
