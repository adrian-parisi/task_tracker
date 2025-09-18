from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.projects import ProjectViewSet
from .views.tasks import TaskViewSet
from .views.tags import TagViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
]