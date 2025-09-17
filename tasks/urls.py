from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TaskViewSet, TagViewSet
from .auth_views import LoginView, logout_view, current_user_view, csrf_token_view

router = DefaultRouter()
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/logout/', logout_view, name='logout'),
    path('auth/user/', current_user_view, name='current_user'),
    path('auth/csrf/', csrf_token_view, name='csrf_token'),
]