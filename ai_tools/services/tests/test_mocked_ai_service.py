"""
Tests for MockedAIService class.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_tools.services.mocked_ai_service import MockedAIService
from tasks.models import Task, ActivityType


@pytest.fixture
def ai_service():
    """Create a MockedAIService instance for testing."""
    return MockedAIService()


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
    task.tags = []  # JSONField for tags
    task.get_status_display.return_value = "To Do"
    return task


@pytest.fixture
def mock_task_with_assignee():
    """Create a mock Task instance with assignee for testing."""
    task = Mock(spec=Task)
    task.id = "test-task-id"
    task.title = "Test Task"
    task.description = "Test Description"
    task.status = "TODO"
    task.estimate = 5
    task.tags = []
    task.get_status_display.return_value = "To Do"
    
    assignee = Mock()
    assignee.username = "testuser"
    task.assignee = assignee
    return task


@pytest.fixture
def mock_task_with_tags():
    """Create a mock Task instance with tags for testing."""
    task = Mock(spec=Task)
    task.id = "test-task-id"
    task.title = "Test Task"
    task.description = "Test Description"
    task.status = "TODO"
    task.estimate = 5
    task.assignee = None
    task.tags = ["frontend", "ui", "react"]  # JSONField for tags
    task.get_status_display.return_value = "To Do"
    return task


@pytest.fixture
def mock_task_with_estimate():
    """Create a mock Task instance with estimate for testing."""
    task = Mock(spec=Task)
    task.id = "test-task-id"
    task.title = "Test Task"
    task.description = "Test Description"
    task.status = "TODO"
    task.estimate = 8
    task.assignee = None
    task.tags = []
    task.get_status_display.return_value = "To Do"
    return task

def test_generate_summary_success(ai_service, mock_task):
    """Test successful summary generation."""
    # Mock activities
    mock_activities = Mock()
    mock_activities.count.return_value = 2
    mock_activities.all.return_value.order_by.return_value = mock_activities
    mock_task.activities = mock_activities

    result = ai_service.generate_summary(mock_task)
    
    assert isinstance(result, str)
    assert len(result) > 0
    assert "task" in result.lower()  # The summary should contain "task"


def test_generate_summary_with_assignee(ai_service, mock_task_with_assignee):
    """Test summary generation with assignee."""
    mock_activities = Mock()
    mock_activities.count.return_value = 1
    mock_activities.all.return_value.order_by.return_value = mock_activities
    mock_task_with_assignee.activities = mock_activities

    result = ai_service.generate_summary(mock_task_with_assignee)
    
    assert "testuser" in result


def test_generate_summary_with_estimate(ai_service, mock_task_with_estimate):
    """Test summary generation with estimate."""
    mock_activities = Mock()
    mock_activities.count.return_value = 1
    mock_activities.all.return_value.order_by.return_value = mock_activities
    mock_task_with_estimate.activities = mock_activities

    result = ai_service.generate_summary(mock_task_with_estimate)
    
    assert "8 points" in result


def test_generate_summary_with_tags(ai_service, mock_task_with_tags):
    """Test summary generation with tags (JSONField)."""
    mock_activities = Mock()
    mock_activities.count.return_value = 1
    mock_activities.all.return_value.order_by.return_value = mock_activities
    mock_task_with_tags.activities = mock_activities

    result = ai_service.generate_summary(mock_task_with_tags)
    
    assert "frontend" in result and "ui" in result


def test_generate_summary_exception_handling(ai_service, mock_task):
    """Test summary generation with exception handling."""
    # Mock activities to raise an exception
    mock_activities = Mock()
    mock_activities.all.side_effect = Exception("Database error")
    mock_task.activities = mock_activities

    result = ai_service.generate_summary(mock_task)
    
    assert result == "Unable to generate summary at this time."

def test_generate_rewrite_success(ai_service, mock_task):
    """Test successful rewrite generation."""
    result = ai_service.generate_rewrite(mock_task)
    
    assert isinstance(result, dict)
    assert 'title' in result
    assert 'user_story' in result
    assert result['title'] == "Test Task"
    assert "As a" in result['user_story']
    assert "I want to" in result['user_story']
    assert "so that" in result['user_story']


@pytest.mark.parametrize("username,expected_role", [
    ("developer", "developer"),
    ("pm_manager", "project manager"),
    ("qa_tester", "QA engineer"),
    ("other_user", "user"),
])
def test_generate_rewrite_with_assignee(ai_service, mock_task, username, expected_role):
    """Test rewrite generation with different assignee types."""
    mock_assignee = Mock()
    mock_assignee.username = username
    mock_task.assignee = mock_assignee

    result = ai_service.generate_rewrite(mock_task)
    
    assert expected_role in result['user_story']


@pytest.mark.parametrize("title,expected_phrase", [
    ("Fix login bug", "resolve the issue"),
    ("Add user authentication", "have the functionality"),
    ("Update user interface", "see the improvements"),
    ("Create new feature", "have the functionality"),
])
def test_generate_rewrite_with_different_titles(ai_service, mock_task, title, expected_phrase):
    """Test rewrite generation with different title types."""
    mock_task.title = title
    result = ai_service.generate_rewrite(mock_task)
    
    assert expected_phrase in result['user_story']


def test_generate_rewrite_exception_handling(ai_service, mock_task):
    """Test rewrite generation with exception handling."""
    # Mock task to raise an exception
    mock_task.title = Mock(side_effect=Exception("Error"))

    result = ai_service.generate_rewrite(mock_task)
    
    assert result['title'] == mock_task.title
    assert "Unable to generate enhanced description" in result['user_story']

@patch('ai_tools.services.mocked_ai_service.Task')
def test_generate_estimate_success(mock_task_model, ai_service, mock_task):
    """Test successful estimate generation."""
    # Mock similar tasks
    mock_similar_task1 = Mock()
    mock_similar_task1.id = "similar-1"
    mock_similar_task1.estimate = 3
    mock_similar_task1.updated_at.timestamp.return_value = 1000
    
    mock_similar_task2 = Mock()
    mock_similar_task2.id = "similar-2"
    mock_similar_task2.estimate = 5
    mock_similar_task2.updated_at.timestamp.return_value = 2000
    
    # Mock the queryset
    mock_queryset = Mock()
    mock_queryset.exclude.return_value.select_related.return_value = [mock_similar_task1, mock_similar_task2]
    mock_task_model.objects = mock_queryset

    result = ai_service.generate_estimate(mock_task)
    
    assert isinstance(result, dict)
    assert 'suggested_points' in result
    assert 'confidence' in result
    assert 'similar_task_ids' in result
    assert 'rationale' in result
    assert isinstance(result['suggested_points'], int)
    assert 0.0 <= result['confidence'] <= 1.0
    assert isinstance(result['similar_task_ids'], list)


@patch('ai_tools.services.mocked_ai_service.Task')
def test_generate_estimate_no_similar_tasks(mock_task_model, ai_service, mock_task):
    """Test estimate generation with no similar tasks."""
    # Mock empty queryset
    mock_queryset = Mock()
    mock_queryset.exclude.return_value.select_related.return_value = []
    mock_task_model.objects = mock_queryset

    result = ai_service.generate_estimate(mock_task)
    
    assert result['suggested_points'] == 3
    assert result['confidence'] == 0.40
    assert result['similar_task_ids'] == []
    assert "No similar tasks found" in result['rationale']


@patch('ai_tools.services.mocked_ai_service.Task')
def test_generate_estimate_exception_handling(mock_task_model, ai_service, mock_task):
    """Test estimate generation with exception handling."""
    # Mock Task.objects to raise an exception
    mock_task_model.objects.exclude.side_effect = Exception("Database error")

    result = ai_service.generate_estimate(mock_task)
    
    assert result['suggested_points'] == 3
    assert result['confidence'] == 0.40
    assert result['similar_task_ids'] == []
    assert "Unable to generate estimate" in result['rationale']

@patch('ai_tools.services.mocked_ai_service.Task')
def test_find_similar_tasks_same_assignee(mock_task_model, ai_service, mock_task):
    """Test finding similar tasks with same assignee."""
    # Mock assignee
    mock_assignee = Mock()
    mock_assignee.id = 1
    mock_task.assignee = mock_assignee
    
    # Mock similar task with same assignee
    mock_similar_task = Mock()
    mock_similar_task.id = "similar-1"
    mock_similar_task.assignee = mock_assignee
    mock_similar_task.tags = []
    mock_similar_task.title = "Similar Task"
    mock_similar_task.description = "Similar Description"
    mock_similar_task.updated_at.timestamp.return_value = 1000
    
    mock_queryset = Mock()
    mock_queryset.exclude.return_value.select_related.return_value = [mock_similar_task]
    mock_task_model.objects = mock_queryset
    
    result = ai_service._find_similar_tasks(mock_task, limit=5)
    
    assert len(result) == 1
    assert result[0].id == "similar-1"


@pytest.mark.parametrize("estimates,similar_count,expected_min_confidence", [
    ([3, 5, 4, 6, 4], 10, 0.5),
    ([5], 5, 0.7),  # Single estimate should have reasonable confidence
    ([], 0, 0.40),
])
def test_calculate_estimate_confidence(ai_service, estimates, similar_count, expected_min_confidence):
    """Test confidence calculation with various scenarios."""
    confidence = ai_service._calculate_estimate_confidence(estimates, similar_count)
    
    assert 0.0 <= confidence <= 1.0
    if expected_min_confidence > 0:
        assert confidence >= expected_min_confidence
    else:
        assert confidence == expected_min_confidence


@pytest.mark.parametrize("count,points,confidence,expected_phrases", [
    (3, 5, 0.8, ["3 similar tasks", "5 points", "high confidence"]),
    (1, 3, 0.6, ["1 similar task", "3 points", "medium confidence"]),
    (0, 0, 0.0, ["No similar tasks found"]),
])
def test_generate_estimate_rationale(ai_service, count, points, confidence, expected_phrases):
    """Test rationale generation with various scenarios."""
    rationale = ai_service._generate_estimate_rationale(count, points, confidence)
    
    for phrase in expected_phrases:
        assert phrase in rationale


def test_generate_deterministic_summary(ai_service, mock_task):
    """Test deterministic summary generation."""
    mock_activities = Mock()
    mock_activities.count.return_value = 2
    
    result = ai_service._generate_deterministic_summary(
        mock_task, mock_activities, 2
    )
    
    assert isinstance(result, str)
    assert "2 activities" in result
    assert "to do" in result.lower()  # Case insensitive check


def test_generate_deterministic_rewrite(ai_service, mock_task):
    """Test deterministic rewrite generation."""
    result = ai_service._generate_deterministic_rewrite(mock_task)
    
    assert isinstance(result, dict)
    assert 'title' in result
    assert 'user_story' in result
    assert result['title'] == "Test Task"
    assert "Acceptance Criteria:" in result['user_story']
