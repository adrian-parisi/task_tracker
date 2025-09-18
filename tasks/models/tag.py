from typing import Any
from django.db import models
from common.models import BaseModel
from .validators import validate_tag_name


class Tag(BaseModel):
    name = models.CharField(
        max_length=64, 
        unique=True,
        validators=[validate_tag_name]
    )
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.functions.Lower('name'), 
                name='unique_tag_name_case_insensitive'
            )
        ]
        ordering = ['name']
    
    def clean(self) -> None:
        """Perform model-level validation."""
        super().clean()
        
        # Validate and normalize tag name
        if self.name:
            validate_tag_name(self.name)
            # Normalize the name by stripping whitespace
            self.name = self.name.strip()
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure validation is called."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.name
