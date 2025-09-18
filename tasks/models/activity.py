from django.db import models
from common.models import BaseModel
from accounts.models import CustomUser
from .choices import ActivityType


class TaskActivity(BaseModel):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL)
    type = models.CharField(max_length=30, choices=ActivityType.choices)
    field = models.CharField(max_length=50, blank=True)
    before = models.JSONField(null=True, blank=True)
    after = models.JSONField(null=True, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['task', '-created_at']),
        ]
    
    def __str__(self) -> str:
        return f"{self.task.title} - {self.type}"
