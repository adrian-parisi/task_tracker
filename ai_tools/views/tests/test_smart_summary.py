"""
Comprehensive tests for smart_summary_view.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from ai_tools.models import AIOperation
from ai_tools.tasks import process_ai_async_task
from tasks.models import Task, TaskStatus, Project, TaskActivity, ActivityType
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py

@pytest.fixture
def url(test_task):
    """Get smart summary URL for task."""
    return reverse('smart-summary', kwargs={'task_id': test_task.id})


def test_smart_summary_success(api_client, test_user, test_task, url):
    """Test successful smart summary generation."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay') as mock_delay:
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Check response data
        assert 'operation_id' in response.data
        assert 'status' in response.data
        assert 'sse_url' in response.data
        assert response.data['status'] == 'pending'
        assert 'stream' in response.data['sse_url']
        
        # Check AIOperation was created
        operation = AIOperation.objects.get(task=test_task)
        assert operation.operation_type == 'SUMMARY'
        assert operation.status == 'PENDING'
        assert operation.user == test_user
        
        # Check async test_task was queued
        mock_delay.assert_called_once_with(str(operation.id))


def test_smart_summary_unauthenticated(api_client, url):
    """Test smart summary without authentication."""
    response = api_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_smart_summary_invalid_task_id(api_client, test_user):
    """Test smart summary with invalid test_task ID."""
    api_client.force_authenticate(user=test_user)
    
    # Test with invalid UUID format - use a valid UUID format but non-existent
    invalid_uuid = '00000000-0000-0000-0000-000000000000'
    invalid_url = reverse('smart-summary', kwargs={'task_id': invalid_uuid})
    response = api_client.post(invalid_url)
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_smart_summary_nonexistent_test_task(api_client, test_user):
    """Test smart summary with non-existent test_task ID."""
    api_client.force_authenticate(user=test_user)
    
    nonexistent_id = uuid.uuid4()
    nonexistent_url = reverse('smart-summary', kwargs={'task_id': nonexistent_id})
    response = api_client.post(nonexistent_url)
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_smart_summary_wrong_method(api_client, test_user, url):
    """Test smart summary with wrong HTTP method."""
    api_client.force_authenticate(user=test_user)
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.put(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@patch('ai_tools.views.smart_summary.validate_and_get_task')
def test_smart_summary_validation_error(mock_validate, api_client, test_user, url):
    """Test smart summary with validation error."""
    api_client.force_authenticate(user=test_user)
    
    mock_validate.side_effect = ValidationError('Invalid test_task ID format')
    
    response = api_client.post(url)
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@patch('ai_tools.views.smart_summary.process_ai_async_task.delay')
def test_smart_summary_async_test_task_failure(mock_delay, api_client, test_user, url):
    """Test smart summary when async test_task fails to queue."""
    api_client.force_authenticate(user=test_user)
    
    mock_delay.side_effect = Exception('Celery connection failed')
    
    response = api_client.post(url)
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert 'error' in response.data
    assert 'Unable to start summary generation' in response.data['error']


def test_smart_summary_operation_creation_failure(api_client, test_user, url):
    """Test smart summary when AIOperation creation fails."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.models.AIOperation.objects.create') as mock_create:
        mock_create.side_effect = Exception('Database error')
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'error' in response.data


@patch('ai_tools.views.smart_summary.logger')
def test_smart_summary_logging(mock_logger, api_client, test_user, test_task, url):
    """Test that smart summary logs appropriate messages."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_logger.info.assert_called_once()
        log_message = mock_logger.info.call_args[0][0]
        assert 'Smart summary async task' in log_message
        assert str(test_task.id) in log_message
        assert str(test_user.id) in log_message


@patch('ai_tools.views.smart_summary.logger')
def test_smart_summary_error_logging(mock_logger, api_client, test_user, test_task, url):
    """Test that smart summary logs errors appropriately."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay') as mock_delay:
        mock_delay.side_effect = Exception('Test error')
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        mock_logger.error.assert_called_once()
        log_message = mock_logger.error.call_args[0][0]
        assert 'Error in smart summary' in log_message
        assert str(test_task.id) in log_message
        assert 'Test error' in log_message


def test_smart_summary_response_serialization(api_client, test_user, url):
    """Test that response is properly serialized."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Check that response data matches expected structure
        expected_fields = ['operation_id', 'status', 'sse_url']
        for field in expected_fields:
            assert field in response.data
        
        # Check data types
        assert isinstance(response.data['operation_id'], str)
        assert isinstance(response.data['status'], str)
        assert isinstance(response.data['sse_url'], str)
        
        # Validate UUID format
        operation_id = response.data['operation_id']
        uuid.UUID(operation_id)  # Should not raise exception


def test_smart_summary_sse_url_format(api_client, test_user, url):
    """Test that SSE URL is properly formatted."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        sse_url = response.data['sse_url']
        assert sse_url.endswith('/stream/')
        assert 'ai-operations' in sse_url
        
        # Extract operation ID from URL and verify it matches
        operation_id_from_url = sse_url.split('/')[-3]  # Get UUID from URL
        assert operation_id_from_url == response.data['operation_id']


def test_smart_summary_multiple_operations(api_client, test_user, test_task, url):
    """Test creating multiple summary operations for the same test_task."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        # Create first operation
        response1 = api_client.post(url)
        assert response1.status_code == status.HTTP_202_ACCEPTED
        
        # Create second operation
        response2 = api_client.post(url)
        assert response2.status_code == status.HTTP_202_ACCEPTED
        
        # Both operations should be created
        operations = AIOperation.objects.filter(task=test_task, operation_type='SUMMARY')
        assert operations.count() == 2
        
        # Operation IDs should be different
        assert response1.data['operation_id'] != response2.data['operation_id']


def test_smart_summary_different_test_users(api_client, test_user, test_task, url, db):
    """Test that different test_users can create operations for the same test_task."""
    # Create another test_user
    other_test_user = CustomUser.objects.create_user(
        username='otheruser',
        email='other@example.com',
        first_name='Other',
        last_name='User'
    )
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        # First test_user creates operation
        api_client.force_authenticate(user=test_user)
        response1 = api_client.post(url)
        assert response1.status_code == status.HTTP_202_ACCEPTED
        
        # Second test_user creates operation
        api_client.force_authenticate(user=other_test_user)
        response2 = api_client.post(url)
        assert response2.status_code == status.HTTP_202_ACCEPTED
        
        # Both operations should be created with correct test_users
        operations = AIOperation.objects.filter(task=test_task, operation_type='SUMMARY')
        assert operations.count() == 2
        
        test_user_ids = [op.user.id for op in operations]
        assert test_user.id in test_user_ids
        assert other_test_user.id in test_user_ids


def test_smart_summary_test_task_with_activities(api_client, test_user, test_task, url, db):
    """Test smart summary with test_task that has activities."""
    # Add some activities to the test_task
    TaskActivity.objects.create(
        task=test_task,
        actor=test_user,
        type=ActivityType.CREATED
    )
    
    TaskActivity.objects.create(
        task=test_task,
        actor=test_user,
        type=ActivityType.UPDATED_STATUS,
        field='status',
        before='TODO',
        after='IN_PROGRESS'
    )
    
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should still be created successfully
        operation = AIOperation.objects.get(task=test_task)
        assert operation.operation_type == 'SUMMARY'


@pytest.mark.parametrize("test_task_status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED])
def test_smart_summary_test_task_different_statuses(api_client, test_user, test_project, test_task_status, db):
    """Test smart summary with test_tasks in different statuses."""
    api_client.force_authenticate(user=test_user)
    
    # Create test_task with specific status
    test_task = Task.objects.create(
        project=test_project,
        title=f'Task {test_task_status}',
        description=f'Task in {test_task_status} status',
        status=test_task_status,
        assignee=test_user,
        reporter=test_user,
    )
    
    url = reverse('smart-summary', kwargs={'task_id': test_task.id})
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should be created
        operation = AIOperation.objects.get(task=test_task)
        assert operation.operation_type == 'SUMMARY'


def test_smart_summary_empty_test_task_description(api_client, test_user, test_project, db):
    """Test smart summary with test_task that has empty description."""
    # Create test_task with empty description
    empty_test_task = Task.objects.create(
        project=test_project,
        title='Empty Description Task',
        description='',  # Empty description
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-summary', kwargs={'task_id': empty_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should still be created
        operation = AIOperation.objects.get(task=empty_test_task)
        assert operation.operation_type == 'SUMMARY'


def test_smart_summary_test_task_with_tags(api_client, test_user, test_project, db):
    """Test smart summary with test_task that has tags."""
    # Create test_task with tags
    tagged_test_task = Task.objects.create(
        project=test_project,
        title='Tagged Task',
        description='Task with tags for testing',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user,
        tags=['frontend', 'backend', 'testing']
    )
    
    url = reverse('smart-summary', kwargs={'task_id': tagged_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should be created
        operation = AIOperation.objects.get(task=tagged_test_task)
        assert operation.operation_type == 'SUMMARY'


def test_smart_summary_large_test_task_description(api_client, test_user, test_project, db):
    """Test smart summary with test_task that has very large description."""
    # Create test_task with large description
    large_description = 'A' * 10000  # 10KB description
    large_test_task = Task.objects.create(
        project=test_project,
        title='Large Description Task',
        description=large_description,
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-summary', kwargs={'task_id': large_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should be created
        operation = AIOperation.objects.get(task=large_test_task)
        assert operation.operation_type == 'SUMMARY'


def test_smart_summary_unicode_content(api_client, test_user, test_project, db):
    """Test smart summary with test_task containing unicode characters."""
    # Create test_task with unicode content
    unicode_test_task = Task.objects.create(
        project=test_project,
        title='Unicode Task 🚀',
        description='Task with unicode characters: ñáéíóú, 中文, العربية, русский',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-summary', kwargs={'task_id': unicode_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_summary.process_ai_async_task.delay'):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_202_ACCEPTED
        
        # Operation should be created
        operation = AIOperation.objects.get(task=unicode_test_task)
        assert operation.operation_type == 'SUMMARY'