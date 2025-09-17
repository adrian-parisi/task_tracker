"""
AI Services for task management functionality.
Provides deterministic mocked AI responses for Smart Summary, Smart Estimate, and Smart Rewrite tools.
"""
import logging
import time
from typing import Dict, Any
from django.contrib.auth.models import User
from tasks.models import Task, ActivityType


logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered task tools with deterministic mocked responses."""
    
    @staticmethod
    def generate_summary(task: Task, user: User = None) -> str:
        """
        Generate a human-readable summary of the task lifecycle based on activities.
        
        This method provides deterministic mocked responses based on task state.
        
        Args:
            task: The task to generate summary for
            user: User requesting the summary (for logging)
            
        Returns:
            Human-readable summary string
        """
        start_time = time.time()
        
        try:
            # Get task activities for analysis
            activities = task.activities.all().order_by('created_at')
            activity_count = activities.count()
            
            # Generate deterministic summary based on task state
            summary = AIService._generate_deterministic_summary(task, activities, activity_count)
            
            # Log the AI tool invocation
            response_time_ms = int((time.time() - start_time) * 1000)
            AIService._log_ai_invocation(
                tool_type='smart_summary',
                task_id=str(task.id),
                user_id=user.id if user else None,
                response_time_ms=response_time_ms
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary for task {task.id}: {str(e)}")
            return "Unable to generate summary at this time."
    
    @staticmethod
    def generate_rewrite(task: Task, user: User = None) -> Dict[str, str]:
        """
        Generate an enhanced task description with user story format and acceptance criteria.
        
        This method provides deterministic mocked responses based on task content.
        
        Args:
            task: The task to rewrite
            user: User requesting the rewrite (for logging)
            
        Returns:
            Dictionary with 'title' and 'user_story' keys
        """
        start_time = time.time()
        
        try:
            # Generate deterministic rewrite based on task content
            rewrite_data = AIService._generate_deterministic_rewrite(task, user)
            
            # Log the AI tool invocation
            response_time_ms = int((time.time() - start_time) * 1000)
            AIService._log_ai_invocation(
                tool_type='smart_rewrite',
                task_id=str(task.id),
                user_id=user.id if user else None,
                response_time_ms=response_time_ms
            )
            
            return rewrite_data
            
        except Exception as e:
            logger.error(f"Error generating rewrite for task {task.id}: {str(e)}")
            return {
                'title': task.title,
                'user_story': 'Unable to generate enhanced description at this time.'
            }
    
    @staticmethod
    def _generate_deterministic_summary(task: Task, activities, activity_count: int) -> str:
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
        tags = list(task.tags.all())
        if tags:
            tag_names = [tag.name for tag in tags]
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
    
    @staticmethod
    def _generate_deterministic_rewrite(task: Task, user: User = None) -> Dict[str, str]:
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
        
        # Determine user role based on user characteristics (use requesting user if available, fallback to assignee)
        role_user = user if user else task.assignee
        if role_user and 'dev' in role_user.username.lower():
            user_role = "developer"
        elif role_user and any(keyword in role_user.username.lower() for keyword in ['pm', 'manager']):
            user_role = "project manager"
        elif role_user and ('qa' in role_user.username.lower() or 'tester' in role_user.username.lower()):
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
        tags = list(task.tags.all())
        if tags:
            tag_names = [tag.name for tag in tags]
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
    
    @staticmethod
    def _log_ai_invocation(tool_type: str, task_id: str, user_id: int = None, response_time_ms: int = 0):
        """
        Log AI tool invocation with telemetry data.
        
        Args:
            tool_type: Type of AI tool used (smart_summary, smart_estimate, smart_rewrite)
            task_id: ID of the task the tool was used on
            user_id: ID of the user who invoked the tool
            response_time_ms: Response time in milliseconds
        """
        logger.info(
            "AI tool invocation",
            extra={
                'tool_type': tool_type,
                'task_id': task_id,
                'user_id': user_id,
                'response_time_ms': response_time_ms
            }
        )