from django.db import models
from django.core.exceptions import ValidationError
from common.models import BaseModel
from accounts.models import CustomUser


def validate_project_code(value: str) -> None:
    """Validate project code format and content."""
    if not value or not value.strip():
        raise ValidationError('Project code cannot be empty or just whitespace.')
    
    # Use stripped value for further validation
    stripped_value = value.strip().upper()
    
    if len(stripped_value) != 3:
        raise ValidationError('Project code must be exactly 3 characters long.')
    
    # Check if contains only letters
    if not stripped_value.isalpha():
        raise ValidationError('Project code can only contain letters.')


def validate_project_name(value: str) -> None:
    """Validate project name format and content."""
    if not value or not value.strip():
        raise ValidationError('Project name cannot be empty or just whitespace.')
    
    stripped_value = value.strip()
    
    if len(stripped_value) < 3:
        raise ValidationError('Project name must be at least 3 characters long.')
    
    if len(stripped_value) > 100:
        raise ValidationError('Project name cannot exceed 100 characters.')


class Project(BaseModel):
    """
    Project model for organizing tasks.
    Each project has a unique 3-character code used for generating task keys.
    """
    code = models.CharField(
        max_length=3,
        unique=True,
        validators=[validate_project_code],
        help_text="3-character project code (e.g., 'PRJ', 'API', 'WEB')"
    )
    name = models.CharField(
        max_length=100,
        validators=[validate_project_name],
        help_text="Full project name"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional project description"
    )
    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_projects',
        help_text="Project owner/manager"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the project is active and accepting new tasks"
    )
    
    class Meta:
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                models.functions.Upper('code'),
                name='unique_project_code_case_insensitive'
            )
        ]
    
    def clean(self) -> None:
        """Perform model-level validation."""
        super().clean()
        
        if self.code:
            validate_project_code(self.code)
            # Normalize the code by converting to uppercase and stripping
            self.code = self.code.strip().upper()
        
        if self.name:
            validate_project_name(self.name)
            # Normalize the name by stripping whitespace
            self.name = self.name.strip()
    
    def save(self, *args, **kwargs):
        """Override save to ensure validation is called."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return f"{self.code} - {self.name}"