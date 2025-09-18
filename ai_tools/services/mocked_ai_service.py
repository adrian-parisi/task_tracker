"""
Mocked AI Service for task management functionality.
Provides deterministic mocked AI responses for Smart Summary, Smart Estimate, and Smart Rewrite tools.
"""
import logging
import statistics
from typing import Dict, Any, List
from tasks.models import Task, ActivityType
logger = logging.getLogger(__name__)


class MockedAIService:
    """Mocked AI service implementation for testing and development."""
    
    def generate_summary(self, task: Task) -> str:
        """
        Generate a human-readable summary of the task lifecycle based on activities.
        
        This method provides deterministic mocked responses based on task state.
        
        Args:
            task: The task to generate summary for
            
        Returns:
            Human-readable summary string
        """
        try:
            # Get task activities for analysis
            activities = task.activities.all().order_by('created_at')
            activity_count = activities.count()
            
            # Generate deterministic summary based on task state
            summary = self._generate_deterministic_summary(task, activities, activity_count)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for task {task.id}: {str(e)}")
            return "Unable to generate summary at this time."
    
    def generate_rewrite(self, task: Task) -> Dict[str, str]:
        """
        Generate an enhanced task description with user story format and acceptance criteria.
        
        This method provides deterministic mocked responses based on task content.
        
        Args:
            task: The task to rewrite
            
        Returns:
            Dictionary with 'title' and 'user_story' keys
        """
        try:
            # Generate deterministic rewrite based on task content
            rewrite_data = self._generate_deterministic_rewrite(task)
            
            return rewrite_data
            
        except Exception as e:
            logger.error(f"Error generating rewrite for task {task.id}: {str(e)}")
            return {
                'title': task.title,
                'user_story': 'Unable to generate enhanced description at this time.'
            }
    
    def generate_estimate(self, task: Task) -> Dict[str, Any]:
        """
        Generate a smart estimate suggestion for a task based on similar tasks.
        
        Args:
            task: Task instance to generate estimate for
            
        Returns:
            Dictionary containing:
            - suggested_points: Median estimate from similar tasks or fallback
            - confidence: Confidence score (0.0 to 1.0)
            - similar_task_ids: List of up to 5 most recent similar task IDs
            - rationale: Human-readable explanation
        """
        try:
            # Find similar tasks using internal similarity matching
            similar_tasks = self._find_similar_tasks(task, limit=20)
            
            # Filter to only tasks with estimates
            tasks_with_estimates = [t for t in similar_tasks if t.estimate is not None]
            
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
            confidence = self._calculate_estimate_confidence(estimates, len(similar_tasks))
            
            # Get up to 5 most recent similar task IDs for reference
            similar_task_ids = [str(t.id) for t in similar_tasks[:5]]
            
            # Generate rationale
            rationale = self._generate_estimate_rationale(
                len(estimates), median_estimate, confidence
            )
            
            return {
                'suggested_points': int(median_estimate),
                'confidence': round(confidence, 2),
                'similar_task_ids': similar_task_ids,
                'rationale': rationale
            }
            
        except Exception as e:
            logger.error(f"Error generating estimate for task {task.id}: {str(e)}")
            return {
                'suggested_points': 3,
                'confidence': 0.40,
                'similar_task_ids': [],
                'rationale': 'Unable to generate estimate at this time.'
            }
    
    def _generate_deterministic_summary(self, task: Task, activities, activity_count: int) -> str:
        """
        Generate deterministic summary based on task state and activities.
        
        Args:
            task: The task instance
            activities: QuerySet of task activities
            activity_count: Number of activities
            
        Returns:
            Deterministic summary string
        """
        # Base summary components
        status_text = task.get_status_display()
        
        # Determine task progression narrative
        if activity_count == 1:
            # Only creation activity
            progression = f"This task was created and is currently {status_text.lower()}."
        elif activity_count <= 3:
            progression = f"This task has had {activity_count} activities and is currently {status_text.lower()}."
        else:
            progression = f"This task has been actively worked on with {activity_count} activities and is currently {status_text.lower()}."
        
        # Add assignee information if available
        assignee_info = ""
        if task.assignee:
            assignee_info = f" It is assigned to {task.assignee.username}."
        
        # Add estimate information if available
        estimate_info = ""
        if task.estimate:
            estimate_info = f" The estimated effort is {task.estimate} points."
        
        # Add tags information if available
        tags_info = ""
        if task.tags:
            tag_names = task.tags
            if len(tag_names) == 1:
                tags_info = f" It is tagged with '{tag_names[0]}'."
            else:
                tags_info = f" It is tagged with {', '.join(tag_names[:-1])} and '{tag_names[-1]}'."
        
        # Combine all parts
        summary = progression + assignee_info + estimate_info + tags_info
        
        # Add status-specific insights
        if task.status == 'DONE':
            summary += " The task has been completed successfully."
        elif task.status == 'BLOCKED':
            summary += " The task is currently blocked and may need attention."
        elif task.status == 'IN_PROGRESS':
            summary += " Work is actively in progress on this task."
        
        return summary.strip()
    
    def _generate_deterministic_rewrite(self, task: Task) -> Dict[str, str]:
        """
        Generate deterministic rewrite with user story format.
        
        Args:
            task: The task instance
            
        Returns:
            Dictionary with enhanced title and user story
        """
        # Preserve original title
        enhanced_title = task.title
        
        # Generate user story based on task content
        # Use deterministic logic based on task attributes
        
        # Determine user role based on task assignee
        if task.assignee and 'dev' in task.assignee.username.lower():
            user_role = "developer"
        elif task.assignee and any(keyword in task.assignee.username.lower() for keyword in ['pm', 'manager']):
            user_role = "project manager"
        elif task.assignee and ('qa' in task.assignee.username.lower() or 'tester' in task.assignee.username.lower()):
            user_role = "QA engineer"
        else:
            user_role = "user"
        
        # Generate want statement based on title
        title_lower = task.title.lower()
        if 'fix' in title_lower or 'bug' in title_lower:
            want_statement = f"resolve the issue described in '{task.title}'"
        elif 'update' in title_lower or 'modify' in title_lower or 'change' in title_lower or 'improve' in title_lower:
            want_statement = f"see the improvements described in '{task.title}'"
        elif 'add' in title_lower or 'create' in title_lower or 'implement' in title_lower:
            want_statement = f"have the functionality described in '{task.title}'"
        else:
            want_statement = f"complete the work described in '{task.title}'"
        
        # Generate benefit statement
        if 'performance' in title_lower or 'optimize' in title_lower:
            benefit = "the system performs better"
        elif 'security' in title_lower or 'auth' in title_lower:
            benefit = "the system is more secure"
        elif 'ui' in title_lower or 'interface' in title_lower or 'frontend' in title_lower or 'improve' in title_lower:
            benefit = "the user experience is improved"
        elif task.status == 'DONE':
            benefit = "the system functions as expected"
        else:
            benefit = "the system meets the requirements"
        
        # Construct user story
        user_story = f"As a {user_role}, I want to {want_statement}, so that {benefit}.\n\n"
        
        # Add acceptance criteria based on task description and status
        user_story += "Acceptance Criteria:\n"
        
        if task.description and len(task.description.strip()) > 10:
            # Generate criteria based on description content
            desc_lower = task.description.lower()
            if 'should' in desc_lower:
                user_story += "1. WHEN the implementation is complete THEN the system SHALL meet the requirements described in the task description\n"
            else:
                user_story += "1. WHEN the feature is implemented THEN the system SHALL function according to the task description\n"
        else:
            user_story += "1. WHEN the task is implemented THEN the system SHALL meet the specified requirements\n"
        
        # Add status-specific criteria
        if task.estimate and task.estimate > 0:
            user_story += f"2. WHEN the work is completed THEN it SHALL be delivered within the estimated {task.estimate} points of effort\n"
        
        # Add tag-based criteria
        if task.tags:  # JSONField - direct list access
            tag_names = task.tags
            if 'frontend' in [t.lower() for t in tag_names]:
                user_story += "3. WHEN the frontend changes are made THEN the user interface SHALL be responsive and accessible\n"
            elif 'backend' in [t.lower() for t in tag_names]:
                user_story += "3. WHEN the backend changes are made THEN the API SHALL return appropriate responses and handle errors gracefully\n"
            elif 'testing' in [t.lower() for t in tag_names]:
                user_story += "3. WHEN the implementation is complete THEN appropriate test coverage SHALL be provided\n"
        
        # Final acceptance criterion
        user_story += f"4. WHEN the task is marked as {task.get_status_display()} THEN all acceptance criteria SHALL be verified"
        
        return {
            'title': enhanced_title,
            'user_story': user_story
        }
    
    def _find_similar_tasks(self, task: Task, limit: int = 20) -> List[Task]:
        """
        Find similar tasks based on rule-based matching criteria with priority scoring.
        
        Similarity is determined by (in priority order):
        1. Same assignee (score: 100)
        2. Overlapping tags (score: 80 per tag)
        3. Title word overlap (score: up to 60)
        4. Description word overlap (score: up to 40)
        
        Args:
            task: The task to find similar tasks for
            limit: Maximum number of similar tasks to return
            
        Returns:
            List of similar tasks, ordered by similarity score (highest first)
        """
        # Get all tasks except the current one
        all_tasks = list(Task.objects.exclude(id=task.id).select_related('assignee', 'project'))
        
        # Score each task based on similarity criteria
        scored_tasks = []
        
        for candidate_task in all_tasks:
            score = 0
            
            # 1. Same assignee (highest priority - 100 points)
            if task.assignee and candidate_task.assignee and task.assignee.id == candidate_task.assignee.id:
                score += 100
            
            # 2. Overlapping tags (80 points per matching tag) - JSONField comparison
            if task.tags and candidate_task.tags:
                task_tags = set(task.tags)  # JSONField - direct list access
                candidate_tags = set(candidate_task.tags)  # JSONField - direct list access
                overlapping_tags = task_tags.intersection(candidate_tags)
                score += len(overlapping_tags) * 80
            
            # 3. Title word overlap (up to 60 points)
            if task.title and candidate_task.title:
                task_title_words = set(task.title.lower().split())
                candidate_title_words = set(candidate_task.title.lower().split())
                # TODO: Omit connectors like "and", "or", "but", etc.
                word_overlap = len(task_title_words.intersection(candidate_title_words))
                if word_overlap > 0:
                    score += min(word_overlap * 20, 60)  # Cap at 60 points
            
            # 4. Description word overlap (up to 40 points)
            if task.description and candidate_task.description:
                task_desc_words = set(task.description.lower().split())
                candidate_desc_words = set(candidate_task.description.lower().split())
                word_overlap = len(task_desc_words.intersection(candidate_desc_words))
                if word_overlap > 0:
                    score += min(word_overlap * 5, 40)  # Cap at 40 points
            
            # Only include tasks with some similarity
            if score > 0:
                scored_tasks.append((candidate_task, score))
        
        # Sort by score (highest first), then by updated_at (most recent first) for ties
        scored_tasks.sort(key=lambda x: (-x[1], -x[0].updated_at.timestamp()))
        
        # Return the top results
        return [task for task, score in scored_tasks[:limit]]
    
    def _calculate_estimate_confidence(self, estimates: List[int], total_similar_tasks: int) -> float:
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
    
    def _generate_estimate_rationale(self, estimate_count: int, median_estimate: int, confidence: float) -> str:
        """
        Generate human-readable rationale for estimate suggestion.
        
        Args:
            estimate_count: Number of similar tasks with estimates
            median_estimate: Median estimate value
            confidence: Confidence score
            
        Returns:
            Human-readable rationale string
        """
        if estimate_count == 0:
            return "No similar tasks found with estimates. Suggesting default 3 points."
        
        rationale = f"Based on {estimate_count} similar task"
        if estimate_count > 1:
            rationale += "s"
        rationale += f", median estimate is {median_estimate} points"
        
        if confidence >= 0.8:
            rationale += " (high confidence)"
        elif confidence >= 0.6:
            rationale += " (medium confidence)"
        else:
            rationale += " (low confidence)"
        
        return rationale
