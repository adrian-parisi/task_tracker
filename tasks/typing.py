"""
Type aliases and typing utilities for the task management system.
"""
from typing import Any, Dict, List, Union
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import QuerySet
from .models import Task, Tag, TaskActivity

# Type aliases for common patterns
TaskQuerySet = QuerySet[Task]
TagQuerySet = QuerySet[Tag]
ActivityQuerySet = QuerySet[TaskActivity]
UserQuerySet = QuerySet[User]

# API Response types
APIResponse = Dict[str, Any]
ErrorResponse = Dict[str, Union[str, Dict[str, List[str]]]]

# Service method return types
ActivityChanges = Dict[str, Dict[str, Any]]
SimilarityResult = Dict[str, Any]
AISummaryResponse = Dict[str, str]
AIEstimateResponse = Dict[str, Union[int, float, List[str], str]]
AIRewriteResponse = Dict[str, str]

# Validation types
ValidationErrors = Dict[str, List[str]]
FieldValidationResult = Union[str, int, None]

# Pagination types
PaginationParams = Dict[str, Union[int, str, None]]

# Filter types
TaskFilters = Dict[str, Union[str, int, List[int], None]]
TagFilters = Dict[str, Union[str, None]]

# Serializer data types
TaskCreateData = Dict[str, Any]
TaskUpdateData = Dict[str, Any]
TagCreateData = Dict[str, str]
TagUpdateData = Dict[str, str]

# Signal types
SignalSender = type[Task]
SignalInstance = Task
SignalCreated = bool
SignalKwargs = Dict[str, Any]

# View types
ViewRequest = Any  # Will be properly typed when DRF types are available
ViewResponse = Any  # Will be properly typed when DRF types are available
ViewKwargs = Dict[str, Any]

# Activity logging types
ActivityActor = User | None
ActivityType = str
ActivityField = str
ActivityBefore = Any
ActivityAfter = Any

# Similarity calculation types
SimilarityConditions = Any  # Django Q objects
EstimateData = List[int]
ConfidenceScore = float
SimilarTaskIds = List[str]
RationaleText = str

# AI Service types
AIToolType = str
TaskId = str
UserId = int | None
ResponseTimeMs = int
AILogData = Dict[str, Union[str, int, None]]

# Model field types
TaskStatus = str
TaskTitle = str
TaskDescription = str
TaskEstimate = int | None
TaskAssignee = User | None
TaskReporter = User | None
TaskTags = List[Tag]
TaskCreatedAt = Any  # datetime
TaskUpdatedAt = Any  # datetime

# Activity model types
ActivityTask = Task
ActivityActor = User | None
ActivityType = str
ActivityField = str
ActivityBefore = Any
ActivityAfter = Any
ActivityCreatedAt = Any  # datetime

# Tag model types
TagName = str
TagId = int

# User model types
UserId = int
Username = str
UserEmail = str
UserFirstName = str
UserLastName = str
UserIsActive = bool
