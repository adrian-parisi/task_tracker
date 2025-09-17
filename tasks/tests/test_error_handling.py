"""
Comprehensive tests for error handling and validation scenarios.
Tests all validation rules, error response formats, and HTTP status codes.
"""
import pytest
import uuid
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from tasks.models import Task, Tag, TaskStatus

User = get_user_model()


# Fixtures are now in conftest.py


@pytest.mark.integration
class TestStandardizedErrorFormat:
    """Test standardized error response format (requirement 8.1)."""
    
    def test_validation_error_format(self, authenticated_client):
        """Test validation errors follow standardized format."""
        url = reverse('task-list')
        data = {
            'title': '',  # Invalid: empty title
            'estimate': -5,  # Invalid: negative estimate
            'status': 'INVALID_STATUS'  # Invalid: not a valid choice
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert 'errors' in response.data
        assert isinstance(response.data['errors'], dict)
        
        # Check specific field errors
        errors = response.data['errors']
        assert 'title' in errors
        assert 'estimate' in errors
        assert 'status' in errors
        
        # Each field should have a list of error messages
        assert isinstance(errors['title'], list)
        assert isinstance(errors['estimate'], list)
        assert isinstance(errors['status'], list)
    
    # ... rest of the test methods would continue here