"""
Celery async tasks for AI operations.
"""
from celery import shared_task
from django.utils import timezone
from .models import AIOperation
from .services import get_ai_service


@shared_task
def process_ai_async_task(operation_id: str):
    """Process AI operation asynchronously."""
    try:
        operation = AIOperation.objects.get(id=operation_id)
        operation.status = 'PROCESSING'
        operation.save()
        
        # Get AI service and process based on operation type
        ai_service = get_ai_service()
        
        if operation.operation_type == 'SUMMARY':
            result = ai_service.generate_summary(operation.task)
        elif operation.operation_type == 'ESTIMATE':
            result = ai_service.generate_estimate(operation.task)
        elif operation.operation_type == 'REWRITE':
            result = ai_service.generate_rewrite(operation.task)
        else:
            raise ValueError(f"Unknown operation type: {operation.operation_type}")
        
        # Update operation with result
        operation.status = 'COMPLETED'
        operation.result = result
        operation.completed_at = timezone.now()
        operation.save()
        
        return f"AsyncTask {operation_id} completed successfully"
        
    except Exception as exc:
        # Update operation with error
        operation = AIOperation.objects.get(id=operation_id)
        operation.status = 'FAILED'
        operation.error_message = str(exc)
        operation.save()
        
        return f"AsyncTask {operation_id} failed: {str(exc)}"
