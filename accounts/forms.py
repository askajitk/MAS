from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

from crispy_forms.helper import FormHelper

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=get_user_model().USER_TYPE_CHOICES, required=True)
    department = forms.ChoiceField(choices=get_user_model().DEPARTMENT_CHOICES)
    other_department = forms.CharField(max_length=100, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.template = 'accounts/custom_signup_form.html'
        # Remove default password help text since we show requirements inline
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password1', 'password2', 'department', 'other_department', 'user_type']

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