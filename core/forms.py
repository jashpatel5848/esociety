from django.contrib.auth.forms import UserCreationForm
from .models import User
from django import forms


class UserSignupForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','gender','email','role','password1','password2']

        widgets = {
            'password1':forms.PasswordInput(),         # password1
            'password2':forms.PasswordInput(),         # password2
            'gender':forms.RadioSelect()               # gender radio 
        }


class UserLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())