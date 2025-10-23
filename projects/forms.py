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
    class Meta:
        model = ProjectTeamMember
        fields = ['project', 'user']
        widgets = {
            'user': forms.Select(attrs={'class': 'user-select2'})
        }

class ProjectVendorForm(forms.ModelForm):
    class Meta:
        model = ProjectVendor
        fields = ['project', 'user']
        widgets = {
            'user': forms.Select(attrs={'class': 'vendor-select2'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['user'].queryset = get_user_model().objects.filter(department='Vendor')