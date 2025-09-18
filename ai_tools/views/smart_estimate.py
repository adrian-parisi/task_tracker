from typing import Any
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from ..services import get_ai_service
from ..utils import validate_and_get_task

logger = logging.getLogger(__name__)


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
    # Validate task_id format and get task
    task = validate_and_get_task(task_id)
    
    # Generate estimate using AI service
    ai_service = get_ai_service()
    estimate_data = ai_service.generate_estimate(task)
    
    # Log the AI tool invocation
    logger.info(f"Smart estimate generated for task {task.id} by user {request.user.id}")
    
    return Response(estimate_data, status=status.HTTP_200_OK)
