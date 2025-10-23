from django.contrib import admin
from .models import MAS, MASActivityLog

@admin.register(MAS)
class MASAdmin(admin.ModelAdmin):
    list_display = ['mas_id', 'revision', 'project', 'building', 'service', 'item', 'make', 'status', 'creator', 'created_at']
    list_filter = ['status', 'project', 'building', 'service', 'created_at']
    search_fields = ['mas_id', 'make', 'creator__username']
    readonly_fields = ['mas_id', 'serial_number', 'revision', 'created_at', 'updated_at']
    
@admin.register(MASActivityLog)
class MASActivityLogAdmin(admin.ModelAdmin):
    list_display = ['mas', 'action', 'user', 'timestamp', 'project_name', 'building_name', 'status']
    list_filter = ['action', 'timestamp', 'status']
    search_fields = ['mas__mas_id', 'user__username', 'project_name', 'building_name', 'details']
    readonly_fields = ['mas', 'action', 'user', 'timestamp', 'details', 'project_name', 'building_name', 'service_name', 'item_name', 'make', 'status']
    date_hierarchy = 'timestamp'
