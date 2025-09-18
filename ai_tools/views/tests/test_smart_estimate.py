"""
Comprehensive tests for smart_estimate_view.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.exceptions import ValidationError

from ai_tools.models import AIOperation
from tasks.models import Task, TaskStatus, Project
from accounts.models import CustomUser


# Using shared fixtures directly from conftest.py

@pytest.fixture
def url(test_test_task):
    """Get smart estimate URL for test_task."""
    return reverse('smart-estimate', kwargs={'test_task_id': test_test_task.id})


# Using shared mock_ai_service_estimate_estimate from conftest.py


def test_smart_estimate_success(api_client, test_user, test_task, url, mock_ai_service_estimate_estimate):
    """Test successful smart estimate generation."""
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check response data
        assert 'suggested_points' in response.data
        assert 'confidence' in response.data
        assert 'similar_test_task_ids' in response.data
        assert 'rationale' in response.data
        
        # Check specific values
        assert response.data['suggested_points'] == 5
        assert response.data['confidence'] == 0.85
        assert response.data['similar_test_task_ids'] == ['test_task-1', 'test_task-2']
        assert 'Based on similar test_tasks' in response.data['rationale']
        
        # Check AI service was called
        mock_ai_service_estimate.generate_estimate.assert_called_once_with(test_task)


def test_smart_estimate_unauthenticated(api_client, url):
    """Test smart estimate without authentication."""
    response = api_client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_smart_estimate_invalid_test_task_id(api_client, test_user):
    """Test smart estimate with invalid test_task ID."""
    api_client.force_authenticate(test_user=test_user)
    
    invalid_url = reverse('smart-estimate', kwargs={'test_task_id': 'invalid-uuid'})
    response = api_client.post(invalid_url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_smart_estimate_nonexistent_test_task(api_client, test_user):
    """Test smart estimate with non-existent test_task ID."""
    api_client.force_authenticate(test_user=test_user)
    
    nonexistent_id = uuid.uuid4()
    nonexistent_url = reverse('smart-estimate', kwargs={'test_task_id': nonexistent_id})
    response = api_client.post(nonexistent_url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_smart_estimate_wrong_method(api_client, test_user, url):
    """Test smart estimate with wrong HTTP method."""
    api_client.force_authenticate(test_user=test_user)
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.put(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@patch('ai_tools.views.smart_estimate.validate_and_get_test_task')
def test_smart_estimate_validation_error(mock_validate, api_client, test_user, url):
    """Test smart estimate with validation error."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_validate.side_effect = ValidationError('Invalid test_task ID format')
    
    response = api_client.post(url)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_smart_estimate_ai_service_failure(api_client, test_user, test_task, url):
    """Test smart estimate when AI service fails."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_estimate.side_effect = Exception('AI service unavailable')
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_smart_estimate_logging(api_client, test_user, test_task, url, mock_ai_service_estimate):
    """Test that smart estimate logs appropriate messages."""
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.logger') as mock_logger:
        with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert 'Smart estimate completed' in log_message
            assert str(test_task.id) in log_message
            assert str(test_user.id) in log_message


def test_smart_estimate_response_serialization(api_client, test_user, url, mock_ai_service_estimate):
    """Test that response is properly serialized."""
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that response data matches expected structure
        expected_fields = ['suggested_points', 'confidence', 'similar_test_task_ids', 'rationale']
        for field in expected_fields:
            assert field in response.data
        
        # Check data types
        assert isinstance(response.data['suggested_points'], int)
        assert isinstance(response.data['confidence'], float)
        assert isinstance(response.data['similar_test_task_ids'], list)
        assert isinstance(response.data['rationale'], str)


def test_smart_estimate_different_confidence_levels(api_client, test_user, test_task, url):
    """Test smart estimate with different confidence levels."""
    api_client.force_authenticate(test_user=test_user)
    
    confidence_levels = [0.1, 0.5, 0.85, 1.0]
    
    for confidence in confidence_levels:
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': 3,
                'confidence': confidence,
                'similar_test_task_ids': [],
                'rationale': f'Confidence level: {confidence}'
            }
            mock_get_service.return_value = mock_service
            
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['confidence'] == confidence


def test_smart_estimate_different_point_values(api_client, test_user, test_task, url):
    """Test smart estimate with different point values."""
    api_client.force_authenticate(test_user=test_user)
    
    point_values = [1, 2, 3, 5, 8, 13, 21]
    
    for points in point_values:
        with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_estimate.return_value = {
                'suggested_points': points,
                'confidence': 0.8,
                'similar_test_task_ids': [f'test_task-{i}' for i in range(points)],
                'rationale': f'Estimated {points} points'
            }
            mock_get_service.return_value = mock_service
            
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['suggested_points'] == points


def test_smart_estimate_empty_similar_test_tasks(api_client, test_user, test_task, url):
    """Test smart estimate with no similar test_tasks."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 3,
        'confidence': 0.3,
        'similar_test_task_ids': [],
        'rationale': 'No similar test_tasks found, using default estimate'
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['similar_test_task_ids'] == []
        assert response.data['confidence'] == 0.3


def test_smart_estimate_many_similar_test_tasks(api_client, test_user, test_task, url):
    """Test smart estimate with many similar test_tasks."""
    api_client.force_authenticate(test_user=test_user)
    
    similar_test_tasks = [f'test_task-{i}' for i in range(50)]  # 50 similar test_tasks
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 8,
        'confidence': 0.95,
        'similar_test_task_ids': similar_test_tasks,
        'rationale': 'High confidence based on many similar test_tasks'
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['similar_test_task_ids']) == 50
        assert response.data['confidence'] == 0.95


@pytest.mark.parametrize("test_task_status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED])
def test_smart_estimate_test_task_different_statuses(api_client, test_user, test_project, test_task_status, mock_ai_service_estimate, db):
    """Test smart estimate with test_tasks in different statuses."""
    api_client.force_authenticate(test_user=test_user)
    
    # Create test_task with specific status
    test_task = Task.objects.create(
        test_project=test_project,
        title=f'Task {test_task_status}',
        description=f'Task in {test_task_status} status',
        status=test_task_status,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_test_task_with_existing_estimate(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task that already has an estimate."""
    # Create test_task with existing estimate
    test_task = Task.objects.create(
        test_project=test_project,
        title='Task with Estimate',
        description='Task that already has an estimate',
        status=TaskStatus.TODO,
        estimate=5,  # Existing estimate
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        # Should still generate estimate even if test_task has one
        assert 'suggested_points' in response.data


def test_smart_estimate_test_task_with_tags(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task that has tags."""
    # Create test_task with tags
    tagged_test_task = Task.objects.create(
        test_project=test_project,
        title='Tagged Task',
        description='Task with tags for testing',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user,
        tags=['frontend', 'backend', 'testing']
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': tagged_test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_test_task_with_activities(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task that has activities."""
    from test_tasks.models import TaskActivity, ActivityType
    
    # Create test_task
    test_task = Task.objects.create(
        test_project=test_project,
        title='Task with Activities',
        description='Task with activities for testing',
        status=TaskStatus.IN_PROGRESS,
        assignee=test_user,
        reporter=test_user
    )
    
    # Add activities
    TaskActivity.objects.create(
        test_task=test_task,
        actor=test_user,
        type=ActivityType.CREATED
    )
    
    TaskActivity.objects.create(
        test_task=test_task,
        actor=test_user,
        type=ActivityType.UPDATED_STATUS,
        field='status',
        before='TODO',
        after='IN_PROGRESS'
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_empty_test_task_description(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task that has empty description."""
    # Create test_task with empty description
    empty_test_task = Task.objects.create(
        test_project=test_project,
        title='Empty Description Task',
        description='',  # Empty description
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': empty_test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_large_test_task_description(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task that has very large description."""
    # Create test_task with large description
    large_description = 'A' * 10000  # 10KB description
    large_test_task = Task.objects.create(
        test_project=test_project,
        title='Large Description Task',
        description=large_description,
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': large_test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_unicode_content(api_client, test_user, test_project, mock_ai_service_estimate, db):
    """Test smart estimate with test_task containing unicode characters."""
    # Create test_task with unicode content
    unicode_test_task = Task.objects.create(
        test_project=test_project,
        title='Unicode Task 🚀',
        description='Task with unicode characters: ñáéíóú, 中文, العربية, русский',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-estimate', kwargs={'test_task_id': unicode_test_task.id})
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_ai_service_estimate):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data


def test_smart_estimate_service_factory_error(api_client, test_user, url):
    """Test smart estimate when service factory fails."""
    api_client.force_authenticate(test_user=test_user)
    
    with patch('ai_tools.views.smart_estimate.get_ai_service') as mock_get_service:
        mock_get_service.side_effect = Exception('Service factory error')
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_smart_estimate_invalid_response_format(api_client, test_user, test_task, url):
    """Test smart estimate when AI service returns invalid format."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    # Return invalid format (missing required fields)
    mock_service.generate_estimate.return_value = {
        'suggested_points': 5,
        # Missing confidence, similar_test_task_ids, rationale
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        # Should still work as serializer handles missing fields
        assert response.status_code == status.HTTP_200_OK


def test_smart_estimate_negative_points(api_client, test_user, test_task, url):
    """Test smart estimate with negative point values."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': -1,  # Negative points
        'confidence': 0.5,
        'similar_test_task_ids': [],
        'rationale': 'Negative estimate'
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggested_points'] == -1


def test_smart_estimate_zero_points(api_client, test_user, test_task, url):
    """Test smart estimate with zero point values."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 0,  # Zero points
        'confidence': 0.5,
        'similar_test_task_ids': [],
        'rationale': 'Zero estimate'
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggested_points'] == 0


def test_smart_estimate_very_high_points(api_client, test_user, test_task, url):
    """Test smart estimate with very high point values."""
    api_client.force_authenticate(test_user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 1000,  # Very high points
        'confidence': 0.5,
        'similar_test_task_ids': [],
        'rationale': 'Very high estimate'
    }
    
    with patch('ai_tools.views.smart_estimate.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggested_points'] == 1000
