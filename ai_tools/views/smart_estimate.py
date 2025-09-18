from typing import Any
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..services.factory import get_ai_service
from django.shortcuts import get_object_or_404
from tasks.models import Task
from ..serializers import SmartEstimateResponseSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="smart_estimate",
    summary="Generate AI estimate for a task",
    description="Generate a smart estimate suggestion for a task based on similar tasks and historical data.",
    request=None,
    responses={
        200: OpenApiResponse(
            response=SmartEstimateResponseSerializer,
            description="Successfully generated estimate suggestion"
        ),
        400: OpenApiResponse(
            description="Invalid task ID or task not found"
        ),
        401: OpenApiResponse(
            description="Authentication required"
        ),
        500: OpenApiResponse(
            description="Internal server error during estimate generation"
        )
    },
    tags=["AI Tools"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_estimate_view(request: Request, task_id: str) -> Response:
    """
    Generate AI estimate synchronously and return the result.
    
    This endpoint analyzes the task and provides an estimate suggestion based on:
    - Similar tasks in the system
    - Historical estimation data
    - Task complexity indicators
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to generate estimate for
        
    Returns:
        JSON response with estimate suggestion data including:
        - suggested_points: Recommended estimate in points
        - confidence: Confidence score (0.0 to 1.0)
        - similar_task_ids: List of similar task IDs used
        - rationale: Human-readable explanation
    """
    # Get task or raise 404
    task = get_object_or_404(Task, id=task_id)
    
    # Get AI service and generate estimate
    ai_service = get_ai_service()
    estimate_result = ai_service.generate_estimate(task)
    
    # Log the AI tool invocation
    logger.info(f"Smart estimate completed for Task {task.id} by user {request.user.id}")
    
    # Serialize and return response
    serializer = SmartEstimateResponseSerializer(estimate_result)
    return Response(serializer.data, status=status.HTTP_200_OK)
