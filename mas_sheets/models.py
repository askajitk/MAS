from django.db import models
from django.conf import settings
from projects.models import Project, Building
from services.models import Service, Item
import os

def mas_file_path(instance, filename):
    """
    Generate file path for MAS attachments
    File will be uploaded to MEDIA_ROOT/mas_files/project_<id>/mas_<id>.<extension>
    """
    ext = filename.split('.')[-1]
    filename = f"{instance.mas_id}.{ext}"
    return os.path.join('mas_files', f'project_{instance.project.id}', filename)

class MAS(models.Model):
    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_requested', 'Revision Requested'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    revision = models.CharField(max_length=5, default='R0', editable=False)
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, 
                               on_delete=models.SET_NULL, 
                               null=True, blank=True,
                               related_name='reviewed_mas')
    approver = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.SET_NULL,
                               null=True, blank=True,
                               related_name='approved_mas')
    review_comment = models.TextField(blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    approval_comment = models.TextField(blank=True)
    approval_date = models.DateTimeField(null=True, blank=True)
    building = models.ForeignKey(Building, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    make = models.CharField(max_length=200)
    other_make = models.CharField(max_length=200, blank=True, null=True)
    attachment = models.FileField(upload_to=mas_file_path, 
                                help_text='Upload PDF or JPEG files only (max 5MB)')
    
    mas_id = models.CharField(max_length=50, unique=True, editable=False)
    serial_number = models.PositiveIntegerField(editable=False)
    
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, 
                              on_delete=models.CASCADE, 
                              related_name='created_mas')
    status = models.CharField(max_length=20, 
                            choices=STATUS_CHOICES, 
                            default='pending_review')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'MAS'
        verbose_name_plural = 'MAS'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.serial_number:
            # Get the latest serial number for this project
            last_mas = MAS.objects.filter(project=self.project).order_by('-serial_number').first()
            self.serial_number = (last_mas.serial_number + 1) if last_mas else 1
        
        if not self.mas_id:
            # Generate MAS ID in format: "Project Number"-"Building"-MAS-"Service"-"Serial Number"
            self.mas_id = f"{self.project.project_number}-{self.building.name}-MAS-{self.service.name}-{self.serial_number}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.mas_id
    
    def can_edit(self):
        return self.status == 'pending'
