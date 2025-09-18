"""
Common models and base classes for the task tracker application.
"""
import uuid
from django.db import models


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models.
    
    This model includes:
    - id: UUID primary key
    - created_at: Timestamp when the record was created
    - updated_at: Timestamp when the record was last updated
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated"
    )
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        """Default string representation using the model's name and ID."""
        return f"{self.__class__.__name__}({self.id})"
