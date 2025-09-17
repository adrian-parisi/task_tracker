"""
Django signals for automatic activity logging.
"""
from typing import Any, Dict
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Task
from .services import ActivityService


# Store original task state before updates
_task_pre_save_state: Dict[str, Task | None] = {}


@receiver(pre_save, sender=Task)
def task_pre_save(sender: type[Task], instance: Task, **kwargs: Any) -> None:
    """
    Capture task state before save to detect changes.
    """
    if instance.pk:  # Only for existing tasks (updates)
        try:
            # Get the current state from database
            original_task = Task.objects.get(pk=instance.pk)
            _task_pre_save_state[instance.pk] = original_task
        except Task.DoesNotExist:
            # Task doesn't exist yet, this is a creation
            _task_pre_save_state[instance.pk] = None


@receiver(post_save, sender=Task)
def task_post_save(sender: type[Task], instance: Task, created: bool, **kwargs: Any) -> None:
    """
    Log task activities after save.
    """
    # Get the actor from the current request context if available
    # For now, we'll handle this in the view layer by setting a temporary attribute
    actor = getattr(instance, '_current_user', None)
    
    if created:
        # Log task creation
        ActivityService.log_task_creation(instance, actor)
    else:
        # Log field changes for updates
        original_task = _task_pre_save_state.get(instance.pk)
        if original_task:
            changes = ActivityService.detect_field_changes(original_task, instance)
            if changes:
                ActivityService.log_field_changes(instance, changes, actor)
        
        # Clean up the stored state
        if instance.pk in _task_pre_save_state:
            del _task_pre_save_state[instance.pk]