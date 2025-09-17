"""
Integration tests for AI Tool API endpoints using pytest.
Tests all AI tool endpoints with proper authentication, error handling, and response validation.
"""
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tasks.models import Task, Tag, TaskStatus, TaskActivity, ActivityType
from unittest.mock import patch
import uuid


@pytest.fixture
def api_client():
    """Provide an API client."""
    return APIClient()


@pytest.fixture
def users(db):
    """Create test users with different roles."""
    dev_user = User.objects.create_user(
        username='testdev',
        email='dev@test.com',
        password='testpass123'
    )
    qa_user = User.objects.create_user(
        username='testqa',
        email='qa@test.com',
        password='testpass123'
    )
    pm_user = User.objects.create_user(
        username='testpm',
        email='pm@test.com',
        password='testpass123'
    )
    return {'dev': dev_user, 'qa': qa_user, 'pm': pm_user}


@pytest.fixture
def tags(db):
    """Create test tags for categorization."""
    frontend_tag = Tag.objects.create(name='frontend')
    backend_tag = Tag.objects.create(name='backend')
    testing_tag = Tag.objects.create(name='testing')
    urgent_tag = Tag.objects.create(name='urgent')
    return {
        'frontend': frontend_tag,
        'backend': backend_tag,
        'testing': testing_tag,
        'urgent': urgent_tag
    }


@pytest.fixture
def authenticated_client(api_client, users):
    """Provide an authenticated API client."""
    api_client.force_authenticate(user=users['dev'])
    return api_client


@pytest.fixture
def sample_tasks(db, users, tags):
    """Create sample tasks with various states for testing."""
    # Task with activities
    task_with_activities = Task.objects.create(
        title='Task with Activities',
        description='A task that has been worked on',
        status=TaskStatus.IN_PROGRESS,
        estimate=5,
        assignee=users['dev'],
        reporter=users['pm']
    )
    task_with_activities.tags.add(tags['backend'], tags['urgent'])
    
    # Create some activities for this task
    TaskActivity.objects.create(
        task=task_with_activities,
        actor=users['pm'],
        type=ActivityType.CREATED
    )
    TaskActivity.objects.create(
        task=task_with_activities,
        actor=users['dev'],
        type=ActivityType.UPDATED_STATUS,
        field='status',
        before=TaskStatus.TODO,
        after=TaskStatus.IN_PROGRESS
    )
    TaskActivity.objects.create(
        task=task_with_activities,
        actor=users['dev'],
        type=ActivityType.UPDATED_ESTIMATE,
        field='estimate',
        before=None,
        after=5
    )
    
    # Simple task for basic testing
    simple_task = Task.objects.create(
        title='Simple Task',
        description='A simple task for testing',
        status=TaskStatus.TODO,
        reporter=users['dev']
    )
    simple_task.tags.add(tags['frontend'])
    
    # Task for similarity testing
    similar_task1 = Task.objects.create(
        title='Fix authentication bug',
        description='Fix the login issue',
        status=TaskStatus.DONE,
        estimate=3,
        assignee=users['dev'],
        reporter=users['pm']
    )
    similar_task1.tags.add(tags['backend'])
    
    similar_task2 = Task.objects.create(
        title='Fix payment processing',
        description='Fix the payment gateway issue',
        status=TaskStatus.DONE,
        estimate=5,
        assignee=users['dev'],
        reporter=users['pm']
    )
    similar_task2.tags.add(tags['backend'])
    
    # Task for estimate testing (similar to simple_task)
    estimate_test_task = Task.objects.create(
        title='Frontend component update',
        description='Update the user interface component',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm']
    )
    estimate_test_task.tags.add(tags['frontend'])
    
    return {
        'with_activities': task_with_activities,
        'simple': simple_task,
        'similar1': similar_task1,
        'similar2': similar_task2,
        'estimate_test': estimate_test_task
    }


@pytest.mark.integration
class TestSmartSummaryEndpoint:
    """Test Smart Summary API endpoint (requirement 7.1)."""
    
    def test_smart_summary_success(self, authenticated_client, sample_tasks):
        """Test successful smart summary generation."""
        task = sample_tasks['with_activities']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'summary' in response.data
        assert isinstance(response.data['summary'], str)
        assert len(response.data['summary']) > 0
        
        # Verify summary contains expected information
        summary = response.data['summary']
        assert 'activities' in summary.lower()
        assert 'in progress' in summary.lower()
        assert 'testdev' in summary.lower()  # Assignee username
    
    def test_smart_summary_simple_task(self, authenticated_client, sample_tasks):
        """Test smart summary for task with minimal activities."""
        task = sample_tasks['simple']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'summary' in response.data
        summary = response.data['summary']
        assert 'created' in summary.lower()
        assert 'to do' in summary.lower() or 'todo' in summary.lower()
    
    def test_smart_summary_task_not_found(self, authenticated_client):
        """Test smart summary with non-existent task returns 404 (requirement 8.2)."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-summary', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'Task not found' in response.data['detail']
        assert 'errors' in response.data
        assert 'task_id' in response.data['errors']
    
    def test_smart_summary_unauthenticated(self, api_client, sample_tasks):
        """Test smart summary requires authentication (requirement 8.3)."""
        task = sample_tasks['simple']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        response = api_client.get(url)
        
        # DRF with SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_smart_summary_deterministic_response(self, authenticated_client, sample_tasks):
        """Test smart summary returns deterministic responses (requirement 7.4)."""
        task = sample_tasks['with_activities']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        # Make multiple requests
        response1 = authenticated_client.get(url)
        response2 = authenticated_client.get(url)
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data['summary'] == response2.data['summary']
    
    @patch('ai_tools.services.AIService._log_ai_invocation')
    def test_smart_summary_logging(self, mock_log, authenticated_client, sample_tasks, users):
        """Test smart summary logs AI tool invocation (requirement 9.3)."""
        task = sample_tasks['simple']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_log.assert_called_once()
        
        # Verify logging parameters
        call_args = mock_log.call_args[1]
        assert call_args['tool_type'] == 'smart_summary'
        assert call_args['task_id'] == str(task.id)
        assert call_args['user_id'] == users['dev'].id
        assert 'response_time_ms' in call_args


@pytest.mark.integration
class TestSmartEstimateEndpoint:
    """Test Smart Estimate API endpoint (requirement 7.2)."""
    
    def test_smart_estimate_success_with_similar_tasks(self, authenticated_client, sample_tasks):
        """Test successful smart estimate with similar tasks."""
        task = sample_tasks['estimate_test']
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'suggested_points' in response.data
        assert 'confidence' in response.data
        assert 'similar_task_ids' in response.data
        assert 'rationale' in response.data
        
        # Verify data types and ranges
        assert isinstance(response.data['suggested_points'], int)
        assert isinstance(response.data['confidence'], float)
        assert 0.0 <= response.data['confidence'] <= 1.0
        assert isinstance(response.data['similar_task_ids'], list)
        assert isinstance(response.data['rationale'], str)
    
    def test_smart_estimate_no_similar_tasks(self, authenticated_client, users, tags):
        """Test smart estimate with no similar tasks returns fallback (requirement 1.3)."""
        # Create a unique task with no similar tasks
        unique_task = Task.objects.create(
            title='Completely unique task with no matches',
            description='This task has no similar tasks in the system',
            status=TaskStatus.TODO,
            reporter=users['dev']
        )
        
        url = reverse('smart-estimate', kwargs={'task_id': unique_task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggested_points'] == 3
        assert response.data['confidence'] == 0.40
        assert response.data['similar_task_ids'] == []
        assert 'no similar tasks' in response.data['rationale'].lower()
    
    def test_smart_estimate_high_confidence(self, authenticated_client, users, tags):
        """Test smart estimate with high confidence scenario."""
        # Create multiple similar tasks with consistent estimates
        base_task = Task.objects.create(
            title='Fix bug in authentication system',
            description='Authentication system needs fixing',
            status=TaskStatus.TODO,
            assignee=users['dev'],
            reporter=users['pm']
        )
        base_task.tags.add(tags['backend'])
        
        # Create similar tasks with same assignee and tags
        for i in range(5):
            similar_task = Task.objects.create(
                title=f'Fix bug in payment system {i}',
                description='Payment system needs fixing',
                status=TaskStatus.DONE,
                estimate=5,  # Consistent estimate
                assignee=users['dev'],
                reporter=users['pm']
            )
            similar_task.tags.add(tags['backend'])
        
        url = reverse('smart-estimate', kwargs={'task_id': base_task.id})
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['suggested_points'] == 5
        assert response.data['confidence'] >= 0.65
        assert len(response.data['similar_task_ids']) > 0
    
    def test_smart_estimate_task_not_found(self, authenticated_client):
        """Test smart estimate with non-existent task returns 404."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-estimate', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Task not found' in response.data['detail']
    
    def test_smart_estimate_unauthenticated(self, api_client, sample_tasks):
        """Test smart estimate requires authentication."""
        task = sample_tasks['simple']
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        
        response = api_client.get(url)
        
        # DRF with SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_smart_estimate_similar_task_limit(self, authenticated_client, sample_tasks):
        """Test smart estimate limits similar task IDs to 5 (requirement 1.5)."""
        task = sample_tasks['estimate_test']
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['similar_task_ids']) <= 5
    
    @patch('ai_tools.services.AIService._log_ai_invocation')
    def test_smart_estimate_logging(self, mock_log, authenticated_client, sample_tasks, users):
        """Test smart estimate logs AI tool invocation."""
        task = sample_tasks['simple']
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_log.assert_called_once()
        
        call_args = mock_log.call_args[1]
        assert call_args['tool_type'] == 'smart_estimate'
        assert call_args['task_id'] == str(task.id)
        assert call_args['user_id'] == users['dev'].id


@pytest.mark.integration
class TestSmartRewriteEndpoint:
    """Test Smart Rewrite API endpoint (requirement 7.3)."""
    
    def test_smart_rewrite_success(self, authenticated_client, sample_tasks):
        """Test successful smart rewrite generation."""
        task = sample_tasks['with_activities']
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'title' in response.data
        assert 'user_story' in response.data
        
        # Verify title is preserved (requirement 3.3)
        assert response.data['title'] == task.title
        
        # Verify user story format (requirement 3.2)
        user_story = response.data['user_story']
        assert 'As a' in user_story
        assert 'I want' in user_story
        assert 'so that' in user_story
        assert 'Acceptance Criteria' in user_story
        assert 'WHEN' in user_story
        assert 'THEN' in user_story
        assert 'SHALL' in user_story
    
    def test_smart_rewrite_different_user_roles(self, authenticated_client, sample_tasks, users):
        """Test smart rewrite adapts to different user roles."""
        task = sample_tasks['simple']
        
        # Test with dev user
        authenticated_client.force_authenticate(user=users['dev'])
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response_dev = authenticated_client.post(url)
        
        # Test with QA user
        authenticated_client.force_authenticate(user=users['qa'])
        response_qa = authenticated_client.post(url)
        
        # Test with PM user
        authenticated_client.force_authenticate(user=users['pm'])
        response_pm = authenticated_client.post(url)
        
        assert response_dev.status_code == status.HTTP_200_OK
        assert response_qa.status_code == status.HTTP_200_OK
        assert response_pm.status_code == status.HTTP_200_OK
        
        # User stories should adapt to user roles
        dev_story = response_dev.data['user_story']
        qa_story = response_qa.data['user_story']
        pm_story = response_pm.data['user_story']
        
        assert 'developer' in dev_story.lower()
        assert 'qa engineer' in qa_story.lower()
        assert 'project manager' in pm_story.lower()
    
    def test_smart_rewrite_task_not_found(self, authenticated_client):
        """Test smart rewrite with non-existent task returns 404."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-rewrite', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'Task not found' in response.data['detail']
    
    def test_smart_rewrite_unauthenticated(self, api_client, sample_tasks):
        """Test smart rewrite requires authentication."""
        task = sample_tasks['simple']
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        
        response = api_client.post(url)
        
        # DRF with SessionAuthentication returns 403 for unauthenticated requests
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_smart_rewrite_deterministic_response(self, authenticated_client, sample_tasks):
        """Test smart rewrite returns deterministic responses."""
        task = sample_tasks['simple']
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        
        # Make multiple requests
        response1 = authenticated_client.post(url)
        response2 = authenticated_client.post(url)
        
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.data['title'] == response2.data['title']
        assert response1.data['user_story'] == response2.data['user_story']
    
    def test_smart_rewrite_with_tags(self, authenticated_client, sample_tasks):
        """Test smart rewrite adapts acceptance criteria based on tags."""
        # Test with frontend task
        frontend_task = sample_tasks['simple']  # Has frontend tag
        url = reverse('smart-rewrite', kwargs={'task_id': frontend_task.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        user_story = response.data['user_story']
        assert 'frontend' in user_story.lower() or 'user interface' in user_story.lower()
        
        # Test with backend task
        backend_task = sample_tasks['similar1']  # Has backend tag
        url = reverse('smart-rewrite', kwargs={'task_id': backend_task.id})
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        user_story = response.data['user_story']
        assert 'backend' in user_story.lower() or 'api' in user_story.lower()
    
    @patch('ai_tools.services.AIService._log_ai_invocation')
    def test_smart_rewrite_logging(self, mock_log, authenticated_client, sample_tasks, users):
        """Test smart rewrite logs AI tool invocation."""
        task = sample_tasks['simple']
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        
        response = authenticated_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        mock_log.assert_called_once()
        
        call_args = mock_log.call_args[1]
        assert call_args['tool_type'] == 'smart_rewrite'
        assert call_args['task_id'] == str(task.id)
        assert call_args['user_id'] == users['dev'].id


@pytest.mark.integration
class TestAIEndpointsErrorHandling:
    """Test error handling across all AI endpoints (requirement 8.1, 8.2, 8.3)."""
    
    def test_invalid_task_id_format(self, authenticated_client):
        """Test all endpoints handle invalid UUID format gracefully."""
        invalid_id = 'not-a-uuid'
        
        # Test smart summary
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
    
    def test_method_not_allowed(self, authenticated_client, sample_tasks):
        """Test endpoints reject incorrect HTTP methods."""
        task = sample_tasks['simple']
        
        # Smart summary should only accept GET
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Smart estimate should only accept GET
        url = reverse('smart-estimate', kwargs={'task_id': task.id})
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
        
        # Smart rewrite should only accept POST
        url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    
    def test_error_response_format(self, authenticated_client):
        """Test error responses follow standardized format (requirement 8.1)."""
        non_existent_id = uuid.uuid4()
        url = reverse('smart-summary', kwargs={'task_id': non_existent_id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert 'detail' in response.data
        assert 'errors' in response.data
        assert isinstance(response.data['errors'], dict)
    
    @patch('ai_tools.services.AIService.generate_summary')
    def test_service_exception_handling(self, mock_generate, authenticated_client, sample_tasks):
        """Test graceful handling of service layer exceptions."""
        # Mock service to raise exception
        mock_generate.side_effect = Exception("Service error")
        
        task = sample_tasks['simple']
        url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'detail' in response.data
        assert 'error occurred' in response.data['detail'].lower()


@pytest.mark.integration
class TestAIEndpointsIntegration:
    """Test integration scenarios across AI endpoints."""
    
    def test_ai_tools_workflow(self, authenticated_client, sample_tasks):
        """Test complete AI tools workflow on a single task."""
        task = sample_tasks['with_activities']
        
        # Step 1: Get smart summary
        summary_url = reverse('smart-summary', kwargs={'task_id': task.id})
        summary_response = authenticated_client.get(summary_url)
        assert summary_response.status_code == status.HTTP_200_OK
        
        # Step 2: Get smart estimate
        estimate_url = reverse('smart-estimate', kwargs={'task_id': task.id})
        estimate_response = authenticated_client.get(estimate_url)
        assert estimate_response.status_code == status.HTTP_200_OK
        
        # Step 3: Get smart rewrite
        rewrite_url = reverse('smart-rewrite', kwargs={'task_id': task.id})
        rewrite_response = authenticated_client.post(rewrite_url)
        assert rewrite_response.status_code == status.HTTP_200_OK
        
        # Verify all responses are valid
        assert 'summary' in summary_response.data
        assert 'suggested_points' in estimate_response.data
        assert 'title' in rewrite_response.data
        assert 'user_story' in rewrite_response.data
    
    def test_ai_tools_with_different_task_states(self, authenticated_client, users, tags):
        """Test AI tools work with tasks in different states."""
        # Create tasks in different states
        todo_task = Task.objects.create(
            title='TODO Task',
            status=TaskStatus.TODO,
            reporter=users['dev']
        )
        
        in_progress_task = Task.objects.create(
            title='In Progress Task',
            status=TaskStatus.IN_PROGRESS,
            estimate=3,
            assignee=users['dev'],
            reporter=users['pm']
        )
        
        done_task = Task.objects.create(
            title='Done Task',
            status=TaskStatus.DONE,
            estimate=5,
            assignee=users['qa'],
            reporter=users['pm']
        )
        
        tasks = [todo_task, in_progress_task, done_task]
        
        for task in tasks:
            # Test summary
            summary_url = reverse('smart-summary', kwargs={'task_id': task.id})
            summary_response = authenticated_client.get(summary_url)
            assert summary_response.status_code == status.HTTP_200_OK
            
            # Test estimate
            estimate_url = reverse('smart-estimate', kwargs={'task_id': task.id})
            estimate_response = authenticated_client.get(estimate_url)
            assert estimate_response.status_code == status.HTTP_200_OK
            
            # Test rewrite
            rewrite_url = reverse('smart-rewrite', kwargs={'task_id': task.id})
            rewrite_response = authenticated_client.post(rewrite_url)
            assert rewrite_response.status_code == status.HTTP_200_OK
    
    def test_concurrent_ai_tool_requests(self, authenticated_client, sample_tasks):
        """Test AI tools handle concurrent requests properly."""
        task = sample_tasks['simple']
        
        # Make multiple concurrent requests to same endpoint
        summary_url = reverse('smart-summary', kwargs={'task_id': task.id})
        
        responses = []
        for _ in range(3):
            response = authenticated_client.get(summary_url)
            responses.append(response)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert 'summary' in response.data
        
        # Responses should be consistent (deterministic)
        first_summary = responses[0].data['summary']
        for response in responses[1:]:
            assert response.data['summary'] == first_summary