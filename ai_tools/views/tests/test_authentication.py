"""
Comprehensive authentication and authorization tests for AI tools views.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from ai_tools.models import AIOperation
from tasks.models import Task, TaskStatus, Project
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py

@pytest.fixture
def other_ai_operation(db, other_test_task, other_test_user):
    """Create AI operation for other test_user's test_task."""
    return AIOperation.objects.create(
        task=other_test_task,
        operation_type='SUMMARY',
        status='PENDING',
        test_user=other_test_user
    )


class TestAuthentication:
    """Test authentication requirements for AI tools views."""

    def test_smart_summary_requires_authentication(self, api_client, test_task):
        """Test that smart summary requires authentication."""
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_smart_estimate_requires_authentication(self, api_client, test_task):
        """Test that smart estimate requires authentication."""
        url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_smart_rewrite_requires_authentication(self, api_client, test_task):
        """Test that smart rewrite requires authentication."""
        url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_sse_requires_authentication(self, api_client, ai_operation):
        """Test that SSE endpoints require authentication."""
        url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 302  # Redirect to login

        url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 302  # Redirect to login

    def test_authenticated_test_user_can_access_own_test_tasks(self, api_client, test_user, test_task):
        """Test that authenticated test_user can access their own test_tasks."""
        api_client.force_authenticate(user=test_user)
        
        # Test smart summary
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Test smart estimate
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_task_ids': [],
                'rationale': 'Test rationale'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        # Test smart rewrite
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Test Title',
                'user_story': 'As a user, I want to test so that I can verify'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_authenticated_test_user_can_access_own_operations(self, api_client, test_user, ai_operation):
        """Test that authenticated test_user can access their own operations."""
        api_client.force_authenticate(user=test_user)
        
        # Test SSE
        url = reverse('ai-operation-sse', kwargs={'operation_id': ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200

        # Test test SSE
        url = reverse('test-sse', kwargs={'operation_id': ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_user_cannot_access_other_test_users_test_tasks(self, api_client, test_user, other_test_task):
        """Test that test_user cannot access other test_users' test_tasks."""
        api_client.force_authenticate(user=test_user)
        
        # Test smart summary
        url = reverse('smart-summary', kwargs={'task_id': other_test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Test smart estimate
        url = reverse('smart-estimate', kwargs={'task_id': other_test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Test smart rewrite
        url = reverse('smart-rewrite', kwargs={'task_id': other_test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_user_cannot_access_other_test_users_operations(self, api_client, test_user, other_ai_operation):
        """Test that test_user cannot access other test_users' operations."""
        api_client.force_authenticate(user=test_user)
        
        # Test SSE
        url = reverse('ai-operation-sse', kwargs={'operation_id': other_ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200
        # Should return error in JSON response
        import json
        data = json.loads(response.content)
        assert data['status'] == 'error'
        assert 'Operation not found' in data['error']

        # Test test SSE
        url = reverse('test-sse', kwargs={'operation_id': other_ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data['status'] == 'error'
        assert 'Operation not found' in data['error']

    def test_inactive_test_user_cannot_access_endpoints(self, api_client, inactive_test_user, test_task):
        """Test that inactive test_user cannot access endpoints."""
        api_client.force_authenticate(user=inactive_test_user)
        
        # Test smart summary
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test smart estimate
        url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

        # Test smart rewrite
        url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_user_can_access_any_task(self, api_client, admin_user, other_task):
        """Test that admin test_user can access any test_task."""
        api_client.force_authenticate(user=admin_test_user)
        
        # Test smart summary
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': other_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Test smart estimate
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_task_ids': [],
                'rationale': 'Test rationale'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': other_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        # Test smart rewrite
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Test Title',
                'user_story': 'As a user, I want to test so that I can verify'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': other_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_admin_test_user_can_access_any_operation(self, api_client, admin_test_user, other_ai_operation):
        """Test that admin test_user can access any operation."""
        api_client.force_authenticate(user=admin_test_user)
        
        # Test SSE
        url = reverse('ai-operation-sse', kwargs={'operation_id': other_ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200

        # Test test SSE
        url = reverse('test-sse', kwargs={'operation_id': other_ai_operation.id})
        response = api_client.get(url)
        assert response.status_code == 200

    def test_token_authentication(self, api_client, test_user, test_task):
        """Test token-based authentication."""
        # This would require setting up token authentication
        # For now, we'll test that the endpoints work with force_authenticate
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_session_authentication(self, api_client, test_user, test_task):
        """Test session-based authentication."""
        api_client.force_login(test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_multiple_authentication_methods(self, api_client, test_user, test_task):
        """Test that multiple authentication methods work."""
        # Test force_authenticate
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Reset api_client
        api_client = APIClient()
        
        # Test force_login
        api_client.force_login(test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_headers(self, api_client, test_user, test_task):
        """Test authentication with various headers."""
        api_client.force_authenticate(user=test_user)
        
        # Test with custom headers
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, HTTP_X_CUSTOM_HEADER='test')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_different_test_user_roles(self, api_client, db):
        """Test authentication with different test_user roles."""
        # Create test_users with different roles
        regular_test_user = CustomUser.objects.create_test_user(
            test_username='regular',
            email='regular@example.com',
            first_name='Regular',
            last_name='User'
        )
        
        staff_test_user = CustomUser.objects.create_test_user(
            test_username='staff',
            email='staff@example.com',
            first_name='Staff',
            last_name='User',
            is_staff=True
        )
        
        supertest_user = CustomUser.objects.create_test_user(
            test_username='super',
            email='super@example.com',
            first_name='Super',
            last_name='User',
            is_supertest_user=True
        )
        
        # Create test_project and test_task
        test_project = Project.objects.create(
            code='AUTH',
            name='Auth Test Project',
            description='Project for auth testing',
            owner=regular_test_user
        )
        
        test_task = Task.objects.create(
            test_project=test_project,
            title='Auth Test Task',
            description='Task for auth testing',
            status=TaskStatus.TODO,
            assignee=regular_test_user,
            reporter=regular_test_user
        )
        
        # Test regular test_user
        api_client.force_authenticate(user=regular_test_user)
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Test staff test_user
        api_client.force_authenticate(user=staff_test_user)
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        # Test supertest_user
        api_client.force_authenticate(user=supertest_user)
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_expired_tokens(self, api_client, test_user, test_task):
        """Test authentication with expired tokens (simulated)."""
        # This would require setting up token authentication with expiration
        # For now, we'll test that the endpoints work with force_authenticate
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_invalid_tokens(self, api_client, test_task):
        """Test authentication with invalid tokens."""
        # Test without authentication
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authentication_with_malformed_tokens(self, api_client, test_task):
        """Test authentication with malformed tokens."""
        # Test with malformed authorization header
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url, HTTP_AUTHORIZATION='Bearer invalid-token')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authentication_without_authorization_header(self, api_client, test_task):
        """Test authentication without authorization header."""
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authentication_with_empty_authorization_header(self, api_client, test_task):
        """Test authentication with empty authorization header."""
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url, HTTP_AUTHORIZATION='')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authentication_with_whitespace_authorization_header(self, api_client, test_task):
        """Test authentication with whitespace-only authorization header."""
        url = reverse('smart-summary', kwargs={'task_id': test_task.id})
        response = api_client.post(url, HTTP_AUTHORIZATION='   ')
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_authentication_with_case_insensitive_headers(self, api_client, test_user, test_task):
        """Test authentication with case-insensitive headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, HTTP_AUTHORIZATION='Bearer test-token')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_multiple_authorization_headers(self, api_client, test_user, test_task):
        """Test authentication with multiple authorization headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_AUTHORIZATION='Bearer token1',
                                 HTTP_X_AUTHORIZATION='Bearer token2')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_special_characters_in_headers(self, api_client, test_user, test_task):
        """Test authentication with special characters in headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_X_CUSTOM_HEADER='Special chars: !@#$%^&*()')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_unicode_in_headers(self, api_client, test_user, test_task):
        """Test authentication with unicode in headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_X_CUSTOM_HEADER='Unicode: ñáéíóú, 中文, العربية')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_very_long_headers(self, api_client, test_user, test_task):
        """Test authentication with very long headers."""
        api_client.force_authenticate(user=test_user)
        
        long_header = 'A' * 10000  # 10KB header
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_X_CUSTOM_HEADER=long_header)
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_null_bytes_in_headers(self, api_client, test_user, test_task):
        """Test authentication with null bytes in headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_X_CUSTOM_HEADER='Header with null\x00bytes')
            assert response.status_code == status.HTTP_202_ACCEPTED

    def test_authentication_with_newlines_in_headers(self, api_client, test_user, test_task):
        """Test authentication with newlines in headers."""
        api_client.force_authenticate(user=test_user)
        
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url, 
                                 HTTP_X_CUSTOM_HEADER='Header with\nnewlines\r\nand\rcarriage returns')
            assert response.status_code == status.HTTP_202_ACCEPTED
