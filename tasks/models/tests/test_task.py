import pytest
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from ..task import Task
from ..choices import TaskStatus


@pytest.fixture
def user():
    """Create a test user."""
    return CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def reporter():
    """Create a test reporter user."""
    return CustomUser.objects.create_user(
        username='reporter',
        email='reporter@example.com',
        password='testpass123'
    )


@pytest.fixture
def sample_task(user, projects):
    """Create a sample task for testing."""
    return Task.objects.create(
        project=projects['main'],
        title='Test Task',
        description='Test description',
        status=TaskStatus.TODO,
        assignee=user
    )


@pytest.fixture
def tasks_ordered(projects):
    """Create tasks in specific order for ordering tests."""
    from django.utils import timezone
    import time
    
    task1 = Task.objects.create(project=projects['main'], title='Task 1', status=TaskStatus.TODO)
    time.sleep(0.1)  # Longer delay to ensure different timestamps
    task2 = Task.objects.create(project=projects['main'], title='Task 2', status=TaskStatus.TODO)
    return [task1, task2]


@pytest.mark.django_db
class TestTaskModel:
    """Test cases for Task model."""
    
    def test_task_creation(self, sample_task, user):
        """Test that task can be created with valid data."""
        assert sample_task.title == 'Test Task'
        assert sample_task.status == TaskStatus.TODO
        assert sample_task.assignee == user
        assert sample_task.id is not None
        assert sample_task.created_at is not None
        assert sample_task.updated_at is not None
    
    @pytest.mark.parametrize("invalid_title,expected_message", [
        ('', 'title'),
        ('   ', 'Task title cannot be empty or just whitespace'),
        ('ab', 'Task title must be at least 3 characters long'),
    ])
    def test_task_title_validation(self, invalid_title, expected_message, projects):
        """Test that task title validation works."""
        task = Task(project=projects['main'], title=invalid_title, status=TaskStatus.TODO)
        with pytest.raises(ValidationError) as exc_info:
            task.full_clean()
        
        if expected_message == 'title':
            assert 'title' in exc_info.value.message_dict
        else:
            assert expected_message in str(exc_info.value)
    
    @pytest.mark.parametrize("invalid_estimate,expected_message", [
        (-1, 'Task estimate cannot be negative'),
        (101, 'Task estimate cannot exceed 100 points'),
    ])
    def test_task_estimate_validation(self, invalid_estimate, expected_message, projects):
        """Test that task estimate validation works."""
        task = Task(project=projects['main'], title='Valid Task', estimate=invalid_estimate, status=TaskStatus.TODO)
        with pytest.raises(ValidationError, match=expected_message):
            task.full_clean()
    
    def test_task_done_without_estimate(self, projects):
        """Test that task cannot be marked as DONE without estimate."""
        task = Task(project=projects['main'], title='Valid Task', status=TaskStatus.DONE, estimate=None)
        with pytest.raises(ValidationError, match='Tasks marked as DONE must have an estimate'):
            task.full_clean()
    
    def test_task_done_with_estimate(self, projects):
        """Test that task can be marked as DONE with estimate."""
        task = Task(project=projects['main'], title='Valid Task', status=TaskStatus.DONE, estimate=5)
        # Should not raise any exception
        task.full_clean()
    
    def test_task_clean_method(self):
        """Test that task clean method validates fields."""
        task = Task(title='  Valid Task  ', estimate=5, status=TaskStatus.TODO)
        task.clean()
        assert task.title == 'Valid Task'  # Should be stripped
    
    def test_task_save_method(self):
        """Test that task save method calls validation."""
        task = Task(title='ab', status=TaskStatus.TODO)  # Too short
        with pytest.raises(ValidationError):
            task.save()
    
    def test_task_meta_ordering(self, tasks_ordered):
        """Test that tasks are ordered by updated_at descending."""
        tasks = list(Task.objects.all())
        assert tasks[0] == tasks_ordered[1]  # Most recent first
        assert tasks[1] == tasks_ordered[0]
    
    def test_task_string_representation(self, sample_task):
        """Test that task string representation returns title."""
        assert str(sample_task) == 'Test Task'
    
    def test_task_foreign_key_relationships(self, user, reporter, projects):
        """Test that task foreign key relationships work."""
        task = Task.objects.create(
            project=projects['main'],
            title='Test Task',
            status=TaskStatus.TODO,
            assignee=user,
            reporter=reporter
        )
        
        assert task.assignee == user
        assert task.reporter == reporter
        assert task in user.assigned_tasks.all()
        assert task in reporter.reported_tasks.all()
    
    @pytest.mark.parametrize("valid_estimate", [0, 50, 100, None])
    def test_task_valid_estimates(self, valid_estimate, projects):
        """Test that valid estimates pass validation."""
        task = Task(project=projects['main'], title='Valid Task', estimate=valid_estimate, status=TaskStatus.TODO)
        # Should not raise any exception
        task.full_clean()
    
    @pytest.mark.parametrize("valid_title", [
        'Valid Task',
        '  Valid Task  ',  # Should work with whitespace
        'A' * 200,  # Max length
    ])
    def test_task_valid_titles(self, valid_title, projects):
        """Test that valid titles pass validation."""
        task = Task(project=projects['main'], title=valid_title, status=TaskStatus.TODO)
        # Should not raise any exception
        task.full_clean()
