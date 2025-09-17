"""
Services for task management functionality.
"""
from typing import Dict, Any, List
import statistics
from django.contrib.auth import get_user_model

User = get_user_model()
from django.db.models import QuerySet, Q
from .models import Task, TaskActivity, ActivityType


class ActivityService:
    """Service for logging task activities and changes."""
    
    # Fields that should be tracked for changes
    TRACKED_FIELDS = {
        'status': ActivityType.UPDATED_STATUS,
        'assignee': ActivityType.UPDATED_ASSIGNEE,
        'estimate': ActivityType.UPDATED_ESTIMATE,
        'description': ActivityType.UPDATED_DESCRIPTION,
    }
    
    @staticmethod
    def log_task_creation(task: Task, actor: User | None = None) -> TaskActivity:
        """
        Log task creation activity.
        
        Args:
            task: The created task
            actor: User who created the task
            
        Returns:
            Created TaskActivity instance
        """
        return TaskActivity.objects.create(
            task=task,
            actor=actor,
            type=ActivityType.CREATED,
            field='',
            before=None,
            after=None
        )
    
    @staticmethod
    def log_field_changes(
        task: Task, 
        changes: Dict[str, Dict[str, Any]], 
        actor: User | None = None
    ) -> list[TaskActivity]:
        """
        Log field changes for a task, creating separate activities for each tracked field.
        
        Args:
            task: The task that was updated
            changes: Dictionary with field names as keys and {'before': old_value, 'after': new_value} as values
            actor: User who made the changes
            
        Returns:
            List of created TaskActivity instances
        """
        activities = []
        
        for field_name, change_data in changes.items():
            if field_name in ActivityService.TRACKED_FIELDS:
                activity_type = ActivityService.TRACKED_FIELDS[field_name]
                
                # Handle special cases for serialization
                before_value = ActivityService._serialize_field_value(
                    field_name, change_data['before']
                )
                after_value = ActivityService._serialize_field_value(
                    field_name, change_data['after']
                )
                
                activity = TaskActivity.objects.create(
                    task=task,
                    actor=actor,
                    type=activity_type,
                    field=field_name,
                    before=before_value,
                    after=after_value
                )
                activities.append(activity)
        
        return activities
    
    @staticmethod
    def _serialize_field_value(field_name: str, value: Any) -> Any:
        """
        Serialize field values for JSON storage.
        
        Args:
            field_name: Name of the field
            value: Value to serialize
            
        Returns:
            JSON-serializable value
        """
        if value is None:
            return None
        
        # Handle User objects (assignee)
        if field_name == 'assignee' and hasattr(value, 'id'):
            return {
                'id': value.id,
                'username': value.username,
                'email': value.email
            }
        
        # Handle other object types that need special serialization
        if hasattr(value, 'pk'):
            return str(value.pk)
        
        return value
    
    @staticmethod
    def detect_field_changes(old_instance: Task, new_instance: Task) -> Dict[str, Dict[str, Any]]:
        """
        Detect changes between old and new task instances.
        
        Args:
            old_instance: Task instance before changes
            new_instance: Task instance after changes
            
        Returns:
            Dictionary of changes with field names as keys
        """
        changes = {}
        
        for field_name in ActivityService.TRACKED_FIELDS.keys():
            old_value = getattr(old_instance, field_name, None)
            new_value = getattr(new_instance, field_name, None)
            
            # Compare values, handling None cases
            if old_value != new_value:
                changes[field_name] = {
                    'before': old_value,
                    'after': new_value
                }
        
        return changes


class SimilarityService:
    """Service for finding similar tasks and calculating estimate suggestions."""
    
    @staticmethod
    def find_similar_tasks(task: Task, limit: int = 20) -> QuerySet:
        """
        Find similar tasks based on rule-based matching criteria.
        
        Similarity is determined by (in priority order):
        1. Same assignee
        2. Overlapping tags
        3. Title substring match (first 20 chars)
        4. Description substring match (first 40 chars)
        
        Args:
            task: The task to find similar tasks for
            limit: Maximum number of similar tasks to return
            
        Returns:
            QuerySet of similar tasks, ordered by updated_at descending
        """
        # Exclude the task itself from results and optimize with select_related
        similar_tasks = Task.objects.exclude(id=task.id).select_related('assignee')
        
        # Build query conditions for similarity matching
        similarity_conditions = Q()
        
        # 1. Same assignee (highest priority)
        if task.assignee:
            similarity_conditions |= Q(assignee=task.assignee)
        
        # 2. Overlapping tags - optimize by prefetching tags only when needed
        task_tags = list(task.tags.values_list('id', flat=True))
        if task_tags:
            similarity_conditions |= Q(tags__in=task_tags)
        
        # 3. Title substring matching (first 20 chars, case-insensitive)
        if task.title and len(task.title.strip()) >= 3:
            title_substring = task.title.strip()[:20]
            similarity_conditions |= Q(title__icontains=title_substring)
        
        # 4. Description substring matching (first 40 chars, case-insensitive)
        if task.description and len(task.description.strip()) >= 5:
            desc_substring = task.description.strip()[:40]
            similarity_conditions |= Q(description__icontains=desc_substring)
        
        # Apply similarity conditions and order by updated_at descending
        if similarity_conditions:
            return (similar_tasks
                   .filter(similarity_conditions)
                   .distinct()
                   .order_by('-updated_at')[:limit])
        else:
            # If no similarity conditions, return empty queryset
            return Task.objects.none()
    
    @staticmethod
    def calculate_estimate_suggestion(task: Task) -> Dict[str, Any]:
        """
        Calculate estimate suggestion based on similar tasks.
        
        Args:
            task: The task to calculate estimate for
            
        Returns:
            Dictionary containing:
            - suggested_points: Median estimate from similar tasks or fallback
            - confidence: Confidence score (0.0 to 1.0)
            - similar_task_ids: List of up to 5 most recent similar task IDs
            - rationale: Human-readable explanation
        """
        # Find similar tasks (get all similar tasks first, then filter)
        all_similar_tasks = SimilarityService.find_similar_tasks(task, limit=20)
        
        # Convert to list to avoid slice issues
        similar_tasks_list = list(all_similar_tasks)
        
        # Filter to only tasks with estimates
        tasks_with_estimates = [t for t in similar_tasks_list if t.estimate is not None]
        
        if not tasks_with_estimates:
            # No similar tasks with estimates - return fallback
            return {
                'suggested_points': 3,
                'confidence': 0.40,
                'similar_task_ids': [],
                'rationale': 'No similar tasks found with estimates. Suggesting default 3 points.'
            }
        
        # Calculate median estimate
        estimates = [t.estimate for t in tasks_with_estimates]
        median_estimate = statistics.median(estimates)
        
        # Calculate confidence based on number of similar tasks and estimate consistency
        confidence = SimilarityService._calculate_confidence(estimates, len(similar_tasks_list))
        
        # Get up to 5 most recent similar task IDs for reference
        similar_task_ids = [str(t.id) for t in similar_tasks_list[:5]]
        
        # Generate rationale
        rationale = SimilarityService._generate_rationale(
            len(estimates), median_estimate, confidence
        )
        
        return {
            'suggested_points': int(median_estimate),
            'confidence': round(confidence, 2),
            'similar_task_ids': similar_task_ids,
            'rationale': rationale
        }
    
    @staticmethod
    def _calculate_confidence(estimates: List[int], total_similar_tasks: int) -> float:
        """
        Calculate confidence score based on estimate data.
        
        Args:
            estimates: List of estimate values from similar tasks
            total_similar_tasks: Total number of similar tasks found
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not estimates:
            return 0.40
        
        # Base confidence starts at 0.65 if we have estimates
        base_confidence = 0.65
        
        # Adjust based on number of estimates (more estimates = higher confidence)
        estimate_count_factor = min(len(estimates) / 5.0, 1.0) * 0.15
        
        # Adjust based on estimate consistency (lower variance = higher confidence)
        if len(estimates) > 1:
            estimate_variance = statistics.variance(estimates)
            max_variance = max(estimates) ** 2  # Normalize variance
            consistency_factor = (1.0 - min(estimate_variance / max_variance, 1.0)) * 0.10
        else:
            consistency_factor = 0.05  # Small bonus for single estimate
        
        # Adjust based on total similar tasks found (more context = higher confidence)
        context_factor = min(total_similar_tasks / 10.0, 1.0) * 0.10
        
        final_confidence = base_confidence + estimate_count_factor + consistency_factor + context_factor
        
        # Cap confidence at 0.95 (never 100% certain)
        return min(final_confidence, 0.95)
    
    @staticmethod
    def _generate_rationale(estimate_count: int, median_estimate: float, confidence: float) -> str:
        """
        Generate human-readable rationale for the estimate suggestion.
        
        Args:
            estimate_count: Number of similar tasks with estimates
            median_estimate: Calculated median estimate
            confidence: Confidence score
            
        Returns:
            Human-readable rationale string
        """
        if estimate_count == 0:
            return "No similar tasks found with estimates. Suggesting default 3 points."
        
        confidence_level = "high" if confidence >= 0.80 else "medium" if confidence >= 0.65 else "low"
        
        if estimate_count == 1:
            return f"Based on 1 similar task with estimate {int(median_estimate)}. Confidence: {confidence_level}."
        else:
            return f"Based on median of {estimate_count} similar tasks (median: {int(median_estimate)} points). Confidence: {confidence_level}."