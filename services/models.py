from django.db import models
from django.contrib.auth import get_user_model

class Service(models.Model):
    SERVICE_CHOICES = [
        ('Electrical', 'Electrical'),
        ('PHE', 'PHE'),
        ('Fire Fighting', 'Fire Fighting'),
        ('ELV', 'ELV'),
        ('HVAC', 'HVAC'),
        ('Other', 'Other'),
    ]

    name = models.CharField(max_length=100, choices=SERVICE_CHOICES)
    other_name = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.other_name if self.name == 'Other' else self.name

class Item(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.service})"

class ItemMake(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='makes')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.item})"

class ServiceLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
    ]

    user = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    # Snapshot of username at time of logging to preserve history if user is deleted/renamed
    username = models.CharField(max_length=150, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    content_type = models.CharField(max_length=50)  # Service, Item, or ItemMake
    object_id = models.IntegerField()
    details = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"
