from django import forms
from core.models import User
from .models import (
    Society, Flat, ResidentProfile, GuardProfile,
    Visitor, Complaint, Facility, FacilityBooking,
    MaintenanceDue, SocietyExpense, Notice, EmergencyAlert
)

class ResidentAddForm(forms.Form):
    first_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    mobile = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    society = forms.ModelChoiceField(queryset=Society.objects.all(), widget=forms.Select(attrs={'class': 'form-select'}))
    flat = forms.ModelChoiceField(queryset=Flat.objects.filter(status='vacant'), widget=forms.Select(attrs={'class': 'form-select'}))

class ResidentEditForm(forms.ModelForm):
    class Meta:
        model = ResidentProfile
        fields = ['flat']
        widgets = {
            'flat': forms.Select(attrs={'class': 'form-select'})
        }

class FlatForm(forms.ModelForm):
    class Meta:
        model = Flat
        fields = ['flat_number', 'floor', 'society']
        widgets = {
            'flat_number': forms.TextInput(attrs={'class': 'form-control'}),
            'floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'society': forms.Select(attrs={'class': 'form-select'})
        }

class ComplaintUpdateForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'remark']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'remark': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['society', 'title', 'content', 'notice_type']
        widgets = {
            'society': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notice_type': forms.Select(attrs={'class': 'form-select'})
        }

class MaintenanceDueForm(forms.ModelForm):
    class Meta:
        model = MaintenanceDue
        fields = ['resident', 'month', 'amount', 'due_date']
        widgets = {
            'resident': forms.Select(attrs={'class': 'form-select'}),
            'month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. March 2026'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

class SocietyExpenseForm(forms.ModelForm):
    class Meta:
        model = SocietyExpense
        fields = ['society', 'title', 'category', 'amount', 'date', 'description']
        widgets = {
            'society': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['society', 'name', 'description', 'capacity', 'price']
        widgets = {
            'society': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['name', 'mobile', 'purpose', 'vehicle_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '10'}),
            'purpose': forms.Select(attrs={'class': 'form-select'}),
            'vehicle_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'category', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class FacilityBookingForm(forms.ModelForm):
    class Meta:
        model = FacilityBooking
        fields = ['date', 'start_time', 'end_time']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        }

class EmergencyAlertForm(forms.ModelForm):
    class Meta:
        model = EmergencyAlert
        fields = ['alert_type', 'description']
        widgets = {
            'alert_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class OTPVerifyForm(forms.Form):
    otp = forms.CharField(max_length=6, widget=forms.TextInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Enter 6-digit OTP',
        'maxlength': '6'
    }))
