"""
Custom exception handlers for Django REST Framework.
Provides standardized error response format across all API endpoints.
"""
from typing import Any, Dict, List
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc: Exception, context: Dict[str, Any]) -> Response | None:
    """
    Custom exception handler that returns standardized error responses.
    
    Handles:
    - DRF validation errors (400)
    - Django model validation errors (400)
    - Database integrity errors (400)
    - Not found errors (404)
    - Authentication errors (401)
    - Permission errors (403)
    - Method not allowed (405)
    - Internal server errors (500)
    
    Returns standardized format:
    {
        "detail": "Human readable error message",
        "errors": {
            "field_name": ["Field specific error messages"],
            "non_field_errors": ["General error messages"]
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Handle DRF exceptions with existing response
        custom_response_data = _format_drf_error_response(response.data, exc)
        response.data = custom_response_data
        return response
    
    # Handle Django exceptions that DRF doesn't handle by default
    if isinstance(exc, DjangoValidationError):
        return _handle_django_validation_error(exc)
    
    if isinstance(exc, IntegrityError):
        return _handle_integrity_error(exc)
    
    if isinstance(exc, Http404):
        return _handle_not_found_error(exc)
    
    # Handle unexpected exceptions
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return Response(
        {
            'detail': 'An unexpected error occurred. Please try again later.',
            'errors': {'server': ['Internal server error']}
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def _format_drf_error_response(error_data: Any, exc: Exception) -> Dict[str, Any]:
    """Format DRF error response to standardized format."""
    # Determine appropriate detail message based on exception type
    detail_message = _get_detail_message(exc)
    
    # Format errors dictionary
    errors = {}
    
    if isinstance(error_data, dict):
        for field, messages in error_data.items():
            if field == 'detail':
                # Skip detail field, we'll set our own
                continue
            elif field == 'non_field_errors':
                errors['non_field_errors'] = _ensure_list(messages)
            else:
                errors[field] = _ensure_list(messages)
    elif isinstance(error_data, list):
        errors['non_field_errors'] = _ensure_list(error_data)
    else:
        errors['non_field_errors'] = [str(error_data)]
    
    return {
        'detail': detail_message,
        'errors': errors
    }


def _handle_django_validation_error(exc: DjangoValidationError) -> Response:
    """Handle Django model validation errors."""
    errors = {}
    
    if hasattr(exc, 'error_dict'):
        # Field-specific validation errors
        for field, error_list in exc.error_dict.items():
            errors[field] = [str(error) for error in error_list]
    elif hasattr(exc, 'error_list'):
        # Non-field validation errors
        errors['non_field_errors'] = [str(error) for error in exc.error_list]
    else:
        errors['non_field_errors'] = [str(exc)]
    
    return Response(
        {
            'detail': 'Validation failed.',
            'errors': errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def _handle_integrity_error(exc: IntegrityError) -> Response:
    """Handle database integrity constraint violations."""
    error_message = str(exc).lower()
    
    # Check for specific constraint violations
    if 'unique' in error_message:
        if 'tag_name' in error_message:
            return Response(
                {
                    'detail': 'A tag with this name already exists.',
                    'errors': {'name': ['A tag with this name already exists (case-insensitive).']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {
                    'detail': 'This value must be unique.',
                    'errors': {'non_field_errors': ['A record with these values already exists.']}
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Generic integrity error
    logger.error(f"Database integrity error: {exc}")
    return Response(
        {
            'detail': 'Data integrity constraint violation.',
            'errors': {'non_field_errors': ['The operation violates database constraints.']}
        },
        status=status.HTTP_400_BAD_REQUEST
    )


def _handle_not_found_error(exc: Http404) -> Response:
    """Handle Http404 exceptions."""
    return Response(
        {
            'detail': 'Resource not found.',
            'errors': {'resource': ['The requested resource does not exist.']}
        },
        status=status.HTTP_404_NOT_FOUND
    )


def _get_detail_message(exc: Exception) -> str:
    """Get appropriate detail message based on exception type."""
    from rest_framework.exceptions import (
        ValidationError, NotFound, PermissionDenied, 
        AuthenticationFailed, MethodNotAllowed, NotAuthenticated
    )
    from django.http import Http404
    
    if isinstance(exc, ValidationError):
        return 'Validation failed.'
    elif isinstance(exc, (NotFound, Http404)):
        return 'Resource not found.'
    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return 'Authentication required.'
    elif isinstance(exc, PermissionDenied):
        return 'Permission denied.'
    elif isinstance(exc, MethodNotAllowed):
        return 'Method not allowed.'
    else:
        return 'An error occurred.'


def _ensure_list(value: Any) -> List[str]:
    """Ensure value is a list for consistent error format."""
    if isinstance(value, list):
        return [str(item) for item in value]
    else:
        return [str(value)]