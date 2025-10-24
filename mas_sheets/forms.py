from django import forms
from .models import MAS
from projects.models import Project, Building
from services.models import Service, Item
from django.core.exceptions import ValidationError
import mimetypes

class MASForm(forms.ModelForm):
    make_choices = forms.ChoiceField(choices=[], required=True)
    other_make = forms.CharField(max_length=200, required=False)
    
    class Meta:
        model = MAS
        fields = ['project', 'building', 'service', 'item', 'make_choices', 'other_make', 'attachment']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'building': forms.Select(attrs={'class': 'form-control'}),
            'service': forms.Select(attrs={'class': 'form-control'}),
            'item': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        self.user = user
        super().__init__(*args, **kwargs)
        # Determine assignments from ProjectVendor
        from projects.models import ProjectVendor

        vendor_assignments = ProjectVendor.objects.filter(user=user)

        # Projects where the user is assigned
        project_ids = vendor_assignments.values_list('project_id', flat=True)
        self.fields['project'].queryset = Project.objects.filter(id__in=project_ids)

        # Initialize other fields as empty initially
        self.fields['building'].queryset = Building.objects.none()
        self.fields['service'].queryset = Service.objects.none()
        self.fields['item'].queryset = Item.objects.none()
        self.fields['make_choices'].choices = [('', 'Select Make')]
        
        # If form is bound (POST data), populate querysets based on submitted data
        if self.is_bound:
            try:
                project_id = self.data.get('project')
                if project_id:
                    self.fields['building'].queryset = Building.objects.filter(project_id=project_id)
                    # Load services based on vendor assignment
                    try:
                        pv = ProjectVendor.objects.get(project_id=project_id, user=user)
                        assigned_services = pv.services.all()
                        if assigned_services.exists():
                            self.fields['service'].queryset = assigned_services
                        else:
                            self.fields['service'].queryset = Service.objects.all()
                    except ProjectVendor.DoesNotExist:
                        self.fields['service'].queryset = Service.objects.all()
                
                service_id = self.data.get('service')
                if service_id:
                    items_qs = Item.objects.filter(service_id=service_id)
                    if project_id:
                        blocked_item_ids = MAS.objects.filter(
                            creator=user,
                            project_id=project_id,
                            is_latest=True,
                        ).values_list('item_id', flat=True)
                        items_qs = items_qs.exclude(id__in=list(blocked_item_ids))
                    self.fields['item'].queryset = items_qs
                
                item_id = self.data.get('item')
                if item_id:
                    from services.models import ItemMake
                    makes_queryset = ItemMake.objects.filter(item_id=item_id).values_list('id', 'name')
                    makes = [('', 'Select Make')]
                    makes.extend([(str(make_id), make_name) for make_id, make_name in makes_queryset])
                    makes.append(('other', 'Other'))
                    self.fields['make_choices'].choices = makes
            except (ValueError, TypeError):
                pass
        
        # If we're editing an existing instance, populate the fields
        elif self.instance.pk:
            self.fields['building'].queryset = Building.objects.filter(project=self.instance.project)
            # Only show services assigned to this vendor for the project if assignments exist
            try:
                pv = ProjectVendor.objects.get(project=self.instance.project, user=user)
                assigned_services = pv.services.all()
                if assigned_services.exists():
                    self.fields['service'].queryset = assigned_services
                else:
                    # Services are global; show all if no assignment
                    self.fields['service'].queryset = Service.objects.all()
            except ProjectVendor.DoesNotExist:
                self.fields['service'].queryset = Service.objects.filter(project=self.instance.project)
            # Items while editing: exclude blocked items but always include the current item
            items_qs = Item.objects.filter(service=self.instance.service)
            blocked_item_ids = MAS.objects.filter(
                creator=user,
                project=self.instance.project,
                is_latest=True,
            ).exclude(pk=self.instance.pk).values_list('item_id', flat=True)
            self.fields['item'].queryset = items_qs.exclude(id__in=list(blocked_item_ids)) | Item.objects.filter(pk=self.instance.item_id)
            
            # Set make choices from ItemMake model
            from services.models import ItemMake
            makes_queryset = ItemMake.objects.filter(item=self.instance.item).values_list('id', 'name')
            makes = [(str(make_id), make_name) for make_id, make_name in makes_queryset]
            makes.append(('other', 'Other'))
            self.fields['make_choices'].choices = makes
            
            # Set initial value for make_choices based on saved make
            if self.instance.make:
                # Try to find matching ItemMake
                matching_make = ItemMake.objects.filter(
                    item=self.instance.item, 
                    name=self.instance.make
                ).first()
                if matching_make:
                    self.initial['make_choices'] = str(matching_make.id)
                else:
                    # It's a custom make
                    self.initial['make_choices'] = 'other'
                    self.initial['other_make'] = self.instance.make
        else:
            # If there's only one project assignment, preselect it
            if self.fields['project'].queryset.count() == 1:
                only_project = self.fields['project'].queryset.first()
                self.initial['project'] = only_project.pk
                # Set building queryset to assigned building if present
                try:
                    pv = vendor_assignments.get(project=only_project)
                    if pv.building:
                        self.fields['building'].queryset = Building.objects.filter(pk=pv.building.pk)
                        self.initial['building'] = pv.building.pk
                    else:
                        self.fields['building'].queryset = Building.objects.filter(project=only_project)
                    # services
                    assigned_services = pv.services.all()
                    if assigned_services.exists():
                        self.fields['service'].queryset = assigned_services
                        if assigned_services.count() == 1:
                            only_service = assigned_services.first()
                            self.initial['service'] = only_service.pk
                            # Pre-populate items for the pre-selected service and filter blocked items
                            items_qs = Item.objects.filter(service=only_service)
                            blocked_item_ids = MAS.objects.filter(
                                creator=user,
                                project=only_project,
                                is_latest=True,
                            ).values_list('item_id', flat=True)
                            self.fields['item'].queryset = items_qs.exclude(id__in=list(blocked_item_ids))
                    else:
                        self.fields['service'].queryset = Service.objects.all()
                except ProjectVendor.DoesNotExist:
                    self.fields['building'].queryset = Building.objects.filter(project=only_project)
                    self.fields['service'].queryset = Service.objects.filter(project=only_project)
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Get file size
            file_size = attachment.size
            if file_size > 5242880:  # 5MB limit
                raise ValidationError("File size must not exceed 5MB.")
            
            # Check file type
            content_type = mimetypes.guess_type(attachment.name)[0]
            if content_type not in ['application/pdf', 'image/jpeg', 'image/jpg']:
                raise ValidationError("Only PDF and JPEG files are allowed.")
        
        return attachment
    
    def clean(self):
        cleaned_data = super().clean()
        make_choices = cleaned_data.get('make_choices')
        other_make = cleaned_data.get('other_make')
        project = cleaned_data.get('project')
        item = cleaned_data.get('item')
        
        if make_choices == 'other' and not other_make:
            raise ValidationError({'other_make': 'This field is required when selecting Other as make.'})
        
        # Set the actual make value
        if make_choices == 'other':
            cleaned_data['make'] = other_make
        else:
            # Fetch the make name from ItemMake model
            from services.models import ItemMake
            try:
                make_obj = ItemMake.objects.get(id=make_choices)
                cleaned_data['make'] = make_obj.name
            except (ItemMake.DoesNotExist, ValueError, TypeError):
                cleaned_data['make'] = make_choices
        
        # Prevent duplicate MAS creation for the same Project + Item by the same vendor
        # If any latest MAS exists for this pair, vendor should revise existing instead of creating a new one
        if project and item:
            existing_qs = MAS.objects.filter(
                creator=self.user,
                project=project,
                item=item,
                is_latest=True,
            )
            # When editing, ignore the current instance
            if self.instance and self.instance.pk:
                existing_qs = existing_qs.exclude(pk=self.instance.pk)

            if existing_qs.exists():
                raise ValidationError(
                    {
                        'item': (
                            'An MAS already exists for this Item in the selected Project. '
                            'Please submit a revision to the existing MAS instead of creating a new one.'
                        )
                    }
                )

        return cleaned_data