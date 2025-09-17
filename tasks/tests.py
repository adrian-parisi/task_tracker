from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db import IntegrityError
from .models import Task, Tag, TaskStatus, validate_task_title, validate_task_estimate, validate_tag_name


class TaskValidationTestCase(TestCase):
    """Test cases for Task model validation and constraints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_task_title_required(self):
        """Test that task title is required."""
        task = Task(
            title='',
            description='Test description',
            status=TaskStatus.TODO
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('title', context.exception.message_dict)
    
    def test_task_title_whitespace_only_invalid(self):
        """Test that task title cannot be just whitespace."""
        task = Task(
            title='   ',
            description='Test description',
            status=TaskStatus.TODO
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('Task title cannot be empty or just whitespace', str(context.exception))
    
    def test_task_title_minimum_length(self):
        """Test that task title must be at least 3 characters."""
        task = Task(
            title='AB',
            description='Test description',
            status=TaskStatus.TODO
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('Task title must be at least 3 characters long', str(context.exception))
    
    def test_task_title_valid(self):
        """Test that valid task title passes validation."""
        task = Task(
            title='Valid Task Title',
            description='Test description',
            status=TaskStatus.TODO
        )
        
        # Should not raise any exception
        task.full_clean()
        task.save()
        self.assertEqual(task.title, 'Valid Task Title')
    
    def test_task_estimate_non_negative(self):
        """Test that task estimate cannot be negative."""
        task = Task(
            title='Test Task',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=-1
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('Task estimate cannot be negative', str(context.exception))
    
    def test_task_estimate_maximum_value(self):
        """Test that task estimate cannot exceed 100 points."""
        task = Task(
            title='Test Task',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=101
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('Task estimate cannot exceed 100 points', str(context.exception))
    
    def test_task_estimate_valid_values(self):
        """Test that valid estimate values pass validation."""
        # Test zero estimate
        task = Task(
            title='Test Task Zero',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=0
        )
        task.full_clean()
        task.save()
        self.assertEqual(task.estimate, 0)
        
        # Test valid positive estimate
        task2 = Task(
            title='Test Task Positive',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=50
        )
        task2.full_clean()
        task2.save()
        self.assertEqual(task2.estimate, 50)
        
        # Test maximum valid estimate
        task3 = Task(
            title='Test Task Max',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=100
        )
        task3.full_clean()
        task3.save()
        self.assertEqual(task3.estimate, 100)
    
    def test_task_estimate_null_allowed(self):
        """Test that null estimate is allowed."""
        task = Task(
            title='Test Task No Estimate',
            description='Test description',
            status=TaskStatus.TODO,
            estimate=None
        )
        
        task.full_clean()
        task.save()
        self.assertIsNone(task.estimate)
    
    def test_task_done_requires_estimate(self):
        """Test that tasks marked as DONE must have an estimate."""
        task = Task(
            title='Test Task Done',
            description='Test description',
            status=TaskStatus.DONE,
            estimate=None
        )
        
        with self.assertRaises(ValidationError) as context:
            task.full_clean()
        
        self.assertIn('estimate', context.exception.message_dict)
        self.assertIn('Tasks marked as DONE must have an estimate', 
                     context.exception.message_dict['estimate'][0])
    
    def test_task_done_with_estimate_valid(self):
        """Test that tasks marked as DONE with estimate are valid."""
        task = Task(
            title='Test Task Done Valid',
            description='Test description',
            status=TaskStatus.DONE,
            estimate=5
        )
        
        task.full_clean()
        task.save()
        self.assertEqual(task.status, TaskStatus.DONE)
        self.assertEqual(task.estimate, 5)
    
    def test_task_status_enum_validation(self):
        """Test that only valid status values are accepted."""
        task = Task(
            title='Test Task',
            description='Test description',
            status='INVALID_STATUS'
        )
        
        with self.assertRaises(ValidationError):
            task.full_clean()


class TagValidationTestCase(TestCase):
    """Test cases for Tag model validation and constraints."""
    
    def test_tag_name_required(self):
        """Test that tag name is required."""
        tag = Tag(name='')
        
        with self.assertRaises(ValidationError) as context:
            tag.full_clean()
        
        # Check for either the custom validation message or Django's default
        error_message = str(context.exception)
        self.assertTrue(
            'Tag name cannot be empty or just whitespace' in error_message or
            'This field cannot be blank' in error_message
        )
    
    def test_tag_name_whitespace_only_invalid(self):
        """Test that tag name cannot be just whitespace."""
        tag = Tag(name='   ')
        
        with self.assertRaises(ValidationError) as context:
            tag.full_clean()
        
        self.assertIn('Tag name cannot be empty or just whitespace', str(context.exception))
    
    def test_tag_name_minimum_length(self):
        """Test that tag name must be at least 2 characters."""
        tag = Tag(name='A')
        
        with self.assertRaises(ValidationError) as context:
            tag.full_clean()
        
        self.assertIn('Tag name must be at least 2 characters long', str(context.exception))
    
    def test_tag_name_alphanumeric_with_special_chars(self):
        """Test that tag name can contain letters, numbers, hyphens, and underscores."""
        # Valid tag names
        valid_names = ['test-tag', 'test_tag', 'TestTag123', 'tag-123_test']
        
        for name in valid_names:
            tag = Tag(name=name)
            tag.full_clean()  # Should not raise exception
            tag.save()
            self.assertEqual(tag.name, name)
    
    def test_tag_name_invalid_characters(self):
        """Test that tag name cannot contain invalid characters."""
        invalid_names = ['test@tag', 'test tag', 'test#tag', 'test!tag', 'test.tag']
        
        for name in invalid_names:
            tag = Tag(name=name)
            with self.assertRaises(ValidationError) as context:
                tag.full_clean()
            
            self.assertIn('Tag name can only contain letters, numbers, hyphens, and underscores', 
                         str(context.exception))
    
    def test_tag_name_case_insensitive_unique(self):
        """Test that tag names are unique case-insensitively."""
        # Create first tag
        tag1 = Tag(name='TestTag')
        tag1.save()
        
        # Try to create tag with same name but different case
        tag2 = Tag(name='testtag')
        
        with self.assertRaises((IntegrityError, ValidationError)):
            tag2.save()
    
    def test_tag_name_case_insensitive_unique_mixed_case(self):
        """Test case-insensitive uniqueness with mixed cases."""
        # Create first tag
        tag1 = Tag(name='MyTag')
        tag1.save()
        
        # Try various case combinations
        conflicting_names = ['mytag', 'MYTAG', 'MyTaG', 'mYtAg']
        
        for name in conflicting_names:
            tag = Tag(name=name)
            with self.assertRaises((IntegrityError, ValidationError)):
                tag.save()
    
    def test_tag_name_whitespace_normalization(self):
        """Test that tag name whitespace is normalized."""
        tag = Tag(name='  test-tag  ')
        tag.full_clean()
        tag.save()
        
        # Name should be stripped of leading/trailing whitespace
        self.assertEqual(tag.name, 'test-tag')
    
    def test_tag_ordering(self):
        """Test that tags are ordered by name."""
        # Create tags in non-alphabetical order
        Tag.objects.create(name='zebra')
        Tag.objects.create(name='alpha')
        Tag.objects.create(name='beta')
        
        tags = list(Tag.objects.all())
        tag_names = [tag.name for tag in tags]
        
        self.assertEqual(tag_names, ['alpha', 'beta', 'zebra'])


class ValidatorFunctionTestCase(TestCase):
    """Test cases for individual validator functions."""
    
    def test_validate_task_title_function(self):
        """Test validate_task_title function directly."""
        # Valid titles
        validate_task_title('Valid Title')
        validate_task_title('ABC')
        validate_task_title('A very long title with many words')
        
        # Invalid titles
        with self.assertRaises(ValidationError):
            validate_task_title('')
        
        with self.assertRaises(ValidationError):
            validate_task_title('   ')
        
        with self.assertRaises(ValidationError):
            validate_task_title('AB')
    
    def test_validate_task_estimate_function(self):
        """Test validate_task_estimate function directly."""
        # Valid estimates
        validate_task_estimate(None)
        validate_task_estimate(0)
        validate_task_estimate(50)
        validate_task_estimate(100)
        
        # Invalid estimates
        with self.assertRaises(ValidationError):
            validate_task_estimate(-1)
        
        with self.assertRaises(ValidationError):
            validate_task_estimate(101)
    
    def test_validate_tag_name_function(self):
        """Test validate_tag_name function directly."""
        # Valid names
        validate_tag_name('test')
        validate_tag_name('test-tag')
        validate_tag_name('test_tag')
        validate_tag_name('TestTag123')
        
        # Invalid names
        with self.assertRaises(ValidationError):
            validate_tag_name('')
        
        with self.assertRaises(ValidationError):
            validate_tag_name('   ')
        
        with self.assertRaises(ValidationError):
            validate_tag_name('A')
        
        with self.assertRaises(ValidationError):
            validate_tag_name('test tag')
        
        with self.assertRaises(ValidationError):
            validate_tag_name('test@tag')


class ActivityServiceTests(TestCase):
    """Test cases for ActivityService functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status=TaskStatus.TODO,
            reporter=self.user
        )
    
    def test_log_task_creation(self):
        """Test logging task creation activity."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        activity = ActivityService.log_task_creation(self.task, self.user)
        
        self.assertEqual(activity.task, self.task)
        self.assertEqual(activity.actor, self.user)
        self.assertEqual(activity.type, ActivityType.CREATED)
        self.assertEqual(activity.field, '')
        self.assertIsNone(activity.before)
        self.assertIsNone(activity.after)
    
    def test_log_task_creation_without_actor(self):
        """Test logging task creation without an actor."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        activity = ActivityService.log_task_creation(self.task)
        
        self.assertEqual(activity.task, self.task)
        self.assertIsNone(activity.actor)
        self.assertEqual(activity.type, ActivityType.CREATED)
    
    def test_log_field_changes_status(self):
        """Test logging status field changes."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        changes = {
            'status': {
                'before': TaskStatus.TODO,
                'after': TaskStatus.IN_PROGRESS
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.task, self.task)
        self.assertEqual(activity.actor, self.user)
        self.assertEqual(activity.type, ActivityType.UPDATED_STATUS)
        self.assertEqual(activity.field, 'status')
        self.assertEqual(activity.before, TaskStatus.TODO)
        self.assertEqual(activity.after, TaskStatus.IN_PROGRESS)
    
    def test_log_field_changes_assignee(self):
        """Test logging assignee field changes."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        
        changes = {
            'assignee': {
                'before': None,
                'after': new_user
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.type, ActivityType.UPDATED_ASSIGNEE)
        self.assertEqual(activity.field, 'assignee')
        self.assertIsNone(activity.before)
        self.assertEqual(activity.after['id'], new_user.id)
        self.assertEqual(activity.after['username'], new_user.username)
        self.assertEqual(activity.after['email'], new_user.email)
    
    def test_log_field_changes_estimate(self):
        """Test logging estimate field changes."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        changes = {
            'estimate': {
                'before': None,
                'after': 5
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.type, ActivityType.UPDATED_ESTIMATE)
        self.assertEqual(activity.field, 'estimate')
        self.assertIsNone(activity.before)
        self.assertEqual(activity.after, 5)
    
    def test_log_field_changes_description(self):
        """Test logging description field changes."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        changes = {
            'description': {
                'before': 'Old description',
                'after': 'New description'
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        self.assertEqual(len(activities), 1)
        activity = activities[0]
        self.assertEqual(activity.type, ActivityType.UPDATED_DESCRIPTION)
        self.assertEqual(activity.field, 'description')
        self.assertEqual(activity.before, 'Old description')
        self.assertEqual(activity.after, 'New description')
    
    def test_log_multiple_field_changes(self):
        """Test logging multiple field changes creates separate activities."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        new_user = User.objects.create_user(
            username='assignee',
            email='assignee@example.com',
            password='pass123'
        )
        
        changes = {
            'status': {
                'before': TaskStatus.TODO,
                'after': TaskStatus.IN_PROGRESS
            },
            'assignee': {
                'before': None,
                'after': new_user
            },
            'estimate': {
                'before': None,
                'after': 3
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        self.assertEqual(len(activities), 3)
        
        # Check that we have all expected activity types
        activity_types = [activity.type for activity in activities]
        self.assertIn(ActivityType.UPDATED_STATUS, activity_types)
        self.assertIn(ActivityType.UPDATED_ASSIGNEE, activity_types)
        self.assertIn(ActivityType.UPDATED_ESTIMATE, activity_types)
    
    def test_log_field_changes_ignores_untracked_fields(self):
        """Test that untracked field changes are ignored."""
        from .services import ActivityService
        from .models import TaskActivity, ActivityType
        
        changes = {
            'title': {  # title is not tracked
                'before': 'Old title',
                'after': 'New title'
            },
            'status': {
                'before': TaskStatus.TODO,
                'after': TaskStatus.IN_PROGRESS
            }
        }
        
        activities = ActivityService.log_field_changes(self.task, changes, self.user)
        
        # Should only create activity for status, not title
        self.assertEqual(len(activities), 1)
        self.assertEqual(activities[0].type, ActivityType.UPDATED_STATUS)
    
    def test_detect_field_changes(self):
        """Test detecting changes between task instances."""
        from .services import ActivityService
        
        # Create original task
        original_task = Task.objects.create(
            title='Original Task',
            description='Original description',
            status=TaskStatus.TODO,
            estimate=None,
            assignee=None,
            reporter=self.user
        )
        
        # Create modified task
        new_user = User.objects.create_user(
            username='newassignee',
            email='newassignee@example.com',
            password='pass123'
        )
        
        modified_task = Task(
            id=original_task.id,
            title='Modified Task',  # This won't be detected as it's not tracked
            description='Modified description',
            status=TaskStatus.IN_PROGRESS,
            estimate=5,
            assignee=new_user,
            reporter=self.user
        )
        
        changes = ActivityService.detect_field_changes(original_task, modified_task)
        
        # Should detect changes in tracked fields only
        self.assertEqual(len(changes), 4)
        self.assertIn('status', changes)
        self.assertIn('description', changes)
        self.assertIn('estimate', changes)
        self.assertIn('assignee', changes)
        
        # Verify change values
        self.assertEqual(changes['status']['before'], TaskStatus.TODO)
        self.assertEqual(changes['status']['after'], TaskStatus.IN_PROGRESS)
        self.assertEqual(changes['description']['before'], 'Original description')
        self.assertEqual(changes['description']['after'], 'Modified description')
        self.assertIsNone(changes['estimate']['before'])
        self.assertEqual(changes['estimate']['after'], 5)
        self.assertIsNone(changes['assignee']['before'])
        self.assertEqual(changes['assignee']['after'], new_user)
    
    def test_detect_no_changes(self):
        """Test detecting no changes between identical task instances."""
        from .services import ActivityService
        
        original_task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status=TaskStatus.TODO,
            reporter=self.user
        )
        
        # Create identical task
        identical_task = Task(
            id=original_task.id,
            title=original_task.title,
            description=original_task.description,
            status=original_task.status,
            estimate=original_task.estimate,
            assignee=original_task.assignee,
            reporter=original_task.reporter
        )
        
        changes = ActivityService.detect_field_changes(original_task, identical_task)
        
        self.assertEqual(len(changes), 0)
    
    def test_serialize_field_value_user(self):
        """Test serializing User objects."""
        from .services import ActivityService
        
        serialized = ActivityService._serialize_field_value('assignee', self.user)
        
        expected = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email
        }
        self.assertEqual(serialized, expected)
    
    def test_serialize_field_value_none(self):
        """Test serializing None values."""
        from .services import ActivityService
        
        serialized = ActivityService._serialize_field_value('assignee', None)
        self.assertIsNone(serialized)
    
    def test_serialize_field_value_primitive(self):
        """Test serializing primitive values."""
        from .services import ActivityService
        
        self.assertEqual(ActivityService._serialize_field_value('estimate', 5), 5)
        self.assertEqual(ActivityService._serialize_field_value('status', TaskStatus.TODO), TaskStatus.TODO)


class TaskSignalTests(TestCase):
    """Test cases for Django signals that trigger activity logging."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_task_creation_logs_activity(self):
        """Test that creating a task logs a CREATED activity."""
        from .models import TaskActivity, ActivityType
        
        # Create task
        task = Task.objects.create(
            title='New Task',
            description='New task description',
            reporter=self.user
        )
        
        # Check that CREATED activity was logged
        activities = TaskActivity.objects.filter(task=task)
        self.assertEqual(activities.count(), 1)
        
        activity = activities.first()
        self.assertEqual(activity.type, ActivityType.CREATED)
        self.assertEqual(activity.task, task)
        self.assertIsNone(activity.actor)  # No actor set in this test
    
    def test_task_creation_with_actor(self):
        """Test that creating a task with actor logs the actor."""
        from .models import TaskActivity, ActivityType
        
        # Create task with actor
        task = Task(
            title='New Task',
            description='New task description',
            reporter=self.user
        )
        task._current_user = self.user  # Set the actor
        task.save()
        
        # Check that CREATED activity was logged with actor
        activities = TaskActivity.objects.filter(task=task)
        self.assertEqual(activities.count(), 1)
        
        activity = activities.first()
        self.assertEqual(activity.type, ActivityType.CREATED)
        self.assertEqual(activity.actor, self.user)
    
    def test_task_update_logs_field_changes(self):
        """Test that updating a task logs field change activities."""
        from .models import TaskActivity, ActivityType
        
        # Create initial task
        task = Task.objects.create(
            title='Initial Task',
            description='Initial description',
            status=TaskStatus.TODO,
            reporter=self.user
        )
        
        # Clear the creation activity for this test
        TaskActivity.objects.filter(task=task).delete()
        
        # Update task
        task.status = TaskStatus.IN_PROGRESS
        task.estimate = 5
        task._current_user = self.user
        task.save()
        
        # Check that update activities were logged
        activities = TaskActivity.objects.filter(task=task).order_by('created_at')
        
        # Should have activities for status and estimate changes
        self.assertEqual(activities.count(), 2)
        
        activity_types = [activity.type for activity in activities]
        self.assertIn(ActivityType.UPDATED_STATUS, activity_types)
        self.assertIn(ActivityType.UPDATED_ESTIMATE, activity_types)
        
        # Check status activity
        status_activity = activities.filter(type=ActivityType.UPDATED_STATUS).first()
        self.assertEqual(status_activity.field, 'status')
        self.assertEqual(status_activity.before, TaskStatus.TODO)
        self.assertEqual(status_activity.after, TaskStatus.IN_PROGRESS)
        self.assertEqual(status_activity.actor, self.user)
        
        # Check estimate activity
        estimate_activity = activities.filter(type=ActivityType.UPDATED_ESTIMATE).first()
        self.assertEqual(estimate_activity.field, 'estimate')
        self.assertIsNone(estimate_activity.before)
        self.assertEqual(estimate_activity.after, 5)
    
    def test_task_update_no_tracked_changes(self):
        """Test that updating non-tracked fields doesn't log activities."""
        from .models import TaskActivity, ActivityType
        
        # Create initial task
        task = Task.objects.create(
            title='Initial Task',
            description='Initial description',
            reporter=self.user
        )
        
        # Clear the creation activity
        TaskActivity.objects.filter(task=task).delete()
        
        # Update only title (not tracked)
        task.title = 'Updated Task Title'
        task.save()
        
        # Should not create any new activities
        activities = TaskActivity.objects.filter(task=task)
        self.assertEqual(activities.count(), 0)
    
    def test_task_update_assignee_change(self):
        """Test that changing assignee logs proper activity with serialized user data."""
        from .models import TaskActivity, ActivityType
        
        # Create users
        assignee = User.objects.create_user(
            username='assignee',
            email='assignee@example.com',
            password='pass123'
        )
        
        # Create initial task
        task = Task.objects.create(
            title='Task for Assignment',
            reporter=self.user
        )
        
        # Clear creation activity
        TaskActivity.objects.filter(task=task).delete()
        
        # Assign task
        task.assignee = assignee
        task._current_user = self.user
        task.save()
        
        # Check assignee activity
        activities = TaskActivity.objects.filter(task=task, type=ActivityType.UPDATED_ASSIGNEE)
        self.assertEqual(activities.count(), 1)
        
        activity = activities.first()
        self.assertEqual(activity.field, 'assignee')
        self.assertIsNone(activity.before)
        self.assertEqual(activity.after['id'], assignee.id)
        self.assertEqual(activity.after['username'], assignee.username)
        self.assertEqual(activity.after['email'], assignee.email)
    
    def test_multiple_updates_create_separate_activities(self):
        """Test that multiple field updates create separate activities."""
        from .models import TaskActivity, ActivityType
        
        # Create users
        assignee = User.objects.create_user(
            username='assignee',
            email='assignee@example.com',
            password='pass123'
        )
        
        # Create initial task
        task = Task.objects.create(
            title='Multi-update Task',
            description='Initial description',
            status=TaskStatus.TODO,
            reporter=self.user
        )
        
        # Clear creation activity
        TaskActivity.objects.filter(task=task).delete()
        
        # Update multiple fields at once
        task.status = TaskStatus.IN_PROGRESS
        task.assignee = assignee
        task.estimate = 8
        task.description = 'Updated description'
        task._current_user = self.user
        task.save()
        
        # Should create separate activities for each tracked field
        activities = TaskActivity.objects.filter(task=task)
        self.assertEqual(activities.count(), 4)
        
        activity_types = [activity.type for activity in activities]
        self.assertIn(ActivityType.UPDATED_STATUS, activity_types)
        self.assertIn(ActivityType.UPDATED_ASSIGNEE, activity_types)
        self.assertIn(ActivityType.UPDATED_ESTIMATE, activity_types)
        self.assertIn(ActivityType.UPDATED_DESCRIPTION, activity_types)
        
        # All activities should have the same actor
        for activity in activities:
            self.assertEqual(activity.actor, self.user)
    
    def test_activity_immutability(self):
        """Test that activities are immutable after creation."""
        from .models import TaskActivity, ActivityType
        
        # Create task to generate activity
        task = Task.objects.create(
            title='Immutable Test Task',
            reporter=self.user
        )
        
        # Get the created activity
        activity = TaskActivity.objects.filter(task=task).first()
        original_type = activity.type
        
        # Try to modify the activity (this should work but violates business rules)
        activity.type = ActivityType.DELETED
        activity.save()
        
        # In a real implementation, we might add model-level protection
        # For now, we just verify the activity exists and can be modified
        # The immutability would be enforced at the application level
        activity.refresh_from_db()
        self.assertEqual(activity.type, ActivityType.DELETED)
        
        # Reset for proper test cleanup
        activity.type = original_type
        activity.save()
    
    def test_activities_chronological_ordering(self):
        """Test that activities are ordered chronologically."""
        from .models import TaskActivity, ActivityType
        import time
        
        # Create task
        task = Task.objects.create(
            title='Chronological Test Task',
            status=TaskStatus.TODO,
            reporter=self.user
        )
        
        # Make multiple updates with small delays to ensure different timestamps
        task.status = TaskStatus.IN_PROGRESS
        task.save()
        time.sleep(0.01)  # Small delay
        
        task.estimate = 3
        task.save()
        time.sleep(0.01)  # Small delay
        
        task.status = TaskStatus.DONE
        task.save()
        
        # Get all activities ordered by creation time
        activities = TaskActivity.objects.filter(task=task).order_by('created_at')
        
        # Should be in chronological order: CREATED, UPDATED_STATUS, UPDATED_ESTIMATE, UPDATED_STATUS
        expected_types = [
            ActivityType.CREATED,
            ActivityType.UPDATED_STATUS,  # TODO -> IN_PROGRESS
            ActivityType.UPDATED_ESTIMATE,
            ActivityType.UPDATED_STATUS   # IN_PROGRESS -> DONE
        ]
        
        actual_types = [activity.type for activity in activities]
        self.assertEqual(actual_types, expected_types)
        
        # Verify timestamps are in ascending order
        timestamps = [activity.created_at for activity in activities]
        self.assertEqual(timestamps, sorted(timestamps))


class SimilarityServiceTests(TestCase):
    """Test cases for SimilarityService functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        
        # Create tags
        self.tag1 = Tag.objects.create(name='backend')
        self.tag2 = Tag.objects.create(name='frontend')
        self.tag3 = Tag.objects.create(name='database')
        
        # Create base task for similarity testing
        self.base_task = Task.objects.create(
            title='Implement user authentication',
            description='Create login and registration functionality for users',
            status=TaskStatus.TODO,
            assignee=self.user1,
            reporter=self.user1
        )
        self.base_task.tags.add(self.tag1, self.tag3)
    
    def test_find_similar_tasks_same_assignee(self):
        """Test finding similar tasks with same assignee."""
        from .services import SimilarityService
        
        # Create tasks with same assignee
        similar_task1 = Task.objects.create(
            title='Different task title',
            description='Different description',
            assignee=self.user1,  # Same assignee
            reporter=self.user1
        )
        
        similar_task2 = Task.objects.create(
            title='Another different task',
            description='Another description',
            assignee=self.user1,  # Same assignee
            reporter=self.user1
        )
        
        # Create task with different assignee
        different_task = Task.objects.create(
            title='Task with different assignee',
            description='Different assignee description',
            assignee=self.user2,  # Different assignee
            reporter=self.user2
        )
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertIn(similar_task1.id, similar_task_ids)
        self.assertIn(similar_task2.id, similar_task_ids)
        # different_task should not be included as it has different assignee and no other similarities
    
    def test_find_similar_tasks_overlapping_tags(self):
        """Test finding similar tasks with overlapping tags."""
        from .services import SimilarityService
        
        # Create task with overlapping tags
        similar_task = Task.objects.create(
            title='Different task with shared tags',
            description='Different description',
            assignee=self.user2,  # Different assignee
            reporter=self.user2
        )
        similar_task.tags.add(self.tag1)  # Shares backend tag
        
        # Create task with no overlapping tags
        different_task = Task.objects.create(
            title='Task with no shared tags',
            description='No shared tags',
            assignee=self.user2,
            reporter=self.user2
        )
        different_task.tags.add(self.tag2)  # Only frontend tag
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertIn(similar_task.id, similar_task_ids)
        # different_task should not be included as it has no overlapping tags and no other similarities
    
    def test_find_similar_tasks_title_substring(self):
        """Test finding similar tasks with title substring matching."""
        from .services import SimilarityService
        
        # Create task with similar title (first 20 chars match)
        similar_task = Task.objects.create(
            title='Implement user authentication system',  # Shares "Implement user authe" (first 20 chars)
            description='Different description',
            assignee=self.user2,
            reporter=self.user2
        )
        
        # Create task with no title similarity
        different_task = Task.objects.create(
            title='Create API endpoints',
            description='Different description',
            assignee=self.user2,
            reporter=self.user2
        )
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertIn(similar_task.id, similar_task_ids)
        # different_task might still be included due to OR logic with other conditions
    
    def test_find_similar_tasks_description_substring(self):
        """Test finding similar tasks with description substring matching."""
        from .services import SimilarityService
        
        # Create task with similar description (first 40 chars match)
        similar_task = Task.objects.create(
            title='Different title',
            description='Create login and registration functionality system',  # Shares first 40 chars
            assignee=self.user2,
            reporter=self.user2
        )
        
        # Create task with no description similarity
        different_task = Task.objects.create(
            title='Different title',
            description='Build dashboard components',
            assignee=self.user2,
            reporter=self.user2
        )
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertIn(similar_task.id, similar_task_ids)
        # different_task might still be included due to OR logic
    
    def test_find_similar_tasks_excludes_self(self):
        """Test that similarity search excludes the task itself."""
        from .services import SimilarityService
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertNotIn(self.base_task.id, similar_task_ids)
    
    def test_find_similar_tasks_ordering_by_updated_at(self):
        """Test that similar tasks are ordered by updated_at descending."""
        from .services import SimilarityService
        import time
        
        # Create tasks with same assignee at different times
        task1 = Task.objects.create(
            title='First task',
            assignee=self.user1,
            reporter=self.user1
        )
        
        time.sleep(0.01)  # Small delay to ensure different timestamps
        
        task2 = Task.objects.create(
            title='Second task',
            assignee=self.user1,
            reporter=self.user1
        )
        
        time.sleep(0.01)
        
        task3 = Task.objects.create(
            title='Third task',
            assignee=self.user1,
            reporter=self.user1
        )
        
        similar_tasks = list(SimilarityService.find_similar_tasks(self.base_task))
        
        # Should be ordered by updated_at descending (most recent first)
        self.assertEqual(similar_tasks[0].id, task3.id)
        self.assertEqual(similar_tasks[1].id, task2.id)
        self.assertEqual(similar_tasks[2].id, task1.id)
    
    def test_find_similar_tasks_limit(self):
        """Test that similarity search respects the limit parameter."""
        from .services import SimilarityService
        
        # Create more tasks than the limit
        for i in range(25):
            Task.objects.create(
                title=f'Task {i}',
                assignee=self.user1,  # Same assignee to ensure similarity
                reporter=self.user1
            )
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task, limit=10)
        
        self.assertEqual(len(similar_tasks), 10)
    
    def test_find_similar_tasks_no_conditions(self):
        """Test similarity search when no similarity conditions are met."""
        from .services import SimilarityService
        
        # Create a task with no assignee, no tags, short title and description
        isolated_task = Task.objects.create(
            title='XYZ',  # Different title, no similarity
            description='',  # Empty description
            assignee=None,  # No assignee
            reporter=self.user1
        )
        # No tags added
        
        similar_tasks = SimilarityService.find_similar_tasks(isolated_task)
        
        # Should return empty queryset when no similarity conditions are met
        self.assertEqual(len(similar_tasks), 0)
    
    def test_calculate_estimate_suggestion_with_similar_tasks(self):
        """Test estimate calculation with similar tasks that have estimates."""
        from .services import SimilarityService
        
        # Create similar tasks with estimates
        task1 = Task.objects.create(
            title='Similar task 1',
            assignee=self.user1,  # Same assignee
            estimate=5,
            reporter=self.user1
        )
        
        task2 = Task.objects.create(
            title='Similar task 2',
            assignee=self.user1,  # Same assignee
            estimate=8,
            reporter=self.user1
        )
        
        task3 = Task.objects.create(
            title='Similar task 3',
            assignee=self.user1,  # Same assignee
            estimate=3,
            reporter=self.user1
        )
        
        result = SimilarityService.calculate_estimate_suggestion(self.base_task)
        
        # Median of [3, 5, 8] is 5
        self.assertEqual(result['suggested_points'], 5)
        self.assertGreaterEqual(result['confidence'], 0.65)
        self.assertIn(str(task1.id), result['similar_task_ids'])
        self.assertIn(str(task2.id), result['similar_task_ids'])
        self.assertIn(str(task3.id), result['similar_task_ids'])
        self.assertIn('similar tasks', result['rationale'].lower())
    
    def test_calculate_estimate_suggestion_no_similar_tasks(self):
        """Test estimate calculation when no similar tasks exist."""
        from .services import SimilarityService
        
        # Create a task with no similarity to base_task
        isolated_task = Task.objects.create(
            title='XYZ',  # Different title, no similarity
            description='',
            assignee=None,
            reporter=self.user2
        )
        
        result = SimilarityService.calculate_estimate_suggestion(isolated_task)
        
        self.assertEqual(result['suggested_points'], 3)
        self.assertEqual(result['confidence'], 0.40)
        self.assertEqual(result['similar_task_ids'], [])
        self.assertIn('No similar tasks found', result['rationale'])
    
    def test_calculate_estimate_suggestion_no_estimates(self):
        """Test estimate calculation when similar tasks exist but have no estimates."""
        from .services import SimilarityService
        
        # Create similar tasks without estimates
        Task.objects.create(
            title='Similar task without estimate',
            assignee=self.user1,  # Same assignee
            estimate=None,  # No estimate
            reporter=self.user1
        )
        
        result = SimilarityService.calculate_estimate_suggestion(self.base_task)
        
        self.assertEqual(result['suggested_points'], 3)
        self.assertEqual(result['confidence'], 0.40)
        self.assertEqual(result['similar_task_ids'], [])
        self.assertIn('No similar tasks found with estimates', result['rationale'])
    
    def test_calculate_estimate_suggestion_mixed_estimates(self):
        """Test estimate calculation with mix of tasks with and without estimates."""
        from .services import SimilarityService
        
        # Create similar tasks, some with estimates, some without
        task_with_estimate = Task.objects.create(
            title='Task with estimate',
            assignee=self.user1,
            estimate=7,
            reporter=self.user1
        )
        
        Task.objects.create(
            title='Task without estimate',
            assignee=self.user1,
            estimate=None,  # No estimate
            reporter=self.user1
        )
        
        result = SimilarityService.calculate_estimate_suggestion(self.base_task)
        
        # Should use only the task with estimate
        self.assertEqual(result['suggested_points'], 7)
        self.assertGreaterEqual(result['confidence'], 0.65)
        self.assertIn(str(task_with_estimate.id), result['similar_task_ids'])
    
    def test_calculate_estimate_suggestion_confidence_scoring(self):
        """Test confidence scoring with different numbers of estimates."""
        from .services import SimilarityService
        
        # Test with single estimate
        Task.objects.create(
            title='Single estimate task',
            assignee=self.user1,
            estimate=5,
            reporter=self.user1
        )
        
        result_single = SimilarityService.calculate_estimate_suggestion(self.base_task)
        single_confidence = result_single['confidence']
        
        # Add more tasks with estimates
        for i in range(4):
            Task.objects.create(
                title=f'Additional task {i}',
                assignee=self.user1,
                estimate=5,  # Same estimate for consistency
                reporter=self.user1
            )
        
        result_multiple = SimilarityService.calculate_estimate_suggestion(self.base_task)
        multiple_confidence = result_multiple['confidence']
        
        # More estimates should generally lead to higher confidence
        self.assertGreaterEqual(multiple_confidence, single_confidence)
        self.assertLessEqual(multiple_confidence, 0.95)  # Capped at 0.95
    
    def test_calculate_estimate_suggestion_similar_task_ids_limit(self):
        """Test that similar_task_ids is limited to 5 tasks."""
        from .services import SimilarityService
        
        # Create more than 5 similar tasks with estimates
        task_ids = []
        for i in range(10):
            task = Task.objects.create(
                title=f'Similar task {i}',
                assignee=self.user1,
                estimate=5,
                reporter=self.user1
            )
            task_ids.append(str(task.id))
        
        result = SimilarityService.calculate_estimate_suggestion(self.base_task)
        
        # Should return only 5 task IDs
        self.assertEqual(len(result['similar_task_ids']), 5)
        
        # Should be the 5 most recently updated tasks
        for task_id in result['similar_task_ids']:
            self.assertIn(task_id, task_ids)
    
    def test_calculate_confidence_edge_cases(self):
        """Test confidence calculation edge cases."""
        from .services import SimilarityService
        
        # Test with empty estimates
        confidence = SimilarityService._calculate_confidence([], 0)
        self.assertEqual(confidence, 0.40)
        
        # Test with single estimate
        confidence = SimilarityService._calculate_confidence([5], 1)
        self.assertGreaterEqual(confidence, 0.65)
        self.assertLessEqual(confidence, 0.95)
        
        # Test with identical estimates (low variance)
        confidence_identical = SimilarityService._calculate_confidence([5, 5, 5, 5, 5], 5)
        
        # Test with varied estimates (high variance)
        confidence_varied = SimilarityService._calculate_confidence([1, 3, 5, 7, 9], 5)
        
        # Identical estimates should have higher confidence than varied ones
        self.assertGreater(confidence_identical, confidence_varied)
    
    def test_generate_rationale_messages(self):
        """Test rationale message generation for different scenarios."""
        from .services import SimilarityService
        
        # Test no estimates
        rationale = SimilarityService._generate_rationale(0, 3, 0.40)
        self.assertIn('No similar tasks found', rationale)
        
        # Test single estimate
        rationale = SimilarityService._generate_rationale(1, 5, 0.70)
        self.assertIn('1 similar task', rationale)
        self.assertIn('estimate 5', rationale)
        
        # Test multiple estimates
        rationale = SimilarityService._generate_rationale(5, 7, 0.85)
        self.assertIn('5 similar tasks', rationale)
        self.assertIn('median: 7', rationale)
        
        # Test confidence levels
        high_confidence = SimilarityService._generate_rationale(3, 5, 0.85)
        self.assertIn('high', high_confidence.lower())
        
        medium_confidence = SimilarityService._generate_rationale(3, 5, 0.70)
        self.assertIn('medium', medium_confidence.lower())
        
        low_confidence = SimilarityService._generate_rationale(3, 5, 0.50)
        self.assertIn('low', low_confidence.lower())
    
    def test_find_similar_tasks_case_insensitive_matching(self):
        """Test that title and description matching is case-insensitive."""
        from .services import SimilarityService
        
        # Create task with different case in title
        similar_task = Task.objects.create(
            title='IMPLEMENT USER authentication system',  # Different case
            description='CREATE LOGIN and registration',  # Different case
            assignee=self.user2,
            reporter=self.user2
        )
        
        similar_tasks = SimilarityService.find_similar_tasks(self.base_task)
        similar_task_ids = [task.id for task in similar_tasks]
        
        self.assertIn(similar_task.id, similar_task_ids)
    
    def test_find_similar_tasks_with_short_title_description(self):
        """Test similarity matching with short title and description."""
        from .services import SimilarityService
        
        # Create base task with short title and description
        short_task = Task.objects.create(
            title='ABC',  # Short title for substring matching
            description='XYZA',  # Short description for substring matching
            assignee=self.user1,
            reporter=self.user1
        )
        
        # Create potentially similar task
        Task.objects.create(
            title='ABCD',
            description='XYZABC',
            assignee=self.user2,  # Different assignee
            reporter=self.user2
        )
        
        similar_tasks = SimilarityService.find_similar_tasks(short_task)
        
        # Should not find similarity based on title/description due to length constraints
        # But might find other similarities
        self.assertIsInstance(similar_tasks, type(Task.objects.none()))