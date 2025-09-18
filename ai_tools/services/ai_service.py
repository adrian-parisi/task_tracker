"""
Real AI Service for task management functionality.
"""
from typing import Dict, Any
from tasks.models import Task


class AIService:
    """Real AI service implementation (not yet implemented)."""
    
    def generate_summary(self, task: Task) -> str:
        """
        Generate a smart summary for a task using real AI.
        
        Args:
            task: Task instance to generate summary for
            
        Returns:
            Human-readable summary string
        """
        raise NotImplementedError("Real AI service not yet implemented. Use MockedAIService for now.")
    
    def generate_rewrite(self, task: Task) -> Dict[str, Any]:
        """
        Generate a smart rewrite for a task using real AI.
        
        Args:
            task: Task instance to rewrite
            
        Returns:
            Dictionary with 'title' and 'user_story' keys
        """
        raise NotImplementedError("Real AI service not yet implemented. Use MockedAIService for now.")
    
    def generate_estimate(self, task: Task) -> Dict[str, Any]:
        """
        Generate a smart estimate suggestion for a task using real AI.
        
        Args:
            task: Task instance to generate estimate for
            
        Returns:
            Dictionary with suggested_points, confidence, similar_task_ids, and rationale
        """
        raise NotImplementedError("Real AI service not yet implemented. Use MockedAIService for now.")
