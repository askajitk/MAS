from django import forms
from .models import Project, Building, ProjectTeamMember, ProjectVendor
from django.contrib.auth import get_user_model

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name', 'project_number']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if Project.objects.filter(name__iexact=name).exists():
            raise forms.ValidationError('A project with this name already exists.')
        return name

class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['project', 'name']

    def clean(self):
        cleaned_data = super().clean()
        project = cleaned_data.get('project')
        name = cleaned_data.get('name')

        if project and name:
            if Building.objects.filter(project=project, name__iexact=name).exists():
                raise forms.ValidationError('This building name already exists in the project.')

        return cleaned_data

class ProjectTeamMemberForm(forms.ModelForm):
    from .models import BuildingRole
    
    building = forms.ModelChoiceField(
        queryset=Building.objects.none(),
        required=False,
        help_text="Optional: Select building to assign role"
    )
    role = forms.ChoiceField(
        choices=[('', '---------')] + BuildingRole.ROLE_CHOICES,
        required=False,
        help_text="Optional: Select role (Reviewer/Approver) for the building"
    )
    
    class Meta:
        model = ProjectTeamMember
        fields = ['project', 'user', 'building', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'user-select2'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter users to only show Team type
        self.fields['user'].queryset = get_user_model().objects.filter(user_type='Team')
        
        # If project is provided in initial data, limit building choices
        project = None
        if 'project' in self.initial and self.initial['project']:
            project = self.initial['project']
        elif 'project' in self.data and self.data.get('project'):
            try:
                project = Project.objects.get(pk=self.data.get('project'))
            except Project.DoesNotExist:
                project = None
        
        if project:
            self.fields['building'].queryset = Building.objects.filter(project=project)
        else:
            self.fields['building'].queryset = Building.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        building = cleaned_data.get('building')
        role = cleaned_data.get('role')
        
        # If building is provided, role must be provided too
        if building and not role:
            raise forms.ValidationError("Role is required when building is selected.")
        if role and not building:
            raise forms.ValidationError("Building is required when role is selected.")
        
        return cleaned_data

class ProjectVendorForm(forms.ModelForm):
    class Meta:
        model = ProjectVendor
        fields = ['project', 'user', 'building', 'services']
        widgets = {
            'user': forms.Select(attrs={'class': 'vendor-select2'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.filter(department='Vendor')
        # If project is provided in initial data, limit building choices
        project = None
        if 'project' in self.initial and self.initial['project']:
            project = self.initial['project']
        elif 'project' in self.data and self.data.get('project'):
            try:
                project = Project.objects.get(pk=self.data.get('project'))
            except Project.DoesNotExist:
                project = None

        if project:
            self.fields['building'].queryset = Building.objects.filter(project=project)
        else:
            self.fields['building'].queryset = Building.objects.none()

        # Services field shows all available services by default
        from services.models import Service
        self.fields['services'].queryset = Service.objects.all()