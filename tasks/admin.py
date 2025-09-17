from django.contrib import admin
from .models import Task, TaskActivity, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'assignee', 'estimate', 'created_at', 'updated_at']
    list_filter = ['status', 'assignee', 'tags', 'created_at']
    search_fields = ['title', 'description']
    filter_horizontal = ['tags']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(TaskActivity)
class TaskActivityAdmin(admin.ModelAdmin):
    list_display = ['task', 'type', 'field', 'actor', 'created_at']
    list_filter = ['type', 'created_at']
    readonly_fields = ['task', 'actor', 'type', 'field', 'before', 'after', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
