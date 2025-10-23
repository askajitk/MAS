from django import forms
from .models import Service, Item, ItemMake

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['name', 'other_name']

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        other_name = cleaned_data.get('other_name')

        if name == 'Other' and not other_name:
            raise forms.ValidationError('Please specify the other service name.')

        return cleaned_data

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['service', 'name']

class ItemMakeForm(forms.ModelForm):
    class Meta:
        model = ItemMake
        fields = ['item', 'name']

class ServiceItemFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        if not any(cleaned_data and not cleaned_data.get('DELETE', False)
                  for cleaned_data in self.cleaned_data):
            raise forms.ValidationError('At least one item is required.')