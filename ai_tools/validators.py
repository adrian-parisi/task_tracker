"""
Validators for AI tools app.
"""
import uuid
from rest_framework.exceptions import ValidationError


def validate_uuid(value):
    """
    Validate that a value is a valid UUID.
    
    Args:
        value: The value to validate
        
    Raises:
        ValidationError: If the value is not a valid UUID
    """
    try:
        uuid.UUID(str(value))
    except (ValueError, TypeError):
        raise ValidationError('Invalid UUID format. Must be a valid UUID.')
