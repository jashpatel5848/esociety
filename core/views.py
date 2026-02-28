from django.shortcuts import render, redirect, HttpResponse
from .forms import UserSignupForm,UserLoginForm 
from django.contrib.auth import authenticate,login
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def userSignupView(request): 
    if request.method == "POST":
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            #email send
            email = form.cleaned_data['email']
            send_mail(subject="welcome to esociety",message="thank you for registering with e-society.",from_email=settings.EMAIL_HOST_USER,recipient_list=[email])
            form.save()
            return redirect("login")
        else:  
            return render(request, 'core/signup.html', {'form': form})    
    else:
        form = UserSignupForm()
    return render(request, 'core/signup.html', {'form': form})


def userLoginView(request):
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
                return render(request,'core/login.html',{'form':form})

    else: 
        form = UserLoginForm()
        return render(request,'core/login.html',{'form': form}) 