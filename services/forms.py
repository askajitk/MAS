from django import forms
from django.forms import inlineformset_factory
from .models import Service, Item, ItemMake

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'other_name']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'class': 'form-select service-type'})
        self.fields['other_name'].widget.attrs.update({
            'class': 'form-control other-service',
            'style': 'display: none;'
        })

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        other_name = cleaned_data.get('other_name')

        if name == 'Other' and not other_name:
            raise forms.ValidationError('Please specify the other service name.')

        return cleaned_data

class ItemForm(forms.ModelForm):
    makes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control makes-input', 'rows': 3}),
        help_text='Enter multiple makes separated by commas',
        required=False
    )

    class Meta:
        model = Item
        fields = ['service', 'name', 'makes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['service'].widget.attrs.update({'class': 'form-select'})
        self.fields['name'].widget.attrs.update({'class': 'form-control'})
        
        if self.instance.pk:
            # If editing existing item, populate makes
            makes = self.instance.makes.all()
            self.fields['makes'].initial = ', '.join(make.name for make in makes)

    def save(self, commit=True):
        item = super().save(commit=commit)
        
        if commit:
            # Handle makes
            makes_text = self.cleaned_data.get('makes', '')
            makes = [make.strip() for make in makes_text.split(',') if make.strip()]
            
            # Delete existing makes not in the new list
            item.makes.exclude(name__in=makes).delete()
            
            # Add new makes
            existing_makes = set(make.name for make in item.makes.all())
            for make in makes:
                if make not in existing_makes:
                    ItemMake.objects.create(item=item, name=make)
        
        return item

class ItemMakeForm(forms.ModelForm):
    class Meta:
        model = ItemMake
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

ItemMakeFormSet = inlineformset_factory(
    Item, ItemMake, 
    form=ItemMakeForm,
    extra=1,
    can_delete=True
)