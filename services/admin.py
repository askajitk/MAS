from django.contrib import admin
from .models import Service, Item, ItemMake, ServiceLog

class ItemMakeInline(admin.TabularInline):
    model = ItemMake
    extra = 1

class ItemAdmin(admin.ModelAdmin):
    inlines = [ItemMakeInline]
    list_display = ['name', 'service']
    list_filter = ['service']
    search_fields = ['name']

class ItemInline(admin.TabularInline):
    model = Item
    extra = 1

class ServiceAdmin(admin.ModelAdmin):
    inlines = [ItemInline]
    list_display = ['name', 'other_name']
    search_fields = ['name', 'other_name']

class ServiceLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'content_type', 'details']
    list_filter = ['action', 'content_type', 'user']
    search_fields = ['details', 'user__username']
    readonly_fields = ['timestamp', 'user', 'action', 'content_type', 'object_id', 'details']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False

admin.site.register(Service, ServiceAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ServiceLog, ServiceLogAdmin)
