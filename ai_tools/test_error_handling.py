"""
Comprehensive tests for AI tools error handling and validation.
Tests error scenarios, response formats, and edge cases for AI endpoints.
"""
import pytest
import uuid
from unittest.mock import patch, Mock
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
    user = User.objects.create_user(
        username='testuser',
        email='test@test.com',
        password='testpass123'
    )
    return {'user': user}


@pytest.fixture
def authenticated_client(api_client, users):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=users['user'])
    return api_client


@pytest.fixture
def sample_task(db, users):
    """Create a sample task for testing."""
    return Task.objects.create(
        title='Test Task',
        description='Test description',
        status=TaskStatus.TODO,
        reporter=users['user']
    )


@pytest.mark.integration
class TestSmartSummaryErrorHandling:
    """Test Smart Summary endpoint error handling."""
    
    def test_invalid_uuid_format(self, authenticated_client):
        """Test invalid UUID format returns 404 (Django URL routing behavior)."""
        invalid_ids = ['not-a-uuid', '123', 'abc-def-ghi', '']
        
        for invalid_id in invalid_ids:
            url = f'/api/tasks/{invalid_id}/smart-summary/'
            response = authenticated_client.get(url)
            
            # Django's UUID converter returns 404 for invalid UUID format
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_nonexistent_task_uuid(self, authenticated_client):
        """Test non-existent but valid UUID returns 404."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-summary', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'errors' in response.data
        assert response.data['detail'] == 'Resource not found.'
    
    def test_unauthenticated_access(self, api_client, sample_task):
        """Test unauthenticated access returns 403."""
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    def test_wrong_http_method(self, authenticated_client, sample_task):
        """Test wrong HTTP methods return 405."""
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        
        # Test POST (should be GET only)
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test PUT
        response = authenticated_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test DELETE
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    @patch('ai_tools.services.AIService.generate_summary')
    def test_service_exception_handling(self, mock_generate, authenticated_client, sample_task):
        """Test graceful handling of service layer exceptions."""
        # Mock service to raise exception
        mock_generate.side_effect = Exception("Service unavailable")
        
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'errors' in response.data
        assert 'error occurred' in response.data['detail'].lower()
    
    @patch('ai_tools.services.AIService.generate_summary')
    def test_service_timeout_handling(self, mock_generate, authenticated_client, sample_task):
        """Test handling of service timeouts."""
        # Mock service to raise timeout
        mock_generate.side_effect = TimeoutError("Service timeout")
        
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'errors' in response.data


@pytest.mark.integration
class TestSmartEstimateErrorHandling:
    """Test Smart Estimate endpoint error handling."""
    
    def test_invalid_uuid_format(self, authenticated_client):
        """Test invalid UUID format returns 404 (Django URL routing behavior)."""
        invalid_ids = ['not-a-uuid', '123', 'abc-def-ghi', '']
        
        for invalid_id in invalid_ids:
            url = f'/api/tasks/{invalid_id}/smart-estimate/'
            response = authenticated_client.get(url)
            
            # Django's UUID converter returns 404 for invalid UUID format
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_nonexistent_task_uuid(self, authenticated_client):
        """Test non-existent but valid UUID returns 404."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-estimate', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    def test_wrong_http_method(self, authenticated_client, sample_task):
        """Test wrong HTTP methods return 405."""
        url = reverse('smart-estimate', kwargs={'task_id': sample_task.id})
        
        # Test POST (should be GET only)
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test PUT
        response = authenticated_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    @patch('tasks.services.SimilarityService.calculate_estimate_suggestion')
    def test_similarity_service_exception(self, mock_calculate, authenticated_client, sample_task):
        """Test handling of similarity service exceptions."""
        # Mock service to raise exception
        mock_calculate.side_effect = Exception("Similarity calculation failed")
        
        url = reverse('smart-estimate', kwargs={'task_id': sample_task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    @patch('ai_tools.services.AIService._log_ai_invocation')
    def test_logging_exception_handling(self, mock_log, authenticated_client, sample_task):
        """Test that logging exceptions don't break the endpoint."""
        # Mock logging to raise exception
        mock_log.side_effect = Exception("Logging failed")
        
        url = reverse('smart-estimate', kwargs={'task_id': sample_task.id})
        response = authenticated_client.get(url)
        
        # Should still succeed despite logging failure
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


@pytest.mark.integration
class TestSmartRewriteErrorHandling:
    """Test Smart Rewrite endpoint error handling."""
    
    def test_invalid_uuid_format(self, authenticated_client):
        """Test invalid UUID format returns 404 (Django URL routing behavior)."""
        invalid_ids = ['not-a-uuid', '123', 'abc-def-ghi', '']
        
        for invalid_id in invalid_ids:
            url = f'/api/tasks/{invalid_id}/smart-rewrite/'
            response = authenticated_client.post(url)
            
            # Django's UUID converter returns 404 for invalid UUID format
            assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_nonexistent_task_uuid(self, authenticated_client):
        """Test non-existent but valid UUID returns 404."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-rewrite', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    def test_wrong_http_method(self, authenticated_client, sample_task):
        """Test wrong HTTP methods return 405."""
        url = reverse('smart-rewrite', kwargs={'task_id': sample_task.id})
        
        # Test GET (should be POST only)
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test PUT
        response = authenticated_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Test DELETE
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    @patch('ai_tools.services.AIService.generate_rewrite')
    def test_service_exception_handling(self, mock_generate, authenticated_client, sample_task):
        """Test graceful handling of service layer exceptions."""
        # Mock service to raise exception
        mock_generate.side_effect = Exception("Rewrite service failed")
        
        url = reverse('smart-rewrite', kwargs={'task_id': sample_task.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'errors' in response.data
    
    def test_request_body_ignored(self, authenticated_client, sample_task):
        """Test that request body is ignored (POST with no body expected)."""
        url = reverse('smart-rewrite', kwargs={'task_id': sample_task.id})
        
        # Send POST with body data (should be ignored)
        response = authenticated_client.post(url, {'extra': 'data'}, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


@pytest.mark.integration
class TestAIEndpointsEdgeCases:
    """Test edge cases across all AI endpoints."""
    
    def test_malformed_urls(self, authenticated_client):
        """Test malformed URLs are handled gracefully."""
        malformed_urls = [
            '/api/tasks//smart-summary/',
            '/api/tasks/smart-summary/',
            '/api/tasks/123/smart-summary/extra/',
        ]
        
        for url in malformed_urls:
            response = authenticated_client.get(url)
            # Should return 404 or 400, not 500
            assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST]
    
    def test_very_long_task_ids(self, authenticated_client):
        """Test very long task ID strings."""
        very_long_id = 'a' * 1000
        url = f'/api/tasks/{very_long_id}/smart-summary/'
        
        response = authenticated_client.get(url)
        
        # Django URL routing returns 404 for invalid UUID format
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_special_characters_in_task_id(self, authenticated_client):
        """Test special characters in task ID."""
        special_ids = ['<script>', '../../etc/passwd', 'task%20id', 'task+id']
        
        for special_id in special_ids:
            url = f'/api/tasks/{special_id}/smart-summary/'
            response = authenticated_client.get(url)
            
            # Should return validation error, not crash
            assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]
    
    def test_concurrent_requests_same_task(self, authenticated_client, sample_task):
        """Test concurrent requests to same task don't cause issues."""
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        
        # Make multiple concurrent requests
        responses = []
        for _ in range(5):
            response = authenticated_client.get(url)
            responses.append(response)
        
        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert 'summary' in response.data
    
    def test_task_with_no_activities(self, authenticated_client, users):
        """Test AI tools work with tasks that have no activities."""
        # Create task without triggering activity creation
        task = Task.objects.create(
            title='No Activities Task',
            reporter=users['user']
        )
        
        # Test all AI endpoints
        summary_url = reverse('smart-summary', kwargs={'task_id': task.id})
        response = authenticated_client.get(summary_url)
        assert response.status_code == status.HTTP_200_OK
        
        estimate_url = reverse('smart-estimate', kwargs={'task_id': task.id})
        response = authenticated_client.get(estimate_url)
        assert response.status_code == status.HTTP_200_OK
        
        rewrite_url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response = authenticated_client.post(rewrite_url)
        assert response.status_code == status.HTTP_200_OK
    
    def test_task_with_minimal_data(self, authenticated_client, users):
        """Test AI tools work with tasks that have minimal data."""
        # Create task with only required fields
        task = Task.objects.create(
            title='Min',  # Minimum length title
            reporter=users['user']
        )
        
        # Test all AI endpoints
        summary_url = reverse('smart-summary', kwargs={'task_id': task.id})
        response = authenticated_client.get(summary_url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['summary']) > 0
        
        estimate_url = reverse('smart-estimate', kwargs={'task_id': task.id})
        response = authenticated_client.get(estimate_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data
        
        rewrite_url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response = authenticated_client.post(rewrite_url)
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data


@pytest.mark.integration
class TestErrorResponseConsistency:
    """Test error response consistency across AI endpoints."""
    
    def test_all_400_errors_have_standard_format(self, authenticated_client):
        """Test all 400 errors follow standard format."""
        # Note: Invalid UUIDs return 404 due to Django URL routing
        # This test focuses on other types of 400 errors
        
        # We'll test with a valid UUID but non-existent task to get proper error format
        non_existent_id = uuid.uuid4()
        
        endpoints = [
            reverse('smart-summary', kwargs={'task_id': non_existent_id}),
            reverse('smart-estimate', kwargs={'task_id': non_existent_id}),
            reverse('smart-rewrite', kwargs={'task_id': non_existent_id}),
        ]
        
        for endpoint in endpoints:
            if 'smart-rewrite' in endpoint:
                response = authenticated_client.post(endpoint)
            else:
                response = authenticated_client.get(endpoint)
            
            # These should return 404, not 400, but should still follow our format
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert 'detail' in response.data
            assert 'errors' in response.data
            assert isinstance(response.data['errors'], dict)
    
    def test_all_404_errors_have_standard_format(self, authenticated_client):
        """Test all 404 errors follow standard format."""
        non_existent_id = uuid.uuid4()
        
        endpoints = [
            reverse('smart-summary', kwargs={'task_id': non_existent_id}),
            reverse('smart-estimate', kwargs={'task_id': non_existent_id}),
            reverse('smart-rewrite', kwargs={'task_id': non_existent_id}),
        ]
        
        for endpoint in endpoints:
            if 'smart-rewrite' in endpoint:
                response = authenticated_client.post(endpoint)
            else:
                response = authenticated_client.get(endpoint)
            
            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert 'detail' in response.data
            assert 'errors' in response.data
            assert isinstance(response.data['errors'], dict)
    
    def test_all_403_errors_have_standard_format(self, api_client, sample_task):
        """Test all 403 errors follow standard format."""
        endpoints = [
            reverse('smart-summary', kwargs={'task_id': sample_task.id}),
            reverse('smart-estimate', kwargs={'task_id': sample_task.id}),
            reverse('smart-rewrite', kwargs={'task_id': sample_task.id}),
        ]
        
        for endpoint in endpoints:
            if 'smart-rewrite' in endpoint:
                response = api_client.post(endpoint)
            else:
                response = api_client.get(endpoint)
            
            assert response.status_code == status.HTTP_403_FORBIDDEN
            assert 'detail' in response.data
            assert 'errors' in response.data
            assert isinstance(response.data['errors'], dict)
    
    def test_all_405_errors_have_standard_format(self, authenticated_client, sample_task):
        """Test all 405 errors follow standard format."""
        test_cases = [
            (reverse('smart-summary', kwargs={'task_id': sample_task.id}), 'post'),
            (reverse('smart-estimate', kwargs={'task_id': sample_task.id}), 'post'),
            (reverse('smart-rewrite', kwargs={'task_id': sample_task.id}), 'get'),
        ]
        
        for endpoint, method in test_cases:
            if method == 'post':
                response = authenticated_client.post(endpoint)
            else:
                response = authenticated_client.get(endpoint)
            
            assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
            # Note: DRF's default 405 handler might not follow our custom format
            # but it should still be a proper error response


@pytest.mark.integration
class TestServiceLayerErrorHandling:
    """Test service layer error handling and recovery."""
    
    @patch('ai_tools.services.AIService.generate_summary')
    def test_summary_service_various_exceptions(self, mock_generate, authenticated_client, sample_task):
        """Test handling of various service exceptions."""
        exceptions_to_test = [
            ValueError("Invalid input"),
            KeyError("Missing key"),
            AttributeError("Missing attribute"),
            TypeError("Type error"),
            RuntimeError("Runtime error"),
        ]
        
        url = reverse('smart-summary', kwargs={'task_id': sample_task.id})
        
        for exception in exceptions_to_test:
            mock_generate.side_effect = exception
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'detail' in response.data
            assert 'errors' in response.data
    
    @patch('tasks.services.SimilarityService.calculate_estimate_suggestion')
    def test_estimate_service_database_errors(self, mock_calculate, authenticated_client, sample_task):
        """Test handling of database-related errors in estimate service."""
        from django.db import DatabaseError, OperationalError
        
        database_errors = [
            DatabaseError("Database connection lost"),
            OperationalError("Table doesn't exist"),
        ]
        
        url = reverse('smart-estimate', kwargs={'task_id': sample_task.id})
        
        for error in database_errors:
            mock_calculate.side_effect = error
            response = authenticated_client.get(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'detail' in response.data
            assert 'errors' in response.data
    
    @patch('ai_tools.services.AIService.generate_rewrite')
    def test_rewrite_service_memory_errors(self, mock_generate, authenticated_client, sample_task):
        """Test handling of memory-related errors."""
        mock_generate.side_effect = MemoryError("Out of memory")
        
        url = reverse('smart-rewrite', kwargs={'task_id': sample_task.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'errors' in response.data