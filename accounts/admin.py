from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm
from .models import CustomUser

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser

class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', 'email', 'department', 'level', 'is_staff']
    list_filter = ['department', 'level', 'is_staff']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Information', {'fields': ('department', 'other_department', 'level')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Information', {'fields': ('department', 'other_department', 'level')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
