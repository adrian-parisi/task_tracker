"""
Services for task management functionality.
"""
from typing import Dict, Any
from accounts.models import CustomUser
from .models import Task, TaskActivity, ActivityType


class ActivityService:
    """Service for logging task activities and changes."""
    
    # Fields that should be tracked for changes
    TRACKED_FIELDS = {
        'status': ActivityType.UPDATED_STATUS,
        'assignee': ActivityType.UPDATED_ASSIGNEE,
        'estimate': ActivityType.UPDATED_ESTIMATE,
        'description': ActivityType.UPDATED_DESCRIPTION,
    }
    
    @staticmethod
    def log_task_creation(task: Task, actor: CustomUser | None = None) -> TaskActivity:
        """
        Log the creation of a new task.
        
        Args:
            task: The task that was created
            actor: The user who created the task (optional)
            
        Returns:
            TaskActivity: The created activity record
        """
        return TaskActivity.objects.create(
            task=task,
            actor=actor,
            type=ActivityType.CREATED
        )
    
    @staticmethod
    def detect_field_changes(original_task: Task, updated_task: Task) -> Dict[str, Dict[str, Any]]:
        """
        Detect which fields have changed between two task instances.
        
        Args:
            original_task: The original task state
            updated_task: The updated task state
            
        Returns:
            Dictionary mapping field names to change data
        """
        changes = {}
        
        for field_name, activity_type in ActivityService.TRACKED_FIELDS.items():
            original_value = getattr(original_task, field_name)
            updated_value = getattr(updated_task, field_name)
            
            # For foreign key fields, compare the actual objects, not just IDs
            if field_name in ['assignee', 'reporter']:
                original_id = original_value.id if original_value else None
                updated_id = updated_value.id if updated_value else None
                if original_id != updated_id:
                    # Convert foreign key objects to serializable values
                    before_value = ActivityService._serialize_field_value(original_value)
                    after_value = ActivityService._serialize_field_value(updated_value)
                    
                    changes[field_name] = {
                        'before': before_value,
                        'after': after_value,
                        'activity_type': activity_type
                    }
            else:
                if original_value != updated_value:
                    # Convert foreign key objects to serializable values
                    before_value = ActivityService._serialize_field_value(original_value)
                    after_value = ActivityService._serialize_field_value(updated_value)
                    
                    changes[field_name] = {
                        'before': before_value,
                        'after': after_value,
                        'activity_type': activity_type
                    }
        
        return changes
    
    @staticmethod
    def _serialize_field_value(value: Any) -> Any:
        """
        Convert field values to JSON-serializable format.
        
        Args:
            value: The field value to serialize
            
        Returns:
            JSON-serializable value
        """
        if value is None:
            return None
        
        # Handle CustomUser objects
        if hasattr(value, 'username'):  # CustomUser instance
            return {
                'id': str(value.id),
                'username': value.username,
                'email': value.email
            }
        
        # Handle other model instances
        if hasattr(value, 'pk'):
            return {
                'id': str(value.pk),
                'str': str(value)
            }
        
        # Return primitive values as-is
        return value
    
    @staticmethod
    def log_field_changes(
        task: Task, 
        changes: Dict[str, Dict[str, Any]], 
        actor: CustomUser | None = None
    ) -> list[TaskActivity]:
        """
        Log changes to task fields.
        
        Args:
            task: The task that was updated
            changes: Dictionary of field changes
            actor: The user who made the changes (optional)
            
        Returns:
            List of created TaskActivity records
        """
        activities = []
        
        for field_name, change_data in changes.items():
            activity = TaskActivity.objects.create(
                task=task,
                actor=actor,
                type=change_data['activity_type'],
                field=field_name,
                before=change_data['before'],
                after=change_data['after']
            )
            activities.append(activity)
        
        return activities
