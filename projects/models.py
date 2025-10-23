from django.db import models
from django.contrib.auth import get_user_model
from services.models import Service

class Project(models.Model):
    name = models.CharField(max_length=200, unique=True)
    project_number = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='owned_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.project_number})"

class Building(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='buildings')
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['project', 'name']

    def __str__(self):
        return f"{self.name} - {self.project}"

class ProjectTeamMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project}"

class ProjectVendor(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='vendors')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    # Optional building assignment for this vendor within the project
    building = models.ForeignKey('Building', on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor_assignments')
    # Services assigned to this vendor for the project (vendor can have multiple services)
    services = models.ManyToManyField(Service, blank=True, related_name='vendor_assignments')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['project', 'user']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.project}"

class BuildingRole(models.Model):
    """Assign Team members as Reviewer or Approver for specific buildings"""
    ROLE_CHOICES = [
        ('Reviewer', 'Reviewer'),
        ('Approver', 'Approver'),
    ]
    
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='role_assignments')
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, 
                            limit_choices_to={'user_type': 'Team'})
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['building', 'user', 'role']
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.role} for {self.building}"
