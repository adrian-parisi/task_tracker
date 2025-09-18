from typing import Any
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from common.models import BaseModel
from accounts.models import CustomUser
from .validators import validate_task_title, validate_task_estimate
from .choices import TaskStatus


class Task(BaseModel):
    key = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text="Auto-generated task key (e.g., 'PRJ-123')"
    )
    project = models.ForeignKey(
        'Project',
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text="Project this task belongs to"
    )
    title = models.CharField(
        max_length=200,
        validators=[validate_task_title]
    )
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, 
        choices=TaskStatus.choices, 
        default=TaskStatus.TODO
    )
    estimate = models.PositiveIntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), validate_task_estimate]
    )
    assignee = models.ForeignKey(
        CustomUser, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='assigned_tasks'
    )
    reporter = models.ForeignKey(
        CustomUser, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='reported_tasks'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of tag names as strings"
    )
    
    class Meta:
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['project']),
            models.Index(fields=['status']),
            models.Index(fields=['assignee']),
            models.Index(fields=['-updated_at']),
            models.Index(fields=['project', '-created_at']),  # For project task listing
        ]
        constraints = [
            models.UniqueConstraint(fields=['key'], name='unique_task_key')
        ]
    
    def clean(self) -> None:
        """Perform model-level validation."""
        super().clean()
        
        # Validate title
        if self.title:
            validate_task_title(self.title)
        
        # Validate estimate
        if self.estimate is not None:
            validate_task_estimate(self.estimate)
        
        # Business rule: Task cannot be marked as DONE without an estimate
        if self.status == TaskStatus.DONE and self.estimate is None:
            raise ValidationError({
                'estimate': 'Tasks marked as DONE must have an estimate.'
            })
    
    def _generate_task_key(self) -> str:
        """
        Generate the next sequential task key for this project.
        Uses database-level atomic operations to ensure consistency.
        """
        if not self.project:
            raise ValidationError("Project is required to generate task key.")
        
        # Get the highest sequence number for this project using Django ORM
        # This is more database-agnostic than raw SQL
        prefix = f"{self.project.code}-"
        
        # Get all tasks for this project and extract the highest number
        existing_tasks = Task.objects.filter(
            key__startswith=prefix
        ).values_list('key', flat=True)
        
        max_number = 0
        for key in existing_tasks:
            try:
                # Extract number after the dash
                number_part = key.split('-', 1)[1]
                number = int(number_part)
                max_number = max(max_number, number)
            except (IndexError, ValueError):
                # Skip malformed keys
                continue
        
        next_number = max_number + 1
        return f"{self.project.code}-{next_number}"
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure validation is called and key is generated."""
        # Generate key if this is a new task
        if not self.key and self.project:
            # Use transaction to ensure atomicity
            with transaction.atomic():
                self.key = self._generate_task_key()
        
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.title
