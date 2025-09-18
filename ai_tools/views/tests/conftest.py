"""
Shared pytest fixtures for AI tools views tests.
"""
import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser
from tasks.models import Task, TaskStatus, Project
from ai_tools.models import AIOperation


@pytest.fixture
def api_client():
    """Provide an API client for testing."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    return CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def other_user(db):
    """Create another test user."""
    return CustomUser.objects.create_user(
        username='otheruser',
        email='other@example.com',
        first_name='Other',
        last_name='User'
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return CustomUser.objects.create_user(
        username='admin',
        email='admin@example.com',
        first_name='Admin',
        last_name='User',
        is_staff=True,
        is_superuser=True
    )


@pytest.fixture
def inactive_user(db):
    """Create an inactive user."""
    return CustomUser.objects.create_user(
        username='inactive',
        email='inactive@example.com',
        first_name='Inactive',
        last_name='User',
        is_active=False
    )


@pytest.fixture
def test_project(db, test_user):
    """Create a test project."""
    return Project.objects.create(
        code='TST',
        name='Test Project',
        description='Test project for AI tools',
        owner=test_user
    )


@pytest.fixture
def other_project(db, other_user):
    """Create a project owned by another user."""
    return Project.objects.create(
        code='OTH',
        name='Other Project',
        description='Project owned by other user',
        owner=other_user
    )


@pytest.fixture
def test_task(db, test_project, test_user):
    """Create a test task."""
    return Task.objects.create(
        project=test_project,
        title='Test Task',
        description='A test task for AI operations',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def other_task(db, other_project, other_user):
    """Create a task in another user's project."""
    return Task.objects.create(
        project=other_project,
        title='Other Task',
        description='Task in other user\'s project',
        status=TaskStatus.TODO,
        assignee=other_user,
        reporter=other_user
    )


@pytest.fixture
def completed_task(db, test_project, test_user):
    """Create a completed task."""
    return Task.objects.create(
        project=test_project,
        title='Completed Task',
        description='A completed task for testing',
        status=TaskStatus.DONE,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def in_progress_task(db, test_project, test_user):
    """Create an in-progress task."""
    return Task.objects.create(
        project=test_project,
        title='In Progress Task',
        description='An in-progress task for testing',
        status=TaskStatus.IN_PROGRESS,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def blocked_task(db, test_project, test_user):
    """Create a blocked task."""
    return Task.objects.create(
        project=test_project,
        title='Blocked Task',
        description='A blocked task for testing',
        status=TaskStatus.BLOCKED,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def task_with_tags(db, test_project, test_user):
    """Create a task with tags."""
    return Task.objects.create(
        project=test_project,
        title='Tagged Task',
        description='A task with tags for testing',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user,
        tags=['frontend', 'backend', 'testing']
    )


@pytest.fixture
def task_with_estimate(db, test_project, test_user):
    """Create a task with an estimate."""
    return Task.objects.create(
        project=test_project,
        title='Estimated Task',
        description='A task with an estimate for testing',
        status=TaskStatus.TODO,
        estimate=5,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def large_task(db, test_project, test_user):
    """Create a task with large content."""
    return Task.objects.create(
        project=test_project,
        title='Large Task',
        description='A' * 10000,  # 10KB description
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def unicode_task(db, test_project, test_user):
    """Create a task with unicode content."""
    return Task.objects.create(
        project=test_project,
        title='Unicode Task 🚀',
        description='Task with unicode: ñáéíóú, 中文, العربية, русский, 🎉✨🌟',
        status=TaskStatus.TODO,
        assignee=test_user,
        reporter=test_user
    )


@pytest.fixture
def minimal_task(db, test_project, test_user):
    """Create a task with minimal content."""
    return Task.objects.create(
        project=test_project,
        title='Min',  # Minimum valid title
        status=TaskStatus.TODO
    )


@pytest.fixture
def ai_operation(db, test_task, test_user):
    """Create a test AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='PENDING',
        user=test_user
    )


@pytest.fixture
def completed_ai_operation(db, test_task, test_user):
    """Create a completed AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='COMPLETED',
        result={'summary': 'Test summary'},
        user=test_user
    )


@pytest.fixture
def failed_ai_operation(db, test_task, test_user):
    """Create a failed AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='FAILED',
        error_message='Test error message',
        user=test_user
    )


@pytest.fixture
def processing_ai_operation(db, test_task, test_user):
    """Create a processing AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='SUMMARY',
        status='PROCESSING',
        user=test_user
    )


@pytest.fixture
def estimate_operation(db, test_task, test_user):
    """Create an estimate AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='ESTIMATE',
        status='COMPLETED',
        result={'suggested_points': 5, 'confidence': 0.8},
        user=test_user
    )


@pytest.fixture
def rewrite_operation(db, test_task, test_user):
    """Create a rewrite AI operation."""
    return AIOperation.objects.create(
        task=test_task,
        operation_type='REWRITE',
        status='COMPLETED',
        result={'title': 'Enhanced Title', 'user_story': 'As a user...'},
        user=test_user
    )


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    from unittest.mock import MagicMock
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 5,
        'confidence': 0.8,
        'similar_task_ids': ['task-1', 'task-2'],
        'rationale': 'Based on similar tasks in the system'
    }
    mock_service.generate_rewrite.return_value = {
        'title': 'Enhanced Test Task',
        'user_story': 'As a user, I want to test the system so that I can verify functionality'
    }
    mock_service.generate_summary.return_value = 'This is a test summary of the task.'
    
    return mock_service


@pytest.fixture
def mock_ai_service_estimate():
    """Mock AI service specifically for estimate testing."""
    from unittest.mock import MagicMock
    
    mock_service = MagicMock()
    mock_service.generate_estimate.return_value = {
        'suggested_points': 5,
        'confidence': 0.85,
        'similar_task_ids': ['task-1', 'task-2'],
        'rationale': 'Based on similar tasks in the system'
    }
    return mock_service


@pytest.fixture
def mock_ai_service_rewrite():
    """Mock AI service specifically for rewrite testing."""
    from unittest.mock import MagicMock
    
    mock_service = MagicMock()
    mock_service.generate_rewrite.return_value = {
        'title': 'Enhanced Test Task',
        'user_story': 'As a user, I want to test the system so that I can verify functionality'
    }
    return mock_service


@pytest.fixture
def mock_celery_task():
    """Mock Celery task for testing."""
    from unittest.mock import MagicMock
    
    mock_task = MagicMock()
    mock_task.delay.return_value = MagicMock()
    
    return mock_task


@pytest.fixture
def sample_tasks(db, test_project, test_user):
    """Create a collection of sample tasks for comprehensive testing."""
    tasks = []
    
    # Create tasks with different statuses
    statuses = [TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.BLOCKED]
    for i, status in enumerate(statuses):
        task = Task.objects.create(
            project=test_project,
            title=f'Task {i+1} - {status}',
            description=f'Task {i+1} in {status} status',
            status=status,
            assignee=test_user,
            reporter=test_user
        )
        tasks.append(task)
    
    # Create tasks with different estimates
    estimates = [1, 2, 3, 5, 8, 13, 21]
    for i, estimate in enumerate(estimates):
        task = Task.objects.create(
            project=test_project,
            title=f'Task with {estimate} points',
            description=f'Task estimated at {estimate} points',
            status=TaskStatus.DONE,
            estimate=estimate,
            assignee=test_user,
            reporter=test_user
        )
        tasks.append(task)
    
    # Create tasks with different tags
    tag_sets = [
        ['frontend'],
        ['backend'],
        ['testing'],
        ['frontend', 'backend'],
        ['frontend', 'testing'],
        ['backend', 'testing'],
        ['frontend', 'backend', 'testing']
    ]
    for i, tags in enumerate(tag_sets):
        task = Task.objects.create(
            project=test_project,
            title=f'Task with tags {i+1}',
            description=f'Task with tags: {", ".join(tags)}',
            status=TaskStatus.DONE,
            assignee=test_user,
            reporter=test_user,
            tags=tags
        )
        tasks.append(task)
    
    return tasks


@pytest.fixture
def sample_operations(db, sample_tasks, test_user):
    """Create a collection of sample AI operations for testing."""
    operations = []
    
    # Create operations for different tasks
    for i, task in enumerate(sample_tasks[:5]):  # Use first 5 tasks
        operation = AIOperation.objects.create(
            task=task,
            operation_type='SUMMARY',
            status='COMPLETED',
            result={'summary': f'Summary for task {i+1}'},
            user=test_user
        )
        operations.append(operation)
    
    return operations
