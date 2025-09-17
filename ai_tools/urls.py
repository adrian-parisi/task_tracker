from django.urls import path
from .views import smart_summary_view, smart_estimate_view, smart_rewrite_view

urlpatterns = [
    path('tasks/<uuid:task_id>/smart-summary/', smart_summary_view, name='smart-summary'),
    path('tasks/<uuid:task_id>/smart-estimate/', smart_estimate_view, name='smart-estimate'),
    path('tasks/<uuid:task_id>/smart-rewrite/', smart_rewrite_view, name='smart-rewrite'),
]