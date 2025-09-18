"""
Pytest fixtures for Tasks app tests.
Provides reusable test data and setup for consistent testing.
"""
import pytest
from rest_framework.test import APIClient
from accounts.models import CustomUser
from tasks.models import Task, Project, TaskStatus


@pytest.fixture
def api_client():
    """Provide an API client for testing."""
    return APIClient()


@pytest.fixture
def users(db):
    """Create test users for various testing scenarios."""
    active_user = CustomUser.objects.create_user(
        username='testuser1',
        email='test1@example.com',
        password='testpass123',
        is_active=True
    )
    inactive_user = CustomUser.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123',
        is_active=False
    )
    dev_user = CustomUser.objects.create_user(
        username='testdev',
        email='dev@test.com',
        password='testpass123'
    )
    qa_user = CustomUser.objects.create_user(
        username='testqa',
        email='qa@test.com',
        password='testpass123'
    )
    pm_user = CustomUser.objects.create_user(
        username='testpm',
        email='pm@test.com',
        password='testpass123'
    )
    
    return {
        'user1': active_user,
        'user2': inactive_user,
        'active': active_user,
        'inactive': inactive_user,
        'dev': dev_user,
        'qa': qa_user,
        'pm': pm_user
    }


@pytest.fixture
def projects(db, users):
    """Create test projects for task organization."""
    main_project = Project.objects.create(
        code='TST',
        name='Test Project',
        description='Main project for testing',
        owner=users['pm'],
        is_active=True
    )
    api_project = Project.objects.create(
        code='API',
        name='API Development',
        description='Backend API development',
        owner=users['dev'],
        is_active=True
    )
    web_project = Project.objects.create(
        code='WEB',
        name='Web Frontend',
        description='Frontend web development',
        owner=users['qa'],
        is_active=True
    )
    inactive_project = Project.objects.create(
        code='OLD',
        name='Legacy Project',
        description='Inactive legacy project',
        owner=users['pm'],
        is_active=False
    )
    
    return {
        'main': main_project,
        'api': api_project,
        'web': web_project,
        'inactive': inactive_project
    }


@pytest.fixture
def tag_names():
    """Provide common tag names for testing."""
    return [
        'backend', 'frontend', 'urgent', 'testing', 'performance', 
        'security', 'ui', 'api', 'database'
    ]


@pytest.fixture
def authenticated_client(api_client, users):
    """Provide an authenticated API client using the first user."""
    api_client.force_authenticate(user=users['user1'])
    return api_client


@pytest.fixture
def sample_task(db, users, projects):
    """Create a basic sample task for testing."""
    return Task.objects.create(
        project=projects['main'],
        title='Sample Task',
        description='A sample task for testing',
        status=TaskStatus.TODO,
        reporter=users['user1']
    )


@pytest.fixture
def sample_tasks(db, users, projects):
    """Create a variety of sample tasks for comprehensive testing."""
    # Basic TODO task
    todo_task = Task.objects.create(
        project=projects['web'],
        title='TODO Task',
        description='A task in TODO status',
        status=TaskStatus.TODO,
        reporter=users['user1'],
        tags=['frontend']
    )
    
    # In Progress task with estimate and assignee
    in_progress_task = Task.objects.create(
        project=projects['api'],
        title='In Progress Task',
        description='A task currently being worked on',
        status=TaskStatus.IN_PROGRESS,
        estimate=5,
        assignee=users['dev'],
        reporter=users['pm'],
        tags=['backend', 'urgent']
    )
    
    # Blocked task
    blocked_task = Task.objects.create(
        project=projects['main'],
        title='Blocked Task',
        description='A task that is currently blocked',
        status=TaskStatus.BLOCKED,
        estimate=8,
        assignee=users['qa'],
        reporter=users['pm'],
        tags=['testing']
    )
    
    # Completed task
    done_task = Task.objects.create(
        project=projects['api'],
        title='Completed Task',
        description='A task that has been completed',
        status=TaskStatus.DONE,
        estimate=3,
        assignee=users['dev'],
        reporter=users['user1'],
        tags=['api', 'backend']
    )
    
    return {
        'todo': todo_task,
        'in_progress': in_progress_task,
        'blocked': blocked_task,
        'done': done_task
    }


@pytest.fixture
def performance_test_data(db, users, projects):
    """Create test data for performance testing."""
    tasks = []
    
    # Create 100 tasks for performance testing across different projects
    for i in range(100):
        # Distribute tasks across projects
        if i % 3 == 0:
            project = projects['main']
        elif i % 3 == 1:
            project = projects['api']
        else:
            project = projects['web']
        
        # Determine tags based on task number
        task_tags = []
        if i % 5 == 0:
            task_tags = ['backend']
        elif i % 5 == 1:
            task_tags = ['frontend']
        elif i % 5 == 2:
            task_tags = ['testing']
            
        task = Task.objects.create(
            project=project,
            title=f'Performance Test Task {i}',
            description=f'Task {i} for performance testing',
            status=TaskStatus.TODO if i % 4 == 0 else TaskStatus.IN_PROGRESS if i % 4 == 1 else TaskStatus.BLOCKED if i % 4 == 2 else TaskStatus.DONE,
            estimate=i % 10 + 1 if i % 4 == 3 else None,  # Only DONE tasks have estimates
            assignee=users['dev'] if i % 3 == 0 else users['qa'] if i % 3 == 1 else None,
            reporter=users['pm'],
            tags=task_tags
        )
        
        tasks.append(task)
    
    return tasks


@pytest.fixture
def similarity_test_tasks(db, users, projects):
    """Create tasks for similarity algorithm testing."""
    # Base task to find similarities for
    base_task = Task.objects.create(
        project=projects['main'],
        title='Find similar tasks for this one',
        description='This is the base task for similarity testing',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm'],
        tags=['backend']
    )
    
    # Similar task - same assignee
    similar_assignee = Task.objects.create(
        project=projects['api'],
        title='Different title but same assignee',
        description='Different description',
        status=TaskStatus.DONE,
        estimate=5,
        assignee=users['dev'],
        reporter=users['pm']
    )
    
    # Similar task - overlapping tags
    similar_tags = Task.objects.create(
        project=projects['web'],
        title='Task with similar tags',
        description='This task has overlapping tags',
        status=TaskStatus.DONE,
        estimate=3,
        assignee=users['qa'],
        reporter=users['pm'],
        tags=['backend', 'api']
    )
    
    # Similar task - title match
    similar_title = Task.objects.create(
        project=projects['main'],
        title='Find similar implementation',
        description='Different description but similar title',
        status=TaskStatus.DONE,
        estimate=2,
        assignee=users['qa'],
        reporter=users['pm']
    )
    
    # Similar task - description match
    similar_description = Task.objects.create(
        project=projects['api'],
        title='Completely different title',
        description='This is the base description for testing',
        status=TaskStatus.DONE,
        estimate=4,
        assignee=users['qa'],
        reporter=users['pm']
    )
    
    # Dissimilar task
    dissimilar = Task.objects.create(
        project=projects['web'],
        title='Unrelated task',
        description='No similarity whatsoever',
        status=TaskStatus.DONE,
        estimate=7,
        assignee=users['user1'],
        reporter=users['user1'],
        tags=['performance']
    )
    
    return {
        'base': base_task,
        'similar_assignee': similar_assignee,
        'similar_tags': similar_tags,
        'similar_title': similar_title,
        'similar_description': similar_description,
        'dissimilar': dissimilar
    }