from django.db import models
from django.conf import settings
from projects.models import Project, Building
from services.models import Service, Item
from django.utils import timezone
from django.db.models import Q
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
    
    mas_id = models.CharField(max_length=50, editable=False)
    serial_number = models.PositiveIntegerField(editable=False)
    
    # Revision tracking
    parent_mas = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='revisions')
    is_latest = models.BooleanField(default=True)  # Only the latest revision should be True
    
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
        
        # When saving a new revision, mark previous versions as not latest
        if self.pk is None and self.parent_mas:
            MAS.objects.filter(
                mas_id=self.mas_id, 
                is_latest=True
            ).update(is_latest=False)
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.mas_id} ({self.revision})"
    
    def can_edit(self):
        return self.status == 'pending_review' and self.is_latest
    
    def get_revision_history(self):
        """Get all revisions of this MAS in chronological order"""
        if self.parent_mas:
            # If this is a revision, get the original and all its revisions
            return MAS.objects.filter(
                Q(mas_id=self.mas_id) | Q(id=self.parent_mas.id)
            ).order_by('created_at')
        else:
            # If this is the original, get it and all its revisions
            return MAS.objects.filter(mas_id=self.mas_id).order_by('created_at')
    
    def log_activity(self, action, user, details=''):
        """Helper method to log activity"""
        MASActivityLog.objects.create(
            mas=self,
            action=action,
            user=user,
            details=details
        )


class MASActivityLog(models.Model):
    """
    Logs all activities related to MAS (create, edit, review, approve, reject, etc.)
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('edited', 'Edited'),
        ('submitted_review', 'Submitted for Review'),
        ('reviewed', 'Reviewed'),
        ('submitted_approval', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('revision_requested', 'Revision Requested'),
        ('revision_submitted', 'Revision Submitted'),
    ]
    
    mas = models.ForeignKey(MAS, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    # Snapshot of username at time of logging to preserve history
    username = models.CharField(max_length=150, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)
    
    # Snapshot of key MAS data at the time of action
    project_name = models.CharField(max_length=200, blank=True)
    building_name = models.CharField(max_length=200, blank=True)
    service_name = models.CharField(max_length=200, blank=True)
    item_name = models.CharField(max_length=200, blank=True)
    make = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'MAS Activity Log'
        verbose_name_plural = 'MAS Activity Logs'
    
    def save(self, *args, **kwargs):
        # Capture username snapshot if available
        if not self.username and self.user:
            self.username = self.user.username
        # Capture snapshot of MAS data if not already set
        if not self.project_name and self.mas:
            self.project_name = self.mas.project.name
            self.building_name = self.mas.building.name
            self.service_name = self.mas.service.name
            self.item_name = self.mas.item.name
            self.make = self.mas.make
            self.status = self.mas.status
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.mas.mas_id} - {self.get_action_display()} by {self.user} at {self.timestamp}"
