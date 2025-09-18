"""
Protocols for AI services.
"""
from typing import Protocol, Dict, Any
from tasks.models import Task


class AIServiceProtocol(Protocol):
    """Protocol for AI service implementations."""
    
    def generate_summary(self, task: Task) -> str:
        """
        Generate a smart summary for a task.
        
        Args:
            task: Task instance to generate summary for
            
        Returns:
            Human-readable summary string
        """
        ...
    
    def generate_rewrite(self, task: Task) -> Dict[str, Any]:
        """
        Generate a smart rewrite for a task.
        
        Args:
            task: Task instance to rewrite
            
        Returns:
            Dictionary with 'title' and 'user_story' keys
        """
        ...
    
    def generate_estimate(self, task: Task) -> Dict[str, Any]:
        """
        Generate a smart estimate suggestion for a task.
        
        Args:
            task: Task instance to generate estimate for
            
        Returns:
            Dictionary with suggested_points, confidence, similar_task_ids, and rationale
        """
        ...
