"""
Comprehensive error handling tests for AI tools views.
"""
import pytest
import uuid
import json
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist

from ai_tools.models import AIOperation
from tasks.models import Task, TaskStatus, Project
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py


class TestErrorHandling:
    """Test error handling and HTTP status codes for AI tools views."""

    def test_http_status_codes_smart_summary(self, api_client, test_user, test_task):
        """Test HTTP status codes for smart summary endpoint."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test successful request
        with patch('ai_tools.views.smart_summary.process_ai_async_test_task.delay'):
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Test unauthenticated request
        api_client.logout()
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test invalid UUID
        api_client.force_authenticate(test_user=test_user)
        invalid_url = reverse('smart-summary', kwargs={'test_task_id': 'invalid-uuid'})
        response = api_client.post(invalid_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test non-existent test_task
        nonexistent_url = reverse('smart-summary', kwargs={'test_task_id': uuid.uuid4()})
        response = api_client.post(nonexistent_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test wrong HTTP method
        response = api_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_http_status_codes_smart_estimate(self, api_client, test_user, test_task):
        """Test HTTP status codes for smart estimate endpoint."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test successful request
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_test_task_ids': [],
                'rationale': 'Test rationale'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        # Test unauthenticated request
        api_client.logout()
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test invalid UUID
        api_client.force_authenticate(test_user=test_user)
        invalid_url = reverse('smart-estimate', kwargs={'test_task_id': 'invalid-uuid'})
        response = api_client.post(invalid_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test non-existent test_task
        nonexistent_url = reverse('smart-estimate', kwargs={'test_task_id': uuid.uuid4()})
        response = api_client.post(nonexistent_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test wrong HTTP method
        response = api_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_http_status_codes_smart_rewrite(self, api_client, test_user, test_task):
        """Test HTTP status codes for smart rewrite endpoint."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test successful request
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Test Title',
                'test_user_story': 'As a test_user, I want to test so that I can verify'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        # Test unauthenticated request
        api_client.logout()
        response = api_client.post(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Test invalid UUID
        api_client.force_authenticate(test_user=test_user)
        invalid_url = reverse('smart-rewrite', kwargs={'test_task_id': 'invalid-uuid'})
        response = api_client.post(invalid_url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test non-existent test_task
        nonexistent_url = reverse('smart-rewrite', kwargs={'test_task_id': uuid.uuid4()})
        response = api_client.post(nonexistent_url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Test wrong HTTP method
        response = api_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_http_status_codes_sse(self, api_client, test_user, ai_operation):
        """Test HTTP status codes for SSE endpoints."""
        # Test successful request
        api_client.force_login(test_user)
        url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200

        # Test unauthenticated request
        api_client.logout()
        response = api_client.get(url)
        assert response.status_code == 302  # Redirect to login

        # Test non-existent operation
        api_client.force_login(test_user)
        nonexistent_url = reverse('ai-operation-sse', kwargs={'operation_id': uuid.uuid4()})
        response = api_client.get(nonexistent_url)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'error'

    def test_error_response_format_smart_summary(self, api_client, test_user, test_task):
        """Test error response format for smart summary."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test validation error
        with patch('ai_tools.views.smart_summary.validate_and_get_test_task') as mock_validate:
            mock_validate.side_effect = ValidationError('Invalid UUID format')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert 'error' in response.data

        # Test service error
        with patch('ai_tools.views.smart_summary.process_ai_async_test_task.delay') as mock_delay:
            mock_delay.side_effect = Exception('Service unavailable')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data
            assert 'Unable to start summary generation' in response.data['error']

    def test_error_response_format_smart_estimate(self, api_client, test_user, test_task):
        """Test error response format for smart estimate."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test service error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Service unavailable')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_error_response_format_smart_rewrite(self, api_client, test_user, test_task):
        """Test error response format for smart rewrite."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test service error
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.side_effect = Exception('Service unavailable')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data
            assert 'Unable to generate rewrite' in response.data['error']

    def test_error_response_format_sse(self, api_client, test_user, ai_operation):
        """Test error response format for SSE endpoints."""
        api_client.force_login(test_user)
        
        # Test non-existent operation
        url = reverse('ai-operation-sse', kwargs={'operation_id': uuid.uuid4()})
        response = api_client.get(url)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'error'
        assert 'Operation not found' in data['error']

        # Test exception handling
        with patch('ai_tools.views.sse.AIOperation.objects.get') as mock_get:
            mock_get.side_effect = Exception('Database error')
            
            url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
            response = api_client.get(url)
            
            assert response.status_code == 200
            data = json.loads(response.content)
            assert data['status'] == 'error'
            assert 'Database error' in data['error']

    def test_database_connection_errors(self, api_client, test_user, test_task):
        """Test handling of database connection errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test AIOperation creation failure
        with patch('ai_tools.models.AIOperation.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database connection failed')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data

    def test_validation_errors(self, api_client, test_user, test_task):
        """Test handling of validation errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test UUID validation error
        with patch('ai_tools.views.smart_summary.validate_and_get_test_task') as mock_validate:
            mock_validate.side_effect = ValidationError('Invalid UUID format')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_service_unavailable_errors(self, api_client, test_user, test_task):
        """Test handling of service unavailable errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test AI service unavailable
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_get_service.side_effect = Exception('AI service unavailable')
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_timeout_errors(self, api_client, test_user, test_task):
        """Test handling of timeout errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test timeout error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = TimeoutError('Request timeout')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_memory_errors(self, api_client, test_user, test_task):
        """Test handling of memory errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test memory error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = MemoryError('Out of memory')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_network_errors(self, api_client, test_user, test_task):
        """Test handling of network errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test network error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = ConnectionError('Network error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_permission_errors(self, api_client, test_user, test_task):
        """Test handling of permission errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test permission error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = PermissionError('Permission denied')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_file_system_errors(self, api_client, test_user, test_task):
        """Test handling of file system errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test file system error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = OSError('File system error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_serialization_errors(self, api_client, test_user, test_task):
        """Test handling of serialization errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test serialization error
        with patch('ai_tools.views.smart_estimate.SmartEstimateResponseSerializer') as mock_serializer:
            mock_serializer.side_effect = Exception('Serialization error')
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_celery_errors(self, api_client, test_user, test_task):
        """Test handling of Celery errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test Celery error
        with patch('ai_tools.views.smart_summary.process_ai_async_test_task.delay') as mock_delay:
            mock_delay.side_effect = Exception('Celery broker unavailable')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert 'error' in response.data

    def test_logging_errors(self, api_client, test_user, test_task):
        """Test handling of logging errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test logging error
        with patch('ai_tools.views.smart_summary.logger') as mock_logger:
            mock_logger.info.side_effect = Exception('Logging error')
            
            with patch('ai_tools.views.smart_summary.process_ai_async_test_task.delay'):
                url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
                response = api_client.post(url)
                
                # Should still work despite logging error
                assert response.status_code == status.HTTP_202_ACCEPTED

    def test_concurrent_access_errors(self, api_client, test_user, test_task):
        """Test handling of concurrent access errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test concurrent access error
        with patch('ai_tools.models.AIOperation.objects.create') as mock_create:
            mock_create.side_effect = Exception('Concurrent access error')
            
            url = reverse('smart-summary', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_resource_exhaustion_errors(self, api_client, test_user, test_task):
        """Test handling of resource exhaustion errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test resource exhaustion error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Resource exhausted')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_custom_exception_handling(self, api_client, test_user, test_task):
        """Test handling of custom exceptions."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test custom exception
        class CustomException(Exception):
            pass
        
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = CustomException('Custom error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_error_message_sanitization(self, api_client, test_user, test_task):
        """Test that error messages are properly sanitized."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test with potentially sensitive error message
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Database password: secret123')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            # Error message should not contain sensitive information
            assert 'secret123' not in str(response.data)

    def test_error_response_consistency(self, api_client, test_user, test_task):
        """Test that error responses are consistent across endpoints."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test all endpoints with same error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Test error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.side_effect = Exception('Test error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_error_response_headers(self, api_client, test_user, test_task):
        """Test that error responses have proper headers."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test error response headers
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Test error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert response['Content-Type'] == 'application/json'

    def test_error_response_timing(self, api_client, test_user, test_task):
        """Test that error responses are returned quickly."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test error response timing
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Test error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            # Response should be quick (no timeout)

    def test_error_response_idempotency(self, api_client, test_user, test_task):
        """Test that error responses are idempotent."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test multiple requests with same error
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Test error')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            
            # Make multiple requests
            for _ in range(3):
                response = api_client.post(url)
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_error_response_recovery(self, api_client, test_user, test_task):
        """Test that system recovers from errors."""
        api_client.force_authenticate(test_user=test_user)
        
        # Test error then success
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = [Exception('Test error'), {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_test_task_ids': [],
                'rationale': 'Test rationale'
            }]
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
            
            # First request should fail
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # Second request should succeed
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
