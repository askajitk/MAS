from django.contrib import admin
from .models import Project, Building, ProjectTeamMember, ProjectVendor

class BuildingInline(admin.TabularInline):
    model = Building
    extra = 1

class ProjectTeamMemberInline(admin.TabularInline):
    model = ProjectTeamMember
    extra = 1

class ProjectVendorInline(admin.TabularInline):
    model = ProjectVendor
    extra = 1

class ProjectAdmin(admin.ModelAdmin):
    inlines = [BuildingInline, ProjectTeamMemberInline, ProjectVendorInline]
    list_display = ['name', 'project_number', 'created_at']
    search_fields = ['name', 'project_number']
    ordering = ['-created_at']

class BuildingAdmin(admin.ModelAdmin):
    list_display = ['name', 'project']
    list_filter = ['project']
    search_fields = ['name']

admin.site.register(Project, ProjectAdmin)
admin.site.register(Building, BuildingAdmin)
