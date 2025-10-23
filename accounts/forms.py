from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    level = forms.CharField(max_length=50, required=True)
    department = forms.ChoiceField(choices=get_user_model().DEPARTMENT_CHOICES)
    other_department = forms.CharField(max_length=100, required=False)

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'department', 'other_department', 'level']

    def clean(self):
        cleaned_data = super().clean()
        department = cleaned_data.get('department')
        other_department = cleaned_data.get('other_department')

        if department == 'Other' and not other_department:
            raise forms.ValidationError('Please specify the other department.')

        return cleaned_data

class CustomAuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError('This account is inactive.')