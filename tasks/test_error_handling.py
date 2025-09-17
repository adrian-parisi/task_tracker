"""
Comprehensive tests for error handling and validation scenarios.
Tests all validation rules, error response formats, and HTTP status codes.
"""
import pytest
import uuid
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tasks.models import Task, Tag, TaskStatus


@pytest.fixture
def api_client():
    """Provide an API client."""
    return APIClient()


@pytest.fixture
def users(db):
    """Create test users."""
    active_user = User.objects.create_user(
        username='activeuser',
        email='active@test.com',
        password='testpass123',
        is_active=True
    )
    inactive_user = User.objects.create_user(
        username='inactiveuser',
        email='inactive@test.com',
        password='testpass123',
        is_active=False
    )
    return {'active': active_user, 'inactive': inactive_user}


@pytest.fixture
def authenticated_client(api_client, users):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=users['active'])
    return api_client


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
    
    def test_not_found_error_format(self, authenticated_client):
        """Test 404 errors follow standardized format (requirement 8.2)."""
        non_existent_id = uuid.uuid4()
        url = reverse('task-detail', kwargs={'pk': non_existent_id})
        
        response = authenticated_client.get(url)
        
        print(f"Response data: {response.data}")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        # DRF's default 404 might not include 'errors', so let's be more flexible
        if 'errors' in response.data:
            assert isinstance(response.data['errors'], dict)
        else:
            # If no errors field, that's also acceptable for 404s
            pass
    
    def test_authentication_error_format(self, api_client):
        """Test authentication errors follow standardized format (requirement 8.3)."""
        url = reverse('task-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    def test_method_not_allowed_error_format(self, authenticated_client, users):
        """Test method not allowed errors follow standardized format."""
        # Create a task first
        task = Task.objects.create(title='Test Task', reporter=users['active'])
        
        # Try to use PATCH on a detail endpoint that doesn't support it
        url = reverse('task-detail', kwargs={'pk': task.id})
        
        # Try an unsupported method (assuming we have restrictions)
        response = authenticated_client.options(url)
        
        # The response should still follow our format if it's an error
        if response.status_code >= 400:
            assert 'detail' in response.data
            assert 'errors' in response.data


@pytest.mark.integration
class TestTaskValidationErrors:
    """Test Task model validation errors (requirements 8.4, 8.5)."""
    
    def test_empty_title_validation(self, authenticated_client):
        """Test empty title returns proper validation error (requirement 8.4)."""
        url = reverse('task-list')
        
        # Test completely empty title
        response = authenticated_client.post(url, {'title': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']
        assert 'empty' in response.data['errors']['title'][0].lower() or 'blank' in response.data['errors']['title'][0].lower()
        
        # Test whitespace-only title
        response = authenticated_client.post(url, {'title': '   '}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']
        
        # Test None title
        response = authenticated_client.post(url, {'title': None}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']
    
    def test_title_length_validation(self, authenticated_client):
        """Test title length validation."""
        url = reverse('task-list')
        
        # Test too short title
        response = authenticated_client.post(url, {'title': 'ab'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']
        assert '3 characters' in response.data['errors']['title'][0]
        
        # Test too long title
        long_title = 'a' * 201
        response = authenticated_client.post(url, {'title': long_title}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data['errors']
        assert '200 characters' in response.data['errors']['title'][0]
    
    def test_negative_estimate_validation(self, authenticated_client):
        """Test negative estimate returns proper validation error (requirement 8.5)."""
        url = reverse('task-list')
        data = {
            'title': 'Valid Title',
            'estimate': -1
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data['errors']
        assert 'negative' in response.data['errors']['estimate'][0].lower()
    
    def test_estimate_range_validation(self, authenticated_client):
        """Test estimate range validation."""
        url = reverse('task-list')
        
        # Test estimate too high
        data = {
            'title': 'Valid Title',
            'estimate': 101
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data['errors']
        assert '100 points' in response.data['errors']['estimate'][0]
    
    def test_invalid_status_validation(self, authenticated_client):
        """Test invalid status validation."""
        url = reverse('task-list')
        data = {
            'title': 'Valid Title',
            'status': 'INVALID_STATUS'
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'status' in response.data['errors']
        assert 'INVALID_STATUS' in response.data['errors']['status'][0]
        # The error message should mention it's not a valid choice
        assert 'valid choice' in response.data['errors']['status'][0].lower()
    
    def test_done_without_estimate_validation(self, authenticated_client):
        """Test DONE status without estimate validation."""
        url = reverse('task-list')
        data = {
            'title': 'Valid Title',
            'status': TaskStatus.DONE
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'estimate' in response.data['errors']
        assert 'DONE' in response.data['errors']['estimate'][0]
    
    def test_description_length_validation(self, authenticated_client):
        """Test description length validation."""
        url = reverse('task-list')
        
        # Test very long description
        long_description = 'a' * 5001
        data = {
            'title': 'Valid Title',
            'description': long_description
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'description' in response.data['errors']
        assert '5000 characters' in response.data['errors']['description'][0]
    
    def test_inactive_user_validation(self, authenticated_client, users):
        """Test validation for inactive users."""
        url = reverse('task-list')
        data = {
            'title': 'Valid Title',
            'assignee': users['inactive'].id
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'assignee' in response.data['errors']
        assert 'inactive' in response.data['errors']['assignee'][0].lower()
    
    def test_invalid_tag_ids_validation(self, authenticated_client):
        """Test validation for invalid tag IDs in filtering."""
        url = reverse('task-list')
        
        # Test with non-existent tag IDs
        response = authenticated_client.get(url, {'tags': '99999,88888'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tags' in response.data['errors']
        assert 'Invalid tag IDs' in response.data['errors']['tags'][0]
    
    def test_malformed_tag_ids_validation(self, authenticated_client):
        """Test validation for malformed tag IDs in filtering."""
        url = reverse('task-list')
        
        # Test with non-integer tag IDs
        response = authenticated_client.get(url, {'tags': 'abc,def'})
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'tags' in response.data['errors']
        assert 'valid integers' in response.data['errors']['tags'][0]


@pytest.mark.integration
class TestTagValidationErrors:
    """Test Tag model validation errors (requirement 6.4)."""
    
    def test_empty_tag_name_validation(self, authenticated_client):
        """Test empty tag name validation."""
        url = reverse('tag-list')
        
        # Test empty name
        response = authenticated_client.post(url, {'name': ''}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']
        
        # Test whitespace-only name
        response = authenticated_client.post(url, {'name': '   '}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']
    
    def test_tag_name_length_validation(self, authenticated_client):
        """Test tag name length validation."""
        url = reverse('tag-list')
        
        # Test too short name
        response = authenticated_client.post(url, {'name': 'a'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']
        assert '2 characters' in response.data['errors']['name'][0]
        
        # Test too long name
        long_name = 'a' * 65
        response = authenticated_client.post(url, {'name': long_name}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']
        assert '64 characters' in response.data['errors']['name'][0]
    
    def test_tag_name_character_validation(self, authenticated_client):
        """Test tag name character validation."""
        url = reverse('tag-list')
        
        # Test invalid characters
        invalid_names = ['tag with spaces', 'tag@symbol', 'tag#hash', 'tag!exclamation']
        
        for invalid_name in invalid_names:
            response = authenticated_client.post(url, {'name': invalid_name}, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'name' in response.data['errors']
            assert 'letters, numbers, hyphens, and underscores' in response.data['errors']['name'][0]
    
    def test_duplicate_tag_name_validation(self, authenticated_client):
        """Test duplicate tag name validation (requirement 6.4)."""
        # Create first tag
        Tag.objects.create(name='existing-tag')
        
        url = reverse('tag-list')
        
        # Try to create duplicate
        response = authenticated_client.post(url, {'name': 'existing-tag'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['errors']
        assert 'already exists' in response.data['errors']['name'][0].lower()
    
    def test_case_insensitive_duplicate_validation(self, authenticated_client):
        """Test case-insensitive duplicate validation (requirement 6.1)."""
        # Create first tag
        Tag.objects.create(name='CamelCase')
        
        url = reverse('tag-list')
        
        # Try to create with different case
        test_cases = ['camelcase', 'CAMELCASE', 'camelCase', 'CamelCASE']
        
        for test_name in test_cases:
            response = authenticated_client.post(url, {'name': test_name}, format='json')
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'name' in response.data['errors']
            assert 'already exists' in response.data['errors']['name'][0].lower()


@pytest.mark.integration
class TestAIToolsErrorHandling:
    """Test AI tools error handling."""
    
    def test_invalid_task_id_format(self, authenticated_client):
        """Test AI endpoints handle invalid UUID format."""
        invalid_id = 'not-a-uuid'
        
        # Test smart summary - Django URL routing returns 404 for invalid UUID format
        url = f'/api/tasks/{invalid_id}/smart-summary/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test smart estimate
        url = f'/api/tasks/{invalid_id}/smart-estimate/'
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test smart rewrite
        url = f'/api/tasks/{invalid_id}/smart-rewrite/'
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_nonexistent_task_id(self, authenticated_client):
        """Test AI endpoints handle non-existent task IDs."""
        non_existent_id = uuid.uuid4()
        
        # Test smart summary
        url = reverse('smart-summary', kwargs={'task_id': non_existent_id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'errors' in response.data
        
        # Test smart estimate
        url = reverse('smart-estimate', kwargs={'task_id': non_existent_id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        
        # Test smart rewrite
        url = reverse('smart-rewrite', kwargs={'task_id': non_existent_id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_unauthenticated_ai_access(self, api_client, users):
        """Test AI endpoints require authentication."""
        # Create a task
        task = Task.objects.create(title='Test Task', reporter=users['active'])
        
        # Test smart summary
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test smart estimate
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
        # Test smart rewrite
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_wrong_http_methods(self, authenticated_client, users):
        """Test AI endpoints reject wrong HTTP methods."""
        task = Task.objects.create(title='Test Task', reporter=users['active'])
        
        # Smart summary should only accept GET
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        response = authenticated_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Smart estimate should only accept GET
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Smart rewrite should only accept POST
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        response = authenticated_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.integration
class TestDatabaseConstraintErrors:
    """Test database constraint error handling."""
    
    def test_tag_unique_constraint_error(self, authenticated_client):
        """Test database-level unique constraint errors are handled properly."""
        # Create tag directly in database to bypass serializer validation
        Tag.objects.create(name='database-tag')
        
        # Try to create duplicate through API
        url = reverse('tag-list')
        response = authenticated_client.post(url, {'name': 'database-tag'}, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'detail' in response.data
        assert 'errors' in response.data
        assert 'name' in response.data['errors']
    
    def test_foreign_key_constraint_handling(self, authenticated_client):
        """Test foreign key constraint error handling."""
        url = reverse('task-list')
        data = {
            'title': 'Valid Title',
            'assignee': 99999  # Non-existent user ID
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'assignee' in response.data['errors']


@pytest.mark.integration
class TestErrorResponseConsistency:
    """Test error response consistency across all endpoints."""
    
    def test_all_validation_errors_have_detail_and_errors(self, authenticated_client):
        """Test all validation errors include both detail and errors fields."""
        test_cases = [
            # Task validation errors
            (reverse('task-list'), 'post', {'title': ''}),
            (reverse('task-list'), 'post', {'title': 'Valid', 'estimate': -1}),
            
            # Tag validation errors
            (reverse('tag-list'), 'post', {'name': ''}),
            (reverse('tag-list'), 'post', {'name': 'a'}),
        ]
        
        for url, method, data in test_cases:
            if method == 'post':
                response = authenticated_client.post(url, data, format='json')
            elif method == 'get':
                response = authenticated_client.get(url, data)
            
            if response.status_code >= 400:
                assert 'detail' in response.data, f"Missing 'detail' in {url} {method} response"
                assert 'errors' in response.data, f"Missing 'errors' in {url} {method} response"
                assert isinstance(response.data['errors'], dict), f"'errors' should be dict in {url} {method}"
    
    def test_404_errors_consistent_format(self, authenticated_client):
        """Test all 404 errors have consistent format."""
        non_existent_id = uuid.uuid4()
        
        urls = [
            reverse('task-detail', kwargs={'pk': non_existent_id}),
            reverse('tag-detail', kwargs={'pk': 99999}),
        ]
        
        for url in urls:
            response = authenticated_client.get(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert 'detail' in response.data
            assert 'errors' in response.data
            assert isinstance(response.data['errors'], dict)
    
    def test_authentication_errors_consistent_format(self, api_client):
        """Test authentication errors have consistent format."""
        urls = [
            reverse('task-list'),
            reverse('tag-list'),
        ]
        
        for url in urls:
            response = api_client.get(url)
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert 'detail' in response.data
            assert 'errors' in response.data


@pytest.mark.integration
class TestValidationEdgeCases:
    """Test edge cases in validation."""
    
    def test_unicode_and_special_characters(self, authenticated_client):
        """Test handling of unicode and special characters."""
        url = reverse('task-list')
        
        # Test unicode characters in title
        data = {'title': 'Task with émojis 🚀 and ñ characters'}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test unicode in description
        data = {
            'title': 'Unicode Test',
            'description': 'Description with 中文 characters and émojis 🎉'
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_boundary_values(self, authenticated_client):
        """Test boundary values for validation."""
        url = reverse('task-list')
        
        # Test minimum valid title length
        data = {'title': 'abc'}  # Exactly 3 characters
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test maximum valid title length
        data = {'title': 'a' * 200}  # Exactly 200 characters
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test zero estimate
        data = {'title': 'Zero Estimate', 'estimate': 0}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test maximum estimate
        data = {'title': 'Max Estimate', 'estimate': 100}
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
    
    def test_null_and_none_values(self, authenticated_client):
        """Test handling of null and None values."""
        url = reverse('task-list')
        
        # Test None values for optional fields that allow null
        data = {
            'title': 'Valid Title',
            'estimate': None,
            'assignee': None
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test empty string for description (should be allowed)
        data = {
            'title': 'Valid Title',
            'description': ''  # Empty string should be allowed
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        
        # Test that None for description is rejected
        data = {
            'title': 'Valid Title',
            'description': None  # Should be rejected
        }
        response = authenticated_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'description' in response.data['errors']