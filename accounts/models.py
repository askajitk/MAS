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

    department = models.CharField(max_length=100, choices=DEPARTMENT_CHOICES)
    other_department = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=50)

    def save(self, *args, **kwargs):
        if self.department != 'Other':
            self.other_department = None
        super().save(*args, **kwargs)
