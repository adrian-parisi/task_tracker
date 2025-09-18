"""
Models for AI tools app.
"""
import uuid
from django.db import models
from django.utils import timezone


class AIOperation(models.Model):
    """Track AI operations for async processing."""
    
    OPERATION_TYPES = [
        ('SUMMARY', 'Smart Summary'),
        ('ESTIMATE', 'Smart Estimate'),
        ('REWRITE', 'Smart Rewrite'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    task = models.ForeignKey('tasks.Task', on_delete=models.CASCADE)
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    result = models.JSONField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.operation_type} for Task {self.task.id} - {self.status}"
