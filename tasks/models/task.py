import uuid
from typing import Any
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from .validators import validate_task_title, validate_task_estimate
from .choices import TaskStatus


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    tags = models.ManyToManyField('Tag', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['assignee']),
            models.Index(fields=['-updated_at']),
        ]
        ordering = ['-updated_at']
    
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
    
    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save to ensure validation is called."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self) -> str:
        return self.title
