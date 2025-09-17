from typing import Any
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from django.shortcuts import get_object_or_404
from django.http import Http404
from tasks.models import Task
from tasks.services import SimilarityService
from .services import AIService
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_summary_view(request: Request, task_id: str) -> Response:
    """
    Generate a smart summary for a task.
    
    Returns a human-readable summary of the task lifecycle based on activities.
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to generate summary for
        
    Returns:
        JSON response with summary field
    """
    # Validate task_id format
    try:
        import uuid
        uuid.UUID(str(task_id))
    except (ValueError, TypeError):
        from rest_framework.exceptions import ValidationError
        raise ValidationError({
            'task_id': ['Invalid task ID format. Must be a valid UUID.']
        })
    
    # Get task or raise 404
    task = get_object_or_404(Task, id=task_id)
    
    # Generate summary using AI service
    summary = AIService.generate_summary(task, user=request.user)
    
    return Response({
        'summary': summary
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def smart_estimate_view(request: Request, task_id: str) -> Response:
    """
    Generate a smart estimate suggestion for a task.
    
    Uses similarity service to find similar tasks and calculate estimate suggestion.
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to generate estimate for
        
    Returns:
        JSON response with suggested_points, confidence, similar_task_ids, and rationale
    """
    # Validate task_id format
    try:
        import uuid
        uuid.UUID(str(task_id))
    except (ValueError, TypeError):
        from rest_framework.exceptions import ValidationError
        raise ValidationError({
            'task_id': ['Invalid task ID format. Must be a valid UUID.']
        })
    
    # Get task or raise 404
    task = get_object_or_404(Task, id=task_id)
    
    # Calculate estimate suggestion using similarity service
    estimate_data = SimilarityService.calculate_estimate_suggestion(task)
    
    # Log AI tool invocation (gracefully handle logging failures)
    try:
        AIService._log_ai_invocation(
            tool_type='smart_estimate',
            task_id=str(task.id),
            user_id=request.user.id,
            response_time_ms=0  # Will be calculated in service if needed
        )
    except Exception as e:
        # Log the logging failure but don't break the response
        logger.warning(f"Failed to log AI invocation: {e}")
    
    return Response(estimate_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_rewrite_view(request: Request, task_id: str) -> Response:
    """
    Generate a smart rewrite for a task with enhanced description and user story format.
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to rewrite
        
    Returns:
        JSON response with title and user_story fields
    """
    # Validate task_id format
    try:
        import uuid
        uuid.UUID(str(task_id))
    except (ValueError, TypeError):
        from rest_framework.exceptions import ValidationError
        raise ValidationError({
            'task_id': ['Invalid task ID format. Must be a valid UUID.']
        })
    
    # Get task or raise 404
    task = get_object_or_404(Task, id=task_id)
    
    # Generate rewrite using AI service
    rewrite_data = AIService.generate_rewrite(task, user=request.user)
    
    return Response(rewrite_data, status=status.HTTP_200_OK)
