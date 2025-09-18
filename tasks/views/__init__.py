# Views package for tasks app
from .projects import ProjectViewSet
from .tasks import TaskViewSet

__all__ = [
    'ProjectViewSet',
    'TaskViewSet'
]