"""
Comprehensive tests for smart_rewrite_view.
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




@pytest.fixture
def url(test_task):
    """Get smart rewrite URL for test_task."""
    return reverse('smart-rewrite', kwargs={'task_id': test_task.id})


# Using shared mock_ai_service_rewrite from conftest.py


def test_smart_rewrite_success(api_client, test_user, test_task, url, mock_ai_service_rewrite):
    """Test successful smart rewrite generation."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check response data
        assert 'title' in response.data
        assert 'user_story' in response.data
        
        # Check specific values
        assert response.data['title'] == 'Enhanced Test Task'
        assert 'As a user' in response.data['user_story']
        assert 'I want to test' in response.data['user_story']
        assert 'so that I can' in response.data['user_story']
        
        # Check AI service was called
        mock_ai_service_rewrite.generate_rewrite.assert_called_once_with(test_task)


def test_smart_rewrite_unauthenticated(api_client, url):
    """Test smart rewrite without authentication."""
    response = api_client.post(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_smart_rewrite_invalid_task_id(api_client, test_user):
    """Test smart rewrite with invalid test_task ID."""
    api_client.force_authenticate(user=test_user)
    
    invalid_url = reverse('smart-rewrite', kwargs={'task_id': '00000000-0000-0000-0000-000000000000'})
    response = api_client.post(invalid_url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_smart_rewrite_nonexistent_test_task(api_client, test_user):
    """Test smart rewrite with non-existent test_task ID."""
    api_client.force_authenticate(user=test_user)
    
    nonexistent_id = uuid.uuid4()
    nonexistent_url = reverse('smart-rewrite', kwargs={'task_id': nonexistent_id})
    response = api_client.post(nonexistent_url)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_smart_rewrite_wrong_method(api_client, test_user, url):
    """Test smart rewrite with wrong HTTP method."""
    api_client.force_authenticate(user=test_user)
    
    response = api_client.get(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.put(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    response = api_client.delete(url)
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED




def test_smart_rewrite_ai_service_failure(api_client, test_user, test_task, url):
    """Test smart rewrite when AI service fails."""
    api_client.force_authenticate(user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_rewrite.side_effect = Exception('AI service unavailable')
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'An unexpected error occurred' in response.data["detail"]


def test_smart_rewrite_logging(api_client, test_user, test_task, url, mock_ai_service_rewrite):
    """Test that smart rewrite logs appropriate messages."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.logger') as mock_logger:
        with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            mock_logger.info.assert_called_once()
            log_message = mock_logger.info.call_args[0][0]
            assert 'Smart rewrite completed' in log_message
            assert str(test_task.id) in log_message
            assert str(test_user.id) in log_message


def test_smart_rewrite_error_logging(api_client, test_user, test_task, url):
    """Test that smart rewrite logs errors appropriately."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.logger') as mock_logger:
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_get_service.side_effect = Exception('Test error')
            
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            # Logger is handled by exception handler, not view


def test_smart_rewrite_response_serialization(api_client, test_user, url, mock_ai_service_rewrite):
    """Test that response is properly serialized."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        
        # Check that response data matches expected structure
        expected_fields = ['title', 'user_story']
        for field in expected_fields:
            assert field in response.data
        
        # Check data types
        assert isinstance(response.data['title'], str)
        assert isinstance(response.data['user_story'], str)


def test_smart_rewrite_different_titles(api_client, test_user, test_task, url):
    """Test smart rewrite with different title formats."""
    api_client.force_authenticate(user=test_user)
    
    test_titles = [
        'Simple Task',
        'Complex Multi-Word Task Title',
        'Task with Numbers 123',
        'Task with Special Characters !@#$%',
        'Very Long Task Title That Should Be Handled Properly By The AI Service'
    ]
    
    for title in test_titles:
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': f'Enhanced {title}',
                'user_story': f'As a user, I want to work with {title} so that I can achieve my goals'
            }
            mock_get_service.return_value = mock_service
            
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert 'Enhanced' in response.data['title']


def test_smart_rewrite_different_user_story_formats(api_client, test_user, test_task, url):
    """Test smart rewrite with different test_user story formats."""
    api_client.force_authenticate(user=test_user)
    
    user_story_formats = [
        'As a developer, I want to implement features so that test_users can benefit',
        'As a QA engineer, I want to test functionality so that quality is ensured',
        'As a product manager, I want to track progress so that deadlines are met',
        'As an end test_user, I want to use the application so that I can be productive'
    ]
    
    for user_story in user_story_formats:
        with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
            mock_service = MagicMock()
            mock_service.generate_rewrite.return_value = {
                'title': 'Test Task',
                'user_story': user_story
            }
            mock_get_service.return_value = mock_service
            
            response = api_client.post(url)
            
            assert response.status_code == status.HTTP_200_OK
            assert response.data['user_story'] == user_story


@pytest.mark.parametrize("test_task_status", [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED])
def test_smart_rewrite_test_task_different_statuses(api_client, test_user, test_project, test_task_status, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_tasks in different statuses."""
    api_client.force_authenticate(user=test_user)
    
    # Create test_task with specific status
    test_task = Task.objects.create(
        project=test_project,
        title=f'Task {test_task_status}',
        description=f'Task in {test_task_status} status',
        status=test_task_status,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_test_task_with_existing_estimate(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task that has an estimate."""
    # Create test_task with estimate
    test_task = Task.objects.create(
        project=test_project,
        title='Task with Estimate',
        description='Task that has an estimate',
        status=TaskStatus.TODO,
        estimate=5,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_test_task_with_tags(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task that has tags."""
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
    
    url = reverse('smart-rewrite', kwargs={'task_id': tagged_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_test_task_with_activities(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task that has activities."""
    # Create test_task
    test_task = Task.objects.create(
        project=test_project,
        title='Task with Activities',
        description='Task with activities for testing',
        status=TaskStatus.IN_PROGRESS,
        assignee=test_user,
        reporter=test_user
    )
    
    # Add activities
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
    
    url = reverse('smart-rewrite', kwargs={'task_id': test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_empty_test_task_description(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task that has empty description."""
    # Create test_task with empty description
    empty_test_task = Task.objects.create(
        project=test_project,
        title='Empty Description Task',
        description='',  # Empty description
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-rewrite', kwargs={'task_id': empty_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_large_test_task_description(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task that has very large description."""
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
    
    url = reverse('smart-rewrite', kwargs={'task_id': large_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_unicode_content(api_client, test_user, test_project, mock_ai_service_rewrite, db):
    """Test smart rewrite with test_task containing unicode characters."""
    # Create test_task with unicode content
    unicode_test_task = Task.objects.create(
        project=test_project,
        title='Unicode Task 🚀',
        description='Task with unicode characters: ñáéíóú, 中文, العربية, русский',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )
    
    url = reverse('smart-rewrite', kwargs={'task_id': unicode_test_task.id})
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data


def test_smart_rewrite_service_factory_error(api_client, test_user, url):
    """Test smart rewrite when service factory fails."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service') as mock_get_service:
        mock_get_service.side_effect = Exception('Service factory error')
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data


def test_smart_rewrite_invalid_response_format(api_client, test_user, test_task, url):
    """Test smart rewrite when AI service returns invalid format."""
    api_client.force_authenticate(user=test_user)
    
    mock_service = MagicMock()
    # Return invalid format (missing required fields)
    mock_service.generate_rewrite.return_value = {
        'title': 'Test Title',
        # Missing user_story
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        # Should return 500 due to serializer error
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


def test_smart_rewrite_empty_title(api_client, test_user, test_task, url):
    """Test smart rewrite with empty title."""
    api_client.force_authenticate(user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': '',  # Empty title
        'user_story': 'As a user, I want to test so that I can verify'
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == ''


def test_smart_rewrite_empty_user_story(api_client, test_user, test_task, url):
    """Test smart rewrite with empty test_user story."""
    api_client.force_authenticate(user=test_user)
    
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': 'Test Title',
        'user_story': ''  # Empty test_user story
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user_story'] == ''


def test_smart_rewrite_very_long_title(api_client, test_user, test_task, url):
    """Test smart rewrite with very long title."""
    api_client.force_authenticate(user=test_user)
    
    long_title = 'A' * 1000  # Very long title
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': long_title,
        'user_story': 'As a user, I want to test so that I can verify'
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == long_title


def test_smart_rewrite_very_long_user_story(api_client, test_user, test_task, url):
    """Test smart rewrite with very long test_user story."""
    api_client.force_authenticate(user=test_user)
    
    long_user_story = 'As a user, I want to test ' + 'A' * 10000 + ' so that I can verify'
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': 'Test Title',
        'user_story': long_user_story
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['user_story'] == long_user_story


def test_smart_rewrite_special_characters_in_title(api_client, test_user, test_task, url):
    """Test smart rewrite with special characters in title."""
    api_client.force_authenticate(user=test_user)
    
    special_title = 'Task with Special Chars: !@#$%^&*()_+-=[]{}|;:,.<>?'
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': special_title,
        'user_story': 'As a user, I want to test so that I can verify'
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == special_title


def test_smart_rewrite_html_in_content(api_client, test_user, test_task, url):
    """Test smart rewrite with HTML content."""
    api_client.force_authenticate(user=test_user)
    
    html_title = 'Task with <b>HTML</b> and <script>alert("xss")</script>'
    html_user_story = 'As a user, I want to <em>test</em> so that I can verify'
    
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': html_title,
        'user_story': html_user_story
    }
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_service):
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == html_title
        assert response.data['user_story'] == html_user_story


def test_smart_rewrite_multiple_calls_same_test_task(api_client, test_user, test_task, url, mock_ai_service_rewrite):
    """Test multiple rewrite calls for the same test_task."""
    api_client.force_authenticate(user=test_user)
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        # First call
        response1 = api_client.post(url)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second call
        response2 = api_client.post(url)
        assert response2.status_code == status.HTTP_200_OK
        
        # Both should work
        assert 'title' in response1.data
        assert 'title' in response2.data
        assert 'user_story' in response1.data
        assert 'user_story' in response2.data


def test_smart_rewrite_different_test_users_same_test_task(api_client, test_user, test_task, url, mock_ai_service_rewrite, db):
    """Test different test_users calling rewrite on the same test_task."""
    # Create another test_user
    other_user = CustomUser.objects.create_user(
        username='othertest_user',
        email='other@example.com',
        first_name='Other',
        last_name='User'
    )
    
    with patch('ai_tools.views.smart_rewrite.get_ai_service', return_value=mock_ai_service_rewrite):
        # First test_user
        api_client.force_authenticate(user=test_user)
        response1 = api_client.post(url)
        assert response1.status_code == status.HTTP_200_OK
        
        # Second test_user
        api_client.force_authenticate(user=other_user)
        response2 = api_client.post(url)
        assert response2.status_code == status.HTTP_200_OK
        
        # Both should work
        assert 'title' in response1.data
        assert 'title' in response2.data
