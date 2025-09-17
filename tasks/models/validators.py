from typing import Union
from django.core.exceptions import ValidationError


def validate_task_title(value: str) -> None:
    """Validate that task title is not empty or just whitespace."""
    if not value or not value.strip():
        raise ValidationError('Task title cannot be empty or just whitespace.')
    if len(value.strip()) < 3:
        raise ValidationError('Task title must be at least 3 characters long.')


def validate_task_estimate(value: Union[int, None]) -> None:
    """Validate task estimate business rules."""
    if value is not None and value < 0:
        raise ValidationError('Task estimate cannot be negative.')
    if value is not None and value > 100:
        raise ValidationError('Task estimate cannot exceed 100 points.')


def validate_tag_name(value: str) -> None:
    """Validate tag name format and content."""
    if not value or not value.strip():
        raise ValidationError('Tag name cannot be empty or just whitespace.')
    
    # Use stripped value for further validation
    stripped_value = value.strip()
    
    if len(stripped_value) < 2:
        raise ValidationError('Tag name must be at least 2 characters long.')
    
    # Check if contains only allowed characters (letters, numbers, hyphens, underscores)
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(char in allowed_chars for char in stripped_value):
        raise ValidationError('Tag name can only contain letters, numbers, hyphens, and underscores.')
