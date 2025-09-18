"""
Utility functions for AI tools app.
"""
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from .validators import validate_uuid
from tasks.models import Task


def validate_and_get_task(task_id: str) -> Task:
    """
    Validate task_id format and retrieve the task.
    
    Args:
        task_id: The task ID to validate and retrieve
        
    Returns:
        Task: The validated task object
        
    Raises:
        ValidationError: If task_id is not a valid UUID
        Http404: If task with given ID doesn't exist
    """
    # Validate task_id format
    validate_uuid(task_id)
    
    # Get task or raise 404
    return get_object_or_404(Task, id=task_id)
