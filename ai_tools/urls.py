from django.urls import path
from .views import smart_summary_view, smart_estimate_view, smart_rewrite_view
from .views.sse import ai_operation_sse, test_sse

urlpatterns = [
    path('tasks/<uuid:task_id>/smart-summary/', smart_summary_view, name='smart-summary'),
    path('tasks/<uuid:task_id>/smart-estimate/', smart_estimate_view, name='smart-estimate'),
    path('tasks/<uuid:task_id>/smart-rewrite/', smart_rewrite_view, name='smart-rewrite'),
    path('ai-operations/<uuid:operation_id>/stream/', ai_operation_sse, name='ai-operation-sse'),
    path('ai-operations/<uuid:operation_id>/test/', test_sse, name='test-sse'),
]