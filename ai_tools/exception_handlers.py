"""
Custom exception handlers for AI tools views.
"""
import logging
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .serializers import ErrorResponseSerializer

logger = logging.getLogger(__name__)


def ai_tools_exception_handler(exc, context):
    """
    Custom exception handler for AI tools views.
    
    This handler provides consistent error responses across all AI tools views
    and maps different exception types to appropriate HTTP status codes.
    
    Args:
        exc: The exception that was raised
        context: The context in which the exception occurred
        
    Returns:
        Response: A standardized error response
    """
    # Handle ValidationError (invalid UUID format, etc.)
    if isinstance(exc, ValidationError):
        error_serializer = ErrorResponseSerializer({'error': str(exc)})
        return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    # Handle Http404 (task not found)
    if isinstance(exc, Http404):
        error_serializer = ErrorResponseSerializer({'error': 'Task not found.'})
        return Response(error_serializer.data, status=status.HTTP_404_NOT_FOUND)
    
    # Handle all other exceptions
    logger.error(f"Unexpected error in AI tools: {str(exc)}", exc_info=True)
    error_serializer = ErrorResponseSerializer({
        'error': 'An unexpected error occurred. Please try again later.'
    })
    return Response(error_serializer.data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
