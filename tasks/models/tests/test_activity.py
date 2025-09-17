import pytest
from accounts.models import CustomUser
from ..task import Task
from ..activity import TaskActivity
from ..choices import ActivityType, TaskStatus


@pytest.fixture
def user():
    """Create a test user."""
    return CustomUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def task(user):
    """Create a test task."""
    return Task.objects.create(
        title='Test Task',
        description='Test description',
        status=TaskStatus.TODO,
        assignee=user
    )


@pytest.fixture
def sample_activity(task, user):
    """Create a sample activity for testing."""
    return TaskActivity.objects.create(
        task=task,
        actor=user,
        type=ActivityType.CREATED,
        field='',
        before=None,
        after=None
    )


@pytest.fixture
def activities_ordered(task):
    """Create activities in specific order for ordering tests."""
    activity1 = TaskActivity.objects.create(
        task=task,
        type=ActivityType.CREATED
    )
    
    activity2 = TaskActivity.objects.create(
        task=task,
        type=ActivityType.UPDATED_STATUS,
        field='status',
        before='TODO',
        after='IN_PROGRESS'
    )
    
    return [activity1, activity2]


class TestTaskActivityModel:
    """Test cases for TaskActivity model."""
    
    def test_activity_creation(self, sample_activity, task, user):
        """Test that activity can be created with valid data."""
        assert sample_activity.task == task
        assert sample_activity.actor == user
        assert sample_activity.type == ActivityType.CREATED
        assert sample_activity.field == ''
        assert sample_activity.before is None
        assert sample_activity.after is None
        assert sample_activity.created_at is not None
    
    def test_activity_without_actor(self, task):
        """Test that activity can be created without actor."""
        activity = TaskActivity.objects.create(
            task=task,
            actor=None,
            type=ActivityType.CREATED
        )
        
        assert activity.task == task
        assert activity.actor is None
        assert activity.type == ActivityType.CREATED
    
    def test_activity_with_field_changes(self, task, user):
        """Test that activity can store field changes."""
        activity = TaskActivity.objects.create(
            task=task,
            actor=user,
            type=ActivityType.UPDATED_STATUS,
            field='status',
            before='TODO',
            after='IN_PROGRESS'
        )
        
        assert activity.field == 'status'
        assert activity.before == 'TODO'
        assert activity.after == 'IN_PROGRESS'
    
    def test_activity_string_representation(self, sample_activity, task):
        """Test that activity string representation works."""
        expected = f"{task.title} - {ActivityType.CREATED}"
        assert str(sample_activity) == expected
    
    def test_activity_meta_ordering(self, activities_ordered):
        """Test that activities are ordered by created_at descending."""
        activities = list(TaskActivity.objects.all())
        assert activities[0] == activities_ordered[1]  # Most recent first
        assert activities[1] == activities_ordered[0]
    
    def test_activity_task_relationship(self, sample_activity, task):
        """Test that activity task relationship works."""
        assert sample_activity.task == task
        assert sample_activity in task.activities.all()
    
    def test_activity_actor_relationship(self, sample_activity, user):
        """Test that activity actor relationship works."""
        assert sample_activity.actor == user
    
    def test_activity_json_fields(self, task, user):
        """Test that activity can store JSON data in before/after fields."""
        before_data = {'status': 'TODO', 'assignee': None}
        after_data = {'status': 'IN_PROGRESS', 'assignee': user.id}
        
        activity = TaskActivity.objects.create(
            task=task,
            actor=user,
            type=ActivityType.UPDATED_STATUS,
            field='status',
            before=before_data,
            after=after_data
        )
        
        assert activity.before == before_data
        assert activity.after == after_data
    
    @pytest.mark.parametrize("activity_type,field,before,after", [
        (ActivityType.CREATED, '', None, None),
        (ActivityType.UPDATED_STATUS, 'status', 'TODO', 'IN_PROGRESS'),
        (ActivityType.UPDATED_ASSIGNEE, 'assignee', None, 'user_id'),
        (ActivityType.UPDATED_ESTIMATE, 'estimate', None, 5),
        (ActivityType.UPDATED_DESCRIPTION, 'description', 'old', 'new'),
        (ActivityType.DELETED, '', None, None),
    ])
    def test_activity_types(self, task, user, activity_type, field, before, after):
        """Test that different activity types can be created."""
        activity = TaskActivity.objects.create(
            task=task,
            actor=user,
            type=activity_type,
            field=field,
            before=before,
            after=after
        )
        
        assert activity.type == activity_type
        assert activity.field == field
        assert activity.before == before
        assert activity.after == after
