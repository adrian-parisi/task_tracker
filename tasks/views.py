from typing import Any
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django_filters.rest_framework import DjangoFilterBackend
from accounts.models import CustomUser
from .models import Task, Tag
from .serializers import TaskSerializer, TaskListSerializer, TagSerializer


class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Task CRUD operations with filtering and pagination.
    
    Supports filtering by:
    - status: Filter by task status (TODO, IN_PROGRESS, BLOCKED, DONE)
    - assignee: Filter by assignee user ID
    - tags: Filter by tag IDs (comma-separated)
    
    Supports pagination with default 20 items per page, max 100.
    """
    
    queryset = Task.objects.all().select_related('assignee', 'reporter').prefetch_related('tags')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'assignee']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-updated_at']  # Default ordering
    
    def get_serializer_class(self) -> type[TaskSerializer | TaskListSerializer]:
        """Use optimized serializer for list view."""
        if self.action == 'list':
            return TaskListSerializer
        return TaskSerializer
    
    def get_queryset(self) -> Any:
        """Apply custom filtering for tags."""
        queryset = super().get_queryset()
        
        # Filter by tags (requirement 4.3)
        tags = self.request.query_params.get('tags', None)
        if tags:
            try:
                tag_ids = [int(tag_id.strip()) for tag_id in tags.split(',') if tag_id.strip()]
                if tag_ids:
                    # Validate that all tag IDs exist
                    from .models import Tag
                    existing_tag_ids = set(Tag.objects.filter(id__in=tag_ids).values_list('id', flat=True))
                    invalid_tag_ids = set(tag_ids) - existing_tag_ids
                    
                    if invalid_tag_ids:
                        from rest_framework.exceptions import ValidationError
                        raise ValidationError({
                            'tags': [f'Invalid tag IDs: {list(invalid_tag_ids)}']
                        })
                    
                    queryset = queryset.filter(tags__id__in=tag_ids).distinct()
            except ValueError as e:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'tags': ['Tag IDs must be valid integers separated by commas.']
                })
        
        return queryset
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new task (requirement 4.1)."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set reporter to current user if not provided
        if 'reporter' not in serializer.validated_data:
            serializer.validated_data['reporter'] = request.user
        
        task = serializer.save()
        
        # Return full task data with nested relationships
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a task (requirement 4.2)."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        task = serializer.save()
        
        # Return full task data with nested relationships
        response_serializer = TaskSerializer(task)
        return Response(response_serializer.data)
    
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a task with hard delete (requirement 4.5)."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tag CRUD operations.
    
    Provides:
    - List tags sorted by name (requirement 6.2)
    - Create new tags with case-insensitive uniqueness (requirement 6.1)
    - Update existing tags
    - Delete tags
    - Proper error handling for duplicate names (requirement 6.4)
    """
    
    queryset = Tag.objects.all().order_by('name')  # Name-based sorting (requirement 6.2)
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['name']  # Default ordering by name
    
    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new tag with proper validation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # The custom exception handler will handle any IntegrityError
        tag = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Update a tag with proper validation."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # The custom exception handler will handle any IntegrityError
        tag = serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a tag."""
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
