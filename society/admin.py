from django.contrib import admin
from .models import Society, Flat, ResidentProfile, GuardProfile, Visitor, Complaint, Facility, FacilityBooking, MaintenanceDue, SocietyExpense, Notice, EmergencyAlert

# Register your models here.
admin.site.register(Society)
admin.site.register(Flat)
admin.site.register(ResidentProfile)
admin.site.register(GuardProfile)
admin.site.register(Visitor)
admin.site.register(Complaint)
admin.site.register(Facility)
admin.site.register(FacilityBooking)
admin.site.register(MaintenanceDue)
admin.site.register(SocietyExpense)
admin.site.register(Notice)
admin.site.register(EmergencyAlert)
