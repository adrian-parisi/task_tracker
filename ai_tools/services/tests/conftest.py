"""
Shared test fixtures for AI services tests.
"""
import pytest
from unittest.mock import Mock
from tasks.models import Task


@pytest.fixture
def mock_task():
    """Create a mock Task instance for testing."""
    task = Mock(spec=Task)
    task.id = "test-task-id"
    task.title = "Test Task"
    task.description = "Test Description"
    task.status = "TODO"
    task.estimate = 5
    task.assignee = None
    task.reporter = None
    task.project = None
    task.tags = []  # JSONField for tags
    task.created_at = None
    task.updated_at = None
    task.get_status_display.return_value = "To Do"
    
    # Mock activities
    task.activities = Mock()
    task.activities.all.return_value.order_by.return_value = Mock()
    task.activities.count.return_value = 1
    
    return task


@pytest.fixture
def mock_task_with_assignee():
    """Create a mock Task instance with assignee for testing."""
    task = mock_task()
    
    assignee = Mock()
    assignee.id = 1
    assignee.username = "testuser"
    assignee.first_name = "Test"
    assignee.last_name = "User"
    assignee.display_name = "Test User"
    
    task.assignee = assignee
    return task


@pytest.fixture
def mock_task_with_tags():
    """Create a mock Task instance with tags for testing."""
    task = mock_task()
    task.tags = ["frontend", "ui", "react"]
    return task


@pytest.fixture
def mock_task_with_estimate():
    """Create a mock Task instance with estimate for testing."""
    task = mock_task()
    task.estimate = 8
    return task


@pytest.fixture
def mock_similar_tasks():
    """Create mock similar tasks for testing."""
    tasks = []
    
    for i in range(3):
        task = Mock(spec=Task)
        task.id = f"similar-task-{i}"
        task.title = f"Similar Task {i}"
        task.description = f"Similar Description {i}"
        task.estimate = 3 + i
        task.assignee = None
        task.tags = []
        task.updated_at.timestamp.return_value = 1000 + i
        tasks.append(task)
    
    return tasks


@pytest.fixture
def ai_service():
    """Create an AIService instance for testing."""
    from ai_tools.services.ai_service import AIService
    return AIService()


@pytest.fixture
def mocked_ai_service():
    """Create a MockedAIService instance for testing."""
    from ai_tools.services.mocked_ai_service import MockedAIService
    return MockedAIService()
