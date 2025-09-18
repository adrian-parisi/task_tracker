from typing import Any, Dict
from rest_framework import viewsets, status, filters, serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.exceptions import ValidationError
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import CustomUser
from ..models import Task, Project, TaskStatus


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for task relationships."""
    
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name']


class ProjectSerializer(serializers.ModelSerializer):
    """Basic project serializer for task relationships."""
    
    class Meta:
        model = Project
        fields = ['id', 'code', 'name']
        read_only_fields = ['id', 'code', 'name']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model with proper field validation."""
    
    # Custom title field with proper validation
    title = serializers.CharField(
        max_length=200,
        required=True,
        allow_blank=False,
        error_messages={
            'blank': 'Task title cannot be empty or just whitespace.',
            'required': 'Task title is required.',
            'max_length': 'Task title cannot exceed 200 characters.'
        }
    )
    
    # Nested serializers for read operations
    project_detail = ProjectSerializer(source='project', read_only=True)
    assignee_detail = UserSerializer(source='assignee', read_only=True)
    reporter_detail = UserSerializer(source='reporter', read_only=True)
    
    # Write-only fields for relationships
    project = serializers.PrimaryKeyRelatedField(
        queryset=Project.objects.filter(is_active=True),
        required=True
    )
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    reporter = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=64),
        required=False,
        help_text="Array of tag names as strings"
    )
    
    # Activity count for UI consumption (requirement 9.4)
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'key', 'project', 'project_detail', 'title', 'description', 'status', 'estimate',
            'assignee', 'reporter', 'tags',
            'assignee_detail', 'reporter_detail',
            'activity_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'key', 'created_at', 'updated_at']
        extra_kwargs = {
            'assignee': {'write_only': True},
            'reporter': {'write_only': True},
            'project': {'write_only': True}
        }
    
    def get_activity_count(self, obj: Task) -> int:
        """Return the count of activities for this task."""
        return obj.activities.count()
    
    def validate_title(self, value: str) -> str:
        """Validate task title is not empty (requirement 8.4)."""
        if not value or not value.strip():
            raise serializers.ValidationError("Task title cannot be empty or just whitespace.")
        
        stripped_title = value.strip()
        
        # Length validation
        if len(stripped_title) < 3:
            raise serializers.ValidationError("Task title must be at least 3 characters long.")
        
        if len(stripped_title) > 200:
            raise serializers.ValidationError("Task title cannot exceed 200 characters.")
        
        return stripped_title
    
    def validate_estimate(self, value: int | None) -> int | None:
        """Validate estimate is not negative (requirement 8.5)."""
        if value is not None:
            if value < 0:
                raise serializers.ValidationError("Task estimate cannot be negative.")
            if value > 100:
                raise serializers.ValidationError("Task estimate cannot exceed 100 points.")
        return value
    
    def validate_status(self, value: str) -> str:
        """Validate status is a valid choice."""
        if value not in [choice[0] for choice in TaskStatus.choices]:
            valid_choices = [choice[0] for choice in TaskStatus.choices]
            raise serializers.ValidationError(
                f"Invalid status '{value}'. Must be one of: {valid_choices}"
            )
        return value
    
    def validate_description(self, value: str | None) -> str | None:
        """Validate task description length."""
        if value and len(value) > 5000:
            raise serializers.ValidationError("Task description cannot exceed 5000 characters.")
        return value
    
    def validate_assignee(self, value: CustomUser | None) -> CustomUser | None:
        """Validate assignee exists and is active."""
        if value is not None:
            if not value.is_active:
                raise serializers.ValidationError("Cannot assign task to inactive user.")
        return value
    
    def validate_reporter(self, value: CustomUser | None) -> CustomUser | None:
        """Validate reporter exists and is active."""
        if value is not None:
            if not value.is_active:
                raise serializers.ValidationError("Reporter must be an active user.")
        return value
    
    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform cross-field validation."""
        # Business rule: Task cannot be marked as DONE without an estimate
        status = attrs.get('status')
        estimate = attrs.get('estimate')
        
        # If we're updating, get current values if not provided
        if self.instance:
            if status is None:
                status = self.instance.status
            if estimate is None:
                estimate = self.instance.estimate
        
        if status == TaskStatus.DONE and estimate is None:
            raise serializers.ValidationError({
                'estimate': 'Tasks marked as DONE must have an estimate.'
            })
        
        return attrs
    
    def create(self, validated_data: Dict[str, Any]) -> Task:
        """Create a new task with tags as array field."""
        # Normalize tag names (trim whitespace and filter empty ones)
        if 'tags' in validated_data:
            validated_data['tags'] = [
                tag.strip() for tag in validated_data['tags'] 
                if tag and tag.strip()
            ]
        
        # Create the task directly - tags are now just an array field
        return Task.objects.create(**validated_data)
    
    def update(self, instance: Task, validated_data: Dict[str, Any]) -> Task:
        """Update task with tags as array field."""
        # Normalize tag names if provided
        if 'tags' in validated_data and validated_data['tags'] is not None:
            validated_data['tags'] = [
                tag.strip() for tag in validated_data['tags'] 
                if tag and tag.strip()
            ]
        
        # Update all fields including tags
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class TaskListSerializer(TaskSerializer):
    """Optimized serializer for task list views."""
    
    class Meta(TaskSerializer.Meta):
        # Exclude activity_count from list view for performance
        fields = [
            'id', 'key', 'project_detail', 'title', 'description', 'status', 'estimate',
            'assignee_detail', 'reporter_detail', 'tags',
            'created_at', 'updated_at'
        ]


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations with filtering and pagination.
    
    Supports filtering by:
    - status: Filter by task status (TODO, IN_PROGRESS, BLOCKED, DONE)
    - project: Filter by project ID
    - assignee: Filter by assignee user ID
    - tags: Filter by tag IDs (comma-separated)
    
    Supports pagination with default 20 items per page, max 100.
    """
    
    queryset = Task.objects.all().select_related('project', 'assignee', 'reporter')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'project', 'assignee']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-updated_at']  # Default ordering
    
    def get_serializer_class(self) -> type[TaskSerializer | TaskListSerializer]:
        """Use optimized serializer for list view."""
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new task (requirement 4.1)."""
        # Set reporter to current user if not provided
        data = request.data.copy()
        if 'reporter' not in data:
            data['reporter'] = request.user.id
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Set current user for activity logging
        task = serializer.save()
        task._current_user = request.user
        task.save()  # Trigger activity logging
        
        # Return full task data with nested relationships
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a task (requirement 4.2)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Set current user for activity logging
        instance._current_user = request.user
        task = serializer.save()
        
        # Return full task data with nested relationships
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data)
    
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a task with hard delete (requirement 4.5)."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)