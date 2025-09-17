import pytest
from ..choices import TaskStatus, ActivityType


class TestChoices:
    """Test cases for model choices."""
    
    def test_task_status_choices(self):
        """Test that TaskStatus choices are properly defined."""
        expected_choices = [
            ('TODO', 'To Do'),
            ('IN_PROGRESS', 'In Progress'),
            ('BLOCKED', 'Blocked'),
            ('DONE', 'Done')
        ]
        
        assert TaskStatus.choices == expected_choices
    
    @pytest.mark.parametrize("status,expected_value", [
        (TaskStatus.TODO, 'TODO'),
        (TaskStatus.IN_PROGRESS, 'IN_PROGRESS'),
        (TaskStatus.BLOCKED, 'BLOCKED'),
        (TaskStatus.DONE, 'DONE'),
    ])
    def test_task_status_values(self, status, expected_value):
        """Test that TaskStatus values are correct."""
        assert status == expected_value
    
    def test_activity_type_choices(self):
        """Test that ActivityType choices are properly defined."""
        expected_choices = [
            ('CREATED', 'Created'),
            ('UPDATED_STATUS', 'Status Updated'),
            ('UPDATED_ASSIGNEE', 'Assignee Updated'),
            ('UPDATED_ESTIMATE', 'Estimate Updated'),
            ('UPDATED_DESCRIPTION', 'Description Updated'),
            ('DELETED', 'Deleted')
        ]
        
        assert ActivityType.choices == expected_choices
    
    @pytest.mark.parametrize("activity_type,expected_value", [
        (ActivityType.CREATED, 'CREATED'),
        (ActivityType.UPDATED_STATUS, 'UPDATED_STATUS'),
        (ActivityType.UPDATED_ASSIGNEE, 'UPDATED_ASSIGNEE'),
        (ActivityType.UPDATED_ESTIMATE, 'UPDATED_ESTIMATE'),
        (ActivityType.UPDATED_DESCRIPTION, 'UPDATED_DESCRIPTION'),
        (ActivityType.DELETED, 'DELETED'),
    ])
    def test_activity_type_values(self, activity_type, expected_value):
        """Test that ActivityType values are correct."""
        assert activity_type == expected_value
