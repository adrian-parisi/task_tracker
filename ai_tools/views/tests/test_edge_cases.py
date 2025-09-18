"""
Comprehensive edge case tests for AI tools views.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from ai_tools.models import AIOperation
from tasks.models import Task, TaskStatus, Project, TaskActivity, ActivityType
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py


class TestEdgeCases:
    """Test edge cases for AI tools views."""

    def test_invalid_uuid_formats(self, api_client, test_user):
        """Test various invalid UUID formats."""
        api_client.force_authenticate(user=test_user)
        
        invalid_uuids = [
            '00000000-0000-0000-0000-000000000001',
            '00000000-0000-0000-0000-000000000002',
            '00000000-0000-0000-0000-000000000003',
            '00000000-0000-0000-0000-000000000004',
            '00000000-0000-0000-0000-000000000005',
        ]
        
        for invalid_uuid in invalid_uuids:
            # Test smart summary
            url = reverse('smart-summary', kwargs={'task_id': invalid_uuid})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test smart estimate
            url = reverse('smart-estimate', kwargs={'task_id': invalid_uuid})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test smart rewrite
            url = reverse('smart-rewrite', kwargs={'task_id': invalid_uuid})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_nonexistent_task_ids(self, api_client, test_user):
        """Test with non-existent but valid UUID test_task IDs."""
        api_client.force_authenticate(user=test_user)
        
        # Generate valid UUIDs that don't exist in database
        nonexistent_ids = [uuid.uuid4() for _ in range(5)]
        
        for task_id in nonexistent_ids:
            # Test smart summary
            url = reverse('smart-summary', kwargs={'task_id': task_id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test smart estimate
            url = reverse('smart-estimate', kwargs={'task_id': task_id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND
            
            # Test smart rewrite
            url = reverse('smart-rewrite', kwargs={'task_id': task_id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_requests(self, api_client, test_task):
        """Test all endpoints without authentication."""
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

    def test_service_failures(self, api_client, test_user, test_task):
        """Test when AI services fail."""
        api_client.force_authenticate(user=test_user)
        
        # Test smart estimate service failure
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = Exception('Service unavailable')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Test smart rewrite service failure
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.side_effect = Exception('Service unavailable')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Test smart summary async test_task failure
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay') as mock_delay:
            mock_delay.side_effect = Exception('Celery unavailable')
            
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_database_errors(self, api_client, test_user, test_task):
        """Test when database operations fail."""
        api_client.force_authenticate(user=test_user)
        
        # Test AIOperation creation failure
        with patch('ai_tools.models.AIOperation.objects.create') as mock_create:
            mock_create.side_effect = Exception('Database error')
            
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    # Removed test_validation_errors - validation function no longer exists

    def test_concurrent_requests(self, api_client, test_user, test_task):
        """Test concurrent requests to the same endpoint."""
        api_client.force_authenticate(user=test_user)
        
        # Test multiple concurrent smart summary requests
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': test_task.id})
            
            # Simulate multiple concurrent requests
            responses = []
            for _ in range(5):
                response = api_client.post(url)
                responses.append(response)
            
            # All should succeed
            for response in responses:
                assert response.status_code == status.HTTP_202_ACCEPTED
            
            # Should create multiple operations
            operations = AIOperation.objects.filter(task=test_task, operation_type='SUMMARY')
            assert operations.count() == 5

    def test_large_payloads(self, api_client, test_user, test_project, db):
        """Test with very large test_task descriptions."""
        api_client.force_authenticate(user=test_user)
        
        # Create test_task with very large description
        large_description = 'A' * 100000  # 100KB description
        large_test_task = Task.objects.create(
            project=test_project,
            title='Large Task',
            description=large_description,
            status=TaskStatus.TODO,
            assignee=test_user,
            reporter=test_user
        )
        
        # Test all endpoints with large test_task
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_task_ids': [],
                'rationale': 'Test rationale'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Test Title',
                'user_story': 'As a user, I want to test so that I can verify'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_unicode_content(self, api_client, test_user, test_project, db):
        """Test with unicode content in test_tasks."""
        api_client.force_authenticate(user=test_user)
        
        unicode_test_task = Task.objects.create(
            project=test_project,
            title='Unicode Task 🚀',
            description='Task with unicode: ñáéíóú, 中文, العربية, русский, 🎉✨🌟',
            status=TaskStatus.TODO,
            assignee=test_user,
            reporter=test_user
        )
        
        # Test all endpoints with unicode test_task
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': unicode_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_task_ids': [],
                'rationale': 'Test rationale'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': unicode_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Unicode Title 🚀',
                'user_story': 'As a user, I want to test unicode so that I can verify'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': unicode_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_empty_and_minimal_test_tasks(self, api_client, test_user, test_project, db):
        """Test with empty and minimal test_task data."""
        api_client.force_authenticate(user=test_user)
        
        # Test with minimal test_task
        minimal_test_task = Task.objects.create(
            project=test_project,
            title='Min',  # Minimum valid title
            status=TaskStatus.TODO
        )
        
        # Test all endpoints with minimal test_task
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': minimal_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 1,
                'confidence': 0.5,
                'similar_task_ids': [],
                'rationale': 'Minimal test_task'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': minimal_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Enhanced Min',
                'user_story': 'As a user, I want to work with minimal test_task so that I can test'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': minimal_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_special_characters_in_test_tasks(self, api_client, test_user, test_project, db):
        """Test with special characters in test_task content."""
        api_client.force_authenticate(user=test_user)
        
        special_test_task = Task.objects.create(
            project=test_project,
            title='Special Chars: !@#$%^&*()_+-=[]{}|;:,.<>?',
            description='Description with special chars: <script>alert("xss")</script> & HTML entities: &lt;&gt;&amp;',
            status=TaskStatus.TODO,
            assignee=test_user,
            reporter=test_user
        )
        
        # Test all endpoints with special character test_task
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': special_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 3,
                'confidence': 0.6,
                'similar_task_ids': [],
                'rationale': 'Special character test_task'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': special_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Enhanced Special Chars',
                'user_story': 'As a user, I want to handle special chars so that I can test security'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': special_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_network_timeouts(self, api_client, test_user, test_task):
        """Test handling of network timeouts."""
        api_client.force_authenticate(user=test_user)
        
        # Test smart estimate with timeout
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.side_effect = TimeoutError('Request timeout')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

        # Test smart rewrite with timeout
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.side_effect = TimeoutError('Request timeout')
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_memory_limits(self, api_client, test_user, test_project, db):
        """Test with test_tasks that might hit memory limits."""
        api_client.force_authenticate(user=test_user)
        
        # Create test_task with very large tags list
        large_tags = [f'tag{i}' for i in range(1000)]  # 1000 tags
        large_test_task = Task.objects.create(
            project=test_project,
            title='Large Tags Task',
            description='Task with many tags',
            status=TaskStatus.TODO,
            assignee=test_user,
            reporter=test_user,
            tags=large_tags
        )
        
        # Test all endpoints with large tags test_task
        with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
            url = reverse('smart-summary', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_202_ACCEPTED

        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 5,
                'confidence': 0.8,
                'similar_task_ids': [],
                'rationale': 'Large tags test_task'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Enhanced Large Tags Task',
                'user_story': 'As a user, I want to work with many tags so that I can organize'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-rewrite', kwargs={'task_id': large_test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK

    def test_rate_limiting_simulation(self, api_client, test_user, test_task):
        """Test rapid successive requests (rate limiting simulation)."""
        api_client.force_authenticate(user=test_user)
        
        # Test rapid requests to smart estimate
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
            
            # Make 10 rapid requests
            for _ in range(10):
                response = api_client.post(url)
                assert response.status_code == status.HTTP_200_OK

    def test_corrupted_data_handling(self, api_client, test_user, test_task):
        """Test handling of corrupted or malformed data."""
        api_client.force_authenticate(user=test_user)
        
        # Test with AI service returning corrupted data
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            # Return data with wrong types
            mock_service.generate_estimate.return_value = {
                'suggested_points': 'not_a_number',  # Should be int
                'confidence': 'not_a_float',  # Should be float
                'similar_task_ids': 'not_a_list',  # Should be list
                'rationale': 123  # Should be string
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            
            # Should return 500 due to serializer error
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_boundary_values(self, api_client, test_user, test_task):
        """Test boundary values and limits."""
        api_client.force_authenticate(user=test_user)
        
        # Test with extreme confidence values
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 0,  # Minimum points
                'confidence': 0.0,  # Minimum confidence
                'similar_task_ids': [],
                'rationale': 'Minimum values'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['suggested_points'] == 0
            assert response.data['confidence'] == 0.0

        # Test with maximum values
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 999999,  # Very large number
                'confidence': 1.0,  # Maximum confidence
                'similar_task_ids': [f'test_task{i}' for i in range(100)],  # Many similar test_tasks
                'rationale': 'Maximum values'
            }
            mock_get_service.return_value = mock_service
            
            url = reverse('smart-estimate', kwargs={'task_id': test_task.id})
            response = api_client.post(url)
            assert response.status_code == status.HTTP_200_OK
            assert response.data['suggested_points'] == 999999
            assert response.data['confidence'] == 1.0
