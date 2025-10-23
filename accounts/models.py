from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    DEPARTMENT_CHOICES = [
        ('Architecture', 'Architecture'),
        ('Structure', 'Structure'),
        ('MEP', 'MEP'),
        ('Construction Management', 'Construction Management'),
        ('Strategy', 'Strategy'),
        ('Vendor', 'Vendor'),
        ('Other', 'Other'),
    ]

    USER_TYPE_CHOICES = [
        ('Admin', 'Admin'),
        ('Team', 'Team'),
        ('Vendor', 'Vendor'),
    ]

    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)
    other_department = models.CharField(max_length=100, blank=True, null=True)
    user_type = models.CharField(max_length=50, choices=USER_TYPE_CHOICES, default='Vendor')

    def save(self, *args, **kwargs):
        # Clear other_department if not 'Other'
        if self.department != 'Other':
            self.other_department = None
            
        # Set staff status based on user_type
        if self.user_type in ['Admin', 'Team']:
            self.is_staff = True
        else:
            self.is_staff = False
            
        # Make Admin users superusers
        if self.user_type == 'Admin':
            self.is_superuser = True
        else:
            self.is_superuser = False
            
        super().save(*args, **kwargs)
