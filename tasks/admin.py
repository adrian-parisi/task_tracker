from django.contrib import admin
from .models import Task, TaskActivity, Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'owner', 'is_active', 'created_at']
    list_filter = ['is_active', 'owner', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_readonly_fields(self, request, obj=None):
        # Make code readonly after creation to prevent breaking task keys
        if obj:  # Editing existing project
            return self.readonly_fields + ['code']
        return self.readonly_fields


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['key', 'title', 'project', 'status', 'assignee', 'estimate', 'created_at', 'updated_at']
    list_filter = ['status', 'project', 'assignee', 'created_at']
    search_fields = ['key', 'title', 'description']
    readonly_fields = ['id', 'key', 'created_at', 'updated_at']


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
