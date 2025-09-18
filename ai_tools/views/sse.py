"""
Server-Sent Events views for AI operations.
"""
import json
import time
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from ..models import AIOperation


@login_required
def test_sse(request, operation_id):
    """Test endpoint to debug SSE issues."""
    try:
        operation = AIOperation.objects.get(id=operation_id, user=request.user)
        return JsonResponse({
            'status': 'success',
            'operation_id': str(operation.id),
            'operation_status': operation.status,
            'user_id': request.user.id
        })
    except AIOperation.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Operation not found',
            'operation_id': operation_id,
            'user_id': request.user.id
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e),
            'operation_id': operation_id,
            'user_id': request.user.id
        })


@login_required
def ai_operation_sse(request, operation_id):
    """Stream AI operation updates via Server-Sent Events."""
    
    try:
        operation = AIOperation.objects.get(id=operation_id, user=request.user)
        
        # For now, just return the current status as JSON
        return JsonResponse({
            'status': operation.status,
            'result': operation.result,
            'error': operation.error_message
        })
    except AIOperation.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'error': 'Operation not found'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'error': str(e)
        })
