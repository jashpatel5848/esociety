from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import UserSignupForm

# Create your views here.
def userSignupView(request):
    if request.method == "POST":
        form = UserSignupForm(request.POST or None)
        if form.is_valid():
            user = form.save()
            # Auto-login after signup
            login(request, user)
            return redirect("/")
        else:
            return render(request, 'core/signup.html', {'form': form})    
    else:
        form = UserSignupForm()
        return render(request, 'core/signup.html', {'form': form})

def userLoginView(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect("/")
        else:
            error_message = "Invalid email/username or password. Please try again."
            return render(request, 'login.html', {'error': error_message})
    
    return render(request, 'login.html')    