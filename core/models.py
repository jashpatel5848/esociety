from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager



class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('Superuser must have is_admin=True.')

        return self.create_user(email, password, **extra_fields)

    

# Create your models here.

class User(AbstractBaseUser):
     
    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin

    
    role_choice = (
        ('admin', 'admin'),
        ('resident', 'resident'),
        ('guard', 'guard'),
    )
    
    gender_choice = (
        ('male','male'),
        ('female','female'),
        ('other','other')
    )

    role = models.CharField(max_length=10, choices=role_choice, default='resident')
    email = models.EmailField(unique=True)
    
    first_name = models.CharField(max_length=50, blank=True, null=True )
    last_name = models.CharField(max_length=50, blank=True, null=True )
    gender = models.CharField(max_length=10, choices=gender_choice, blank=True, null=True )
    mobile = models.CharField(max_length=10, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    # override username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


