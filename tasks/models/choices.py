from django.db import models


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
