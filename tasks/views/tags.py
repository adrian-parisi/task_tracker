from typing import Any
import string
from rest_framework import viewsets, status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from ..models import Tag


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
        allowed_chars = set(string.ascii_letters + string.digits + '-_')
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
