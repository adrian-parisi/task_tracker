from typing import Any, Dict
from rest_framework import serializers
from accounts.models import CustomUser
from .models import Task, Tag, TaskStatus


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model with case-insensitive validation."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']
    
    def validate_name(self, value: str) -> str:
        """Validate tag name with case-insensitive uniqueness check."""
        if not value or not value.strip():
            raise serializers.ValidationError("Tag name cannot be empty or just whitespace.")
        
        # Normalize the name
        normalized_name = value.strip()
        
        # Length validation
        if len(normalized_name) < 2:
            raise serializers.ValidationError("Tag name must be at least 2 characters long.")
        
        if len(normalized_name) > 64:
            raise serializers.ValidationError("Tag name cannot exceed 64 characters.")
        
        # Character validation
        allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        if not all(char in allowed_chars for char in normalized_name):
            raise serializers.ValidationError(
                "Tag name can only contain letters, numbers, hyphens, and underscores."
            )
        
        # Check case-insensitive uniqueness (requirement 6.1)
        existing_tag = Tag.objects.filter(name__iexact=normalized_name)
        
        # If updating, exclude current instance
        if self.instance:
            existing_tag = existing_tag.exclude(pk=self.instance.pk)
        
        if existing_tag.exists():
            raise serializers.ValidationError("A tag with this name already exists (case-insensitive).")
        
        return normalized_name


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for task relationships."""
    
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name']


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
    assignee_detail = UserSerializer(source='assignee', read_only=True)
    reporter_detail = UserSerializer(source='reporter', read_only=True)
    tags_detail = TagSerializer(source='tags', many=True, read_only=True)
    
    # Write-only fields for relationships
    assignee = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    reporter = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        required=False,
        allow_null=True,
        write_only=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False,
        write_only=True
    )
    
    # Activity count for UI consumption (requirement 9.4)
    activity_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'status', 'estimate',
            'assignee', 'reporter', 'tags',
            'assignee_detail', 'reporter_detail', 'tags_detail',
            'activity_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
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
        """Create a new task with proper tag handling."""
        tags_data = validated_data.pop('tags', [])
        task = Task.objects.create(**validated_data)
        task.tags.set(tags_data)
        return task
    
    def update(self, instance: Task, validated_data: Dict[str, Any]) -> Task:
        """Update task with proper tag handling."""
        tags_data = validated_data.pop('tags', None)
        
        # Update all other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update tags if provided
        if tags_data is not None:
            instance.tags.set(tags_data)
        
        return instance


class TaskListSerializer(TaskSerializer):
    """Optimized serializer for task list views."""
    
    class Meta(TaskSerializer.Meta):
        # Exclude activity_count from list view for performance
        fields = [
            'id', 'title', 'description', 'status', 'estimate',
            'assignee_detail', 'reporter_detail', 'tags_detail',
            'created_at', 'updated_at'
        ]