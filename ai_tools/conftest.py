"""
Pytest fixtures for AI Tools tests.
Provides reusable test data and setup for consistent testing.
"""
import pytest
from django.contrib.auth.models import User
from tasks.models import Task, TaskActivity, ActivityType, Tag, TaskStatus


@pytest.fixture
def users(db):
    """Create test users with different roles based on username patterns."""
    return {
        'dev': User.objects.create_user(
            username='testdev',
            email='dev@test.com',
            first_name='Test',
            last_name='Developer'
        ),
        'qa': User.objects.create_user(
            username='testqa',
            email='qa@test.com',
            first_name='Test',
            last_name='QA'
        ),
        'pm': User.objects.create_user(
            username='testpm',
            email='pm@test.com',
            first_name='Test',
            last_name='Manager'
        ),
        'user': User.objects.create_user(
            username='testuser',
            email='user@test.com',
            first_name='Test',
            last_name='User'
        )
    }


@pytest.fixture
def tags(db):
    """Create test tags for categorization."""
    return {
        'frontend': Tag.objects.create(name='frontend'),
        'backend': Tag.objects.create(name='backend'),
        'testing': Tag.objects.create(name='testing'),
        'performance': Tag.objects.create(name='performance'),
        'security': Tag.objects.create(name='security')
    }


@pytest.fixture
def basic_task(db, users):
    """Create a basic task for general testing."""
    return Task.objects.create(
        title='Basic test task',
        description='A simple task for testing',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm']
    )


@pytest.fixture
def complex_task(db, users, tags):
    """Create a complex task with estimate and tags."""
    task = Task.objects.create(
        title='Fix authentication bug',
        description='The login system should validate user credentials properly',
        status=TaskStatus.IN_PROGRESS,
        estimate=5,
        assignee=users['dev'],
        reporter=users['qa']
    )
    task.tags.add(tags['backend'], tags['security'])
    return task


@pytest.fixture
def completed_task(db, users, tags):
    """Create a completed task with multiple tags."""
    task = Task.objects.create(
        title='Add user interface improvements',
        description='Update the UI to be more responsive',
        status=TaskStatus.DONE,
        estimate=8,
        assignee=users['qa'],
        reporter=users['pm']
    )
    task.tags.add(tags['frontend'], tags['testing'])
    return task


@pytest.fixture
def blocked_task(db, users, tags):
    """Create a blocked task for status-specific testing."""
    task = Task.objects.create(
        title='Optimize database performance',
        description='Improve query performance for large datasets',
        status=TaskStatus.BLOCKED,
        estimate=13,
        assignee=users['dev'],
        reporter=users['pm']
    )
    task.tags.add(tags['backend'], tags['performance'])
    return task


@pytest.fixture
def sample_tasks(db, basic_task, complex_task, completed_task, blocked_task):
    """Provide a collection of sample tasks for comprehensive testing."""
    return {
        'basic': basic_task,
        'complex': complex_task,
        'completed': completed_task,
        'blocked': blocked_task
    }


@pytest.fixture
def task_with_activities(db, users, basic_task):
    """Create a task with multiple activities for activity-based testing."""
    # Create creation activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['pm'],
        type=ActivityType.CREATED
    )
    
    # Create status update activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['dev'],
        type=ActivityType.UPDATED_STATUS,
        field='status',
        before='TODO',
        after='IN_PROGRESS'
    )
    
    # Create assignee update activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['pm'],
        type=ActivityType.UPDATED_ASSIGNEE,
        field='assignee',
        before=None,
        after={
            'id': users['dev'].id,
            'username': users['dev'].username,
            'email': users['dev'].email
        }
    )
    
    return basic_task


@pytest.fixture
def similar_tasks_set(db, users, tags):
    """Create a set of tasks for similarity algorithm testing."""
    # Task 1: Same assignee as target
    task1 = Task.objects.create(
        title='Similar task 1',
        description='Another task for the same developer',
        status=TaskStatus.DONE,
        estimate=3,
        assignee=users['dev'],
        reporter=users['pm']
    )
    
    # Task 2: Overlapping tags
    task2 = Task.objects.create(
        title='Similar task 2',
        description='A backend task with similar tags',
        status=TaskStatus.DONE,
        estimate=5,
        assignee=users['qa'],
        reporter=users['pm']
    )
    task2.tags.add(tags['backend'])
    
    # Task 3: Title substring match
    task3 = Task.objects.create(
        title='Basic implementation task',
        description='Different description but similar title',
        status=TaskStatus.DONE,
        estimate=2,
        assignee=users['qa'],
        reporter=users['pm']
    )
    
    # Task 4: Description substring match
    task4 = Task.objects.create(
        title='Different title',
        description='A simple task for testing purposes',
        status=TaskStatus.DONE,
        estimate=4,
        assignee=users['qa'],
        reporter=users['pm']
    )
    
    # Task 5: No similarity (control)
    task5 = Task.objects.create(
        title='Completely different task',
        description='No similarity to target task',
        status=TaskStatus.DONE,
        estimate=7,
        assignee=users['user'],
        reporter=users['pm']
    )
    task5.tags.add(tags['performance'])
    
    return {
        'same_assignee': task1,
        'overlapping_tags': task2,
        'title_match': task3,
        'description_match': task4,
        'no_similarity': task5
    }


@pytest.fixture
def tasks_for_estimate_calculation(db, users, tags):
    """Create tasks specifically for estimate calculation testing."""
    estimates = [2, 3, 3, 5, 8]  # Median should be 3
    tasks = []
    
    for i, estimate in enumerate(estimates):
        task = Task.objects.create(
            title=f'Estimate test task {i+1}',
            description='Task for estimate calculation testing',
            status=TaskStatus.DONE,
            estimate=estimate,
            assignee=users['dev'],
            reporter=users['pm']
        )
        task.tags.add(tags['backend'])
        tasks.append(task)
    
    return tasks


@pytest.fixture
def minimal_task(db):
    """Create a task with minimal required fields for edge case testing."""
    return Task.objects.create(
        title='Min',  # Minimum valid title length
        status=TaskStatus.TODO
    )


@pytest.fixture
def multi_tag_task(db, users, tags):
    """Create a task with multiple tags for tag handling tests."""
    task = Task.objects.create(
        title='Multi-tag task',
        description='Task with multiple tags for testing',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm']
    )
    # Add tags in specific order to test sorting
    task.tags.add(tags['frontend'], tags['backend'], tags['testing'])
    return task