from typing import Any, Dict
from rest_framework import viewsets, filters, serializers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import CustomUser
from ..models import Project


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for project relationships."""
    
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name']


class ProjectSerializer(serializers.ModelSerializer):
    """Serializer for Project model."""
    
    owner_detail = UserSerializer(source='owner', read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'code', 'name', 'description', 'owner', 'owner_detail',
            'is_active', 'task_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_task_count(self, obj: Project) -> int:
        """Return the count of tasks for this project."""
        return obj.tasks.count()
    
    def validate_code(self, value: str) -> str:
        """Validate project code format."""
        if not value or not value.strip():
            raise serializers.ValidationError("Project code cannot be empty.")
        
        normalized_code = value.strip().upper()
        
        if len(normalized_code) != 3:
            raise serializers.ValidationError("Project code must be exactly 3 characters long.")
        
        if not normalized_code.isalpha():
            raise serializers.ValidationError("Project code can only contain letters.")
        
        # Check uniqueness (case-insensitive)
        existing_project = Project.objects.filter(code__iexact=normalized_code)
        if self.instance:
            existing_project = existing_project.exclude(pk=self.instance.pk)
        
        if existing_project.exists():
            raise serializers.ValidationError("A project with this code already exists.")
        
        return normalized_code
    
    def validate_name(self, value: str) -> str:
        """Validate project name."""
        if not value or not value.strip():
            raise serializers.ValidationError("Project name cannot be empty.")
        
        stripped_name = value.strip()
        
        if len(stripped_name) < 3:
            raise serializers.ValidationError("Project name must be at least 3 characters long.")
        
        if len(stripped_name) > 100:
            raise serializers.ValidationError("Project name cannot exceed 100 characters.")
        
        return stripped_name


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.
    
    Supports filtering by:
    - is_active: Filter by active/inactive projects
    - owner: Filter by owner user ID
    """
    
    queryset = Project.objects.all().select_related('owner')
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['is_active', 'owner']
    search_fields = ['code', 'name', 'description']
    ordering_fields = ['code', 'name', 'created_at', 'updated_at']
    ordering = ['code']  # Default ordering