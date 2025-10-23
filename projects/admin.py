from django.contrib import admin
from django import forms
from .models import Project, Building, ProjectTeamMember, ProjectVendor, BuildingRole

class BuildingInline(admin.TabularInline):
    model = Building
    extra = 1
    fields = ['name']

class BuildingRoleInline(admin.TabularInline):
    """Inline for assigning Team members with role for this building"""
    model = BuildingRole
    extra = 1
    fields = ['user', 'role']
    autocomplete_fields = ['user']

class ProjectTeamMemberForm(forms.ModelForm):
    building = forms.ModelChoiceField(
        queryset=Building.objects.none(),
        required=False,
        help_text="Select building to assign role"
    )
    role = forms.ChoiceField(
        choices=[('', '---------')] + BuildingRole.ROLE_CHOICES,
        required=False,
        help_text="Select role (Reviewer/Approver)"
    )
    
    class Meta:
        model = ProjectTeamMember
        fields = ['user', 'building', 'role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter buildings based on the project
        if self.instance.project_id:
            self.fields['building'].queryset = Building.objects.filter(project_id=self.instance.project_id)
        elif 'initial' in kwargs and 'project' in kwargs['initial']:
            project_id = kwargs['initial']['project']
            self.fields['building'].queryset = Building.objects.filter(project_id=project_id)

class ProjectTeamMemberInline(admin.TabularInline):
    model = ProjectTeamMember
    form = ProjectTeamMemberForm
    extra = 1
    fields = ['user', 'building', 'role', 'get_user_type', 'added_at']
    readonly_fields = ['get_user_type', 'added_at']
    autocomplete_fields = ['user']
    
    def get_user_type(self, obj):
        return obj.user.user_type if obj.user else '-'
    get_user_type.short_description = 'User Type'
    
    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        # Pass the project to the form
        if obj:
            formset.form.base_fields['building'].queryset = Building.objects.filter(project=obj)
        return formset
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Create BuildingRole if building and role are provided
        building = form.cleaned_data.get('building')
        role = form.cleaned_data.get('role')
        if building and role and obj.user:
            BuildingRole.objects.get_or_create(
                building=building,
                user=obj.user,
                role=role
            )
    
    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
            # Get the form for this instance
            for form in formset.forms:
                if form.instance == instance:
                    building = form.cleaned_data.get('building')
                    role = form.cleaned_data.get('role')
                    if building and role and instance.user:
                        BuildingRole.objects.get_or_create(
                            building=building,
                            user=instance.user,
                            role=role
                        )
        formset.save_m2m()
        # Handle deletions
        for obj in formset.deleted_objects:
            obj.delete()

class ProjectVendorInline(admin.StackedInline):
    model = ProjectVendor
    extra = 0
    fields = ['user', 'building', 'services', 'added_at']
    readonly_fields = ['added_at']
    autocomplete_fields = ['user']
    filter_horizontal = ['services']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "building":
            # Filter buildings to only show those from the current project
            if request.resolver_match.kwargs.get('object_id'):
                project_id = request.resolver_match.kwargs['object_id']
                kwargs["queryset"] = Building.objects.filter(project_id=project_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

class ProjectAdmin(admin.ModelAdmin):
    inlines = [BuildingInline, ProjectTeamMemberInline, ProjectVendorInline]
    list_display = ['name', 'project_number', 'owner', 'created_at']
    search_fields = ['name', 'project_number']
    ordering = ['-created_at']

class BuildingAdmin(admin.ModelAdmin):
    inlines = [BuildingRoleInline]
    list_display = ['name', 'project', 'get_reviewers', 'get_approvers']
    list_filter = ['project']
    search_fields = ['name', 'project__name']
    
    def get_reviewers(self, obj):
        reviewers = obj.role_assignments.filter(role='Reviewer')
        return ", ".join([r.user.get_full_name() for r in reviewers]) or '-'
    get_reviewers.short_description = 'Reviewers'
    
    def get_approvers(self, obj):
        approvers = obj.role_assignments.filter(role='Approver')
        return ", ".join([a.user.get_full_name() for a in approvers]) or '-'
    get_approvers.short_description = 'Approvers'

class BuildingRoleAdmin(admin.ModelAdmin):
    list_display = ['building', 'user', 'role', 'assigned_at']
    list_filter = ['role', 'building__project']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'building__name']
    autocomplete_fields = ['user', 'building']

class ProjectTeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_user_type', 'project', 'added_at']
    list_filter = ['project', 'user__user_type']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'project__name']
    autocomplete_fields = ['user']
    
    def get_user_type(self, obj):
        return obj.user.user_type if obj.user else '-'
    get_user_type.short_description = 'User Type'

class ProjectVendorAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'building', 'get_services', 'added_at']
    list_filter = ['project', 'building']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'project__name']
    autocomplete_fields = ['user']
    filter_horizontal = ['services']
    
    def get_services(self, obj):
        return ", ".join([s.name for s in obj.services.all()])
    get_services.short_description = 'Services'

admin.site.register(Project, ProjectAdmin)
admin.site.register(Building, BuildingAdmin)
admin.site.register(BuildingRole, BuildingRoleAdmin)
admin.site.register(ProjectTeamMember, ProjectTeamMemberAdmin)
admin.site.register(ProjectVendor, ProjectVendorAdmin)
