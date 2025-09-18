from typing import Any
import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from drf_spectacular.utils import extend_schema, OpenApiResponse
from ..models import AIOperation
from ..tasks import process_ai_async_task
from django.shortcuts import get_object_or_404
from tasks.models import Task
from ..serializers import AIOperationResponseSerializer, ErrorResponseSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    operation_id="smart_summary",
    summary="Generate AI summary for a task (async)",
    description="Start an asynchronous AI summary generation process for a task. Use the returned operation_id to track progress via Server-Sent Events.",
    request=None,
    responses={
        202: OpenApiResponse(
            response=AIOperationResponseSerializer,
            description="Successfully started summary generation process"
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
            description="Internal server error during summary generation setup"
        )
    },
    tags=["AI Tools"]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def smart_summary_view(request: Request, task_id: str) -> Response:
    """
    Start AI summary generation and return operation ID.
    
    This endpoint initiates an asynchronous process to generate a comprehensive
    summary of a task based on its activities, status, and metadata. The process
    runs in the background and results are delivered via Server-Sent Events.
    
    The summary includes:
    - Task progression narrative
    - Status-specific insights
    - Assignee and estimate information
    - Tag-based context
    - Activity-based timeline
    
    Args:
        request: HTTP request object
        task_id: UUID of the task to generate summary for
        
    Returns:
        JSON response with:
        - operation_id: Unique identifier for tracking the operation
        - status: Current status of the operation (initially 'pending')
        - sse_url: Server-Sent Events URL for real-time updates
        
    Note:
        Use the sse_url to connect to Server-Sent Events for real-time updates.
        The operation will send 'completed' or 'failed' status updates with results.
    """
    # Get task or raise 404
    task = get_object_or_404(Task, id=task_id)
    
    # Create AI operation record
    operation = AIOperation.objects.create(
        task=task,
        operation_type='SUMMARY',
        status='PENDING',
        user=request.user
    )
    
    # Queue async task
    process_ai_async_task.delay(str(operation.id))
    
    # Log the AI tool invocation
    logger.info(f"Smart summary async task {operation.id} started for Task {task.id} by user {request.user.id}")
    
    # Serialize and return response
    response_data = {
        'operation_id': str(operation.id),
        'status': 'pending',
        'sse_url': f'/api/ai-operations/{operation.id}/stream/'
    }
    serializer = AIOperationResponseSerializer(response_data)
    return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
