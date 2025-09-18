from typing import Any
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..services.factory import get_ai_service
from ..utils import validate_and_get_task
from ..serializers import SmartRewriteResponseSerializer, ErrorResponseSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="smart_rewrite",
    summary="Generate AI rewrite for a task",
    description="Generate an enhanced task description with user story format and acceptance criteria.",
    request=None,
    responses={
        200: OpenApiResponse(
            response=SmartRewriteResponseSerializer,
            description="Successfully generated rewrite suggestion"
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Invalid task ID or task not found"
        ),
        401: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Authentication required"
        ),
        500: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Internal server error during rewrite generation"
        )
    },
    tags=["AI Tools"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_rewrite_view(request: Request, task_id: str) -> Response:
    """
    Generate AI rewrite synchronously and return the result.
    
    This endpoint enhances the task description by:
    - Converting to user story format (As a [user], I want [goal], so that [benefit])
    - Adding acceptance criteria
    - Improving clarity and structure
    - Maintaining the original intent while making it more actionable
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to rewrite
        
    Returns:
        JSON response with rewritten content including:
        - title: Enhanced task title
        - user_story: Complete user story with acceptance criteria
    """
    try:
        # Validate task_id format and get task
        task = validate_and_get_task(task_id)
        
        # Get AI service and generate rewrite
        ai_service = get_ai_service()
        rewrite_result = ai_service.generate_rewrite(task)
        
        # Log the AI tool invocation
        logger.info(f"Smart rewrite completed for Task {task.id} by user {request.user.id}")
        
        # Serialize and return response
        serializer = SmartRewriteResponseSerializer(rewrite_result)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error in smart rewrite for task {task_id}: {str(e)}")
        error_serializer = ErrorResponseSerializer({'error': 'Unable to generate rewrite at this time.'})
        return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
