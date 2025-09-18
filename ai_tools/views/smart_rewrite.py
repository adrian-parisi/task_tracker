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
def smart_rewrite_view(request: Request, task_id: str) -> Response:
    """
    Generate a smart rewrite for a task with enhanced description and user story format.
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to rewrite
        
    Returns:
        JSON response with title and user_story fields
    """
    # Validate task_id format and get task
    task = validate_and_get_task(task_id)
    
    # Generate rewrite using AI service
    ai_service = get_ai_service()
    rewrite_data = ai_service.generate_rewrite(task)
    
    # Log the AI tool invocation
    logger.info(f"Smart rewrite generated for task {task.id} by user {request.user.id}")
    
    return Response(rewrite_data, status=status.HTTP_200_OK)
