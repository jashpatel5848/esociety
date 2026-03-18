from django.db import models
from core.models import User


# ─────────────────────────────────────────
# 1. SOCIETY
# ─────────────────────────────────────────
class Society(models.Model):
    name        = models.CharField(max_length=100)
    address     = models.TextField()
    city        = models.CharField(max_length=50)
    state       = models.CharField(max_length=50)
    pincode     = models.CharField(max_length=6)
    total_flats = models.PositiveIntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# ─────────────────────────────────────────
# 2. FLAT
# ─────────────────────────────────────────
class Flat(models.Model):
    STATUS_CHOICES = (
        ('occupied',  'Occupied'),
        ('vacant',    'Vacant'),
    )
    society     = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='flats')
    flat_number = models.CharField(max_length=10)
    floor       = models.PositiveIntegerField(default=0)
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='vacant')

    def __str__(self):
        return f"Flat {self.flat_number} - {self.society.name}"


# ─────────────────────────────────────────
# 3. RESIDENT PROFILE
# ─────────────────────────────────────────
class ResidentProfile(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='resident_profile')
    society     = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='residents')
    flat        = models.ForeignKey(Flat, on_delete=models.SET_NULL, null=True, blank=True, related_name='residents')
    profile_pic = models.ImageField(upload_to='residents/', blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.flat}"


# ─────────────────────────────────────────
# 4. GUARD PROFILE
# ─────────────────────────────────────────
class GuardProfile(models.Model):
    SHIFT_CHOICES = (
        ('morning',  'Morning'),
        ('evening',  'Evening'),
        ('night',    'Night'),
    )
    user      = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guard_profile')
    society   = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='guards')
    shift     = models.CharField(max_length=10, choices=SHIFT_CHOICES, default='morning')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Guard: {self.user.email}"


# ─────────────────────────────────────────
# 5. VISITOR MANAGEMENT
# ─────────────────────────────────────────
class Visitor(models.Model):
    STATUS_CHOICES = (
        ('pending',  'Pending'),
        ('approved', 'Approved'),
        ('denied',   'Denied'),
        ('exited',   'Exited'),
    )
    PURPOSE_CHOICES = (
        ('guest',        'Guest'),
        ('delivery',     'Delivery'),
        ('maintenance',  'Maintenance'),
        ('other',        'Other'),
    )
    resident        = models.ForeignKey(ResidentProfile, on_delete=models.CASCADE, related_name='visitors')
    name            = models.CharField(max_length=100)
    mobile          = models.CharField(max_length=10)
    purpose         = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='guest')
    vehicle_number  = models.CharField(max_length=15, blank=True, null=True)
    otp             = models.CharField(max_length=6, blank=True, null=True)
    status          = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    entry_time      = models.DateTimeField(blank=True, null=True)
    exit_time       = models.DateTimeField(blank=True, null=True)
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} → Flat {self.resident.flat}"


# ─────────────────────────────────────────
# 6. COMPLAINT TRACKING
# ─────────────────────────────────────────
class Complaint(models.Model):
    CATEGORY_CHOICES = (
        ('plumbing',    'Plumbing'),
        ('electrical',  'Electrical'),
        ('cleaning',    'Cleaning'),
        ('security',    'Security'),
        ('lift',        'Lift'),
        ('other',       'Other'),
    )
    STATUS_CHOICES = (
        ('open',        'Open'),
        ('in_progress', 'In Progress'),
        ('resolved',    'Resolved'),
        ('closed',      'Closed'),
    )
    resident    = models.ForeignKey(ResidentProfile, on_delete=models.CASCADE, related_name='complaints')
    title       = models.CharField(max_length=150)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField()
    image       = models.ImageField(upload_to='complaints/', blank=True, null=True)
    status      = models.CharField(max_length=15, choices=STATUS_CHOICES, default='open')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    remark      = models.TextField(blank=True, null=True)   # admin remark
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.status}] {self.title} - {self.resident.user.email}"


# ─────────────────────────────────────────
# 7. FACILITY BOOKING
# ─────────────────────────────────────────
class Facility(models.Model):
    society     = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='facilities')
    name        = models.CharField(max_length=100)   # e.g. Gymnasium, Pool
    description = models.TextField(blank=True)
    capacity    = models.PositiveIntegerField(default=1)
    price       = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_active   = models.BooleanField(default=True)
    image       = models.ImageField(upload_to='facilities/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.society.name}"


class FacilityBooking(models.Model):
    STATUS_CHOICES = (
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    )
    resident    = models.ForeignKey(ResidentProfile, on_delete=models.CASCADE, related_name='bookings')
    facility    = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='bookings')
    date        = models.DateField()
    start_time  = models.TimeField()
    end_time    = models.TimeField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        # prevent double booking of same facility at same time
        unique_together = ('facility', 'date', 'start_time')

    def __str__(self):
        return f"{self.resident.user.email} → {self.facility.name} on {self.date}"


# ─────────────────────────────────────────
# 8. FINANCIAL MANAGEMENT
# ─────────────────────────────────────────
class MaintenanceDue(models.Model):
    STATUS_CHOICES = (
        ('unpaid', 'Unpaid'),
        ('paid',   'Paid'),
    )
    resident    = models.ForeignKey(ResidentProfile, on_delete=models.CASCADE, related_name='dues')
    month       = models.CharField(max_length=20)   # e.g. "March 2026"
    amount      = models.DecimalField(max_digits=8, decimal_places=2)
    due_date    = models.DateField()
    status      = models.CharField(max_length=10, choices=STATUS_CHOICES, default='unpaid')
    paid_on     = models.DateTimeField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.resident.user.email} - {self.month} - {self.status}"


class SocietyExpense(models.Model):
    CATEGORY_CHOICES = (
        ('maintenance', 'Maintenance'),
        ('salary',      'Salary'),
        ('utility',     'Utility'),
        ('repair',      'Repair'),
        ('other',       'Other'),
    )
    society     = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='expenses')
    title       = models.CharField(max_length=150)
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    amount      = models.DecimalField(max_digits=10, decimal_places=2)
    date        = models.DateField()
    description = models.TextField(blank=True)
    added_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - ₹{self.amount}"


# ─────────────────────────────────────────
# 9. NOTICE BOARD
# ─────────────────────────────────────────
class Notice(models.Model):
    TYPE_CHOICES = (
        ('general',   'General'),
        ('event',     'Event'),
        ('meeting',   'Meeting'),
        ('emergency', 'Emergency'),
    )
    society     = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='notices')
    posted_by   = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    title       = models.CharField(max_length=200)
    content     = models.TextField()
    notice_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='general')
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# ─────────────────────────────────────────
# 10. EMERGENCY ALERT
# ─────────────────────────────────────────
class EmergencyAlert(models.Model):
    TYPE_CHOICES = (
        ('fire',          'Fire'),
        ('unauthorized',  'Unauthorized Entry'),
        ('medical',       'Medical'),
        ('other',         'Other'),
    )
    society      = models.ForeignKey(Society, on_delete=models.CASCADE, related_name='alerts')
    raised_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    alert_type   = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    description  = models.TextField()
    is_resolved  = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    resolved_at  = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"[{self.alert_type}] {self.society.name} - {self.created_at.strftime('%d %b %Y')}"
