from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from django.db.models import Q
from ..models import CustomUser


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model with search functionality and display name."""
    
    display_name = serializers.ReadOnlyField()
    
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name', 'display_name']
        read_only_fields = ['id', 'username', 'first_name', 'last_name', 'display_name']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User search and listing operations.
    
    Provides:
    - List active users
    - Search users by username, first_name, and last_name
    - Read-only operations (users should not be created/modified through task API)
    
    Supports filtering by:
    - search: Search across username, first_name, and last_name (case-insensitive)
    """
    
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name']
    ordering_fields = ['username', 'first_name', 'last_name']
    ordering = ['username']  # Default ordering
    
    def get_queryset(self):
        """Return only active users."""
        return CustomUser.objects.filter(is_active=True)
