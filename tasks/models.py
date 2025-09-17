import uuid
from typing import Any, Dict
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError


def validate_task_title(value: str) -> None:
    """Validate that task title is not empty or just whitespace."""
    if not value or not value.strip():
        raise ValidationError('Task title cannot be empty or just whitespace.')
    if len(value.strip()) < 3:
        raise ValidationError('Task title must be at least 3 characters long.')


def validate_task_estimate(value: int | None) -> None:
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


class TaskStatus(models.TextChoices):
    TODO = 'TODO', 'To Do'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    BLOCKED = 'BLOCKED', 'Blocked'
    DONE = 'DONE', 'Done'


class ActivityType(models.TextChoices):
    CREATED = 'CREATED', 'Created'
    UPDATED_STATUS = 'UPDATED_STATUS', 'Status Updated'
    UPDATED_ASSIGNEE = 'UPDATED_ASSIGNEE', 'Assignee Updated'
    UPDATED_ESTIMATE = 'UPDATED_ESTIMATE', 'Estimate Updated'
    UPDATED_DESCRIPTION = 'UPDATED_DESCRIPTION', 'Description Updated'
    DELETED = 'DELETED', 'Deleted'


class Tag(models.Model):
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
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='assigned_tasks'
    )
    reporter = models.ForeignKey(
        User, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='reported_tasks'
    )
    tags = models.ManyToManyField(Tag, blank=True)
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


class TaskActivity(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=30, choices=ActivityType.choices)
    field = models.CharField(max_length=50, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['task', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"{self.task.title} - {self.type}"
