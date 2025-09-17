"""
Unit tests for AI Tools services using pytest.
"""
import logging
from unittest.mock import patch
import pytest
from django.contrib.auth.models import User
from tasks.models import Task, TaskActivity, ActivityType, Tag, TaskStatus
from .services import AIService

def test_generate_summary_basic_task(basic_task, users):
    """Test summary generation for a basic task with minimal activities."""
    # Create a creation activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(basic_task, users['dev'])
    
    # Verify deterministic output (account for potential signal-created activities)
    expected_parts = [
        "currently to do",
        f"assigned to {users['dev'].username}"
    ]
    
    for part in expected_parts:
        assert part in summary
def test_generate_summary_complex_task(complex_task, users):
    """Test summary generation for a task with multiple activities."""
    # Create multiple activities
    activities = [
        TaskActivity.objects.create(
            task=complex_task,
            actor=users['dev'],
            type=ActivityType.CREATED
        ),
        TaskActivity.objects.create(
            task=complex_task,
            actor=users['qa'],
            type=ActivityType.UPDATED_STATUS,
            field='status',
            before='TODO',
            after='IN_PROGRESS'
        ),
        TaskActivity.objects.create(
            task=complex_task,
            actor=users['dev'],
            type=ActivityType.UPDATED_ESTIMATE,
            field='estimate',
            before=None,
            after=5
        )
    ]
    
    summary = AIService.generate_summary(complex_task, users['dev'])
    
    # Verify deterministic output components (account for potential signal-created activities)
    assert "activities" in summary  # Don't check exact count due to signals
    assert "currently in progress" in summary
    assert f"assigned to {users['dev'].username}" in summary
    assert "5 points" in summary
    assert "tagged with backend and 'security'" in summary
    assert "Work is actively in progress" in summary
def test_generate_summary_completed_task(completed_task, users):
    """Test summary generation for a completed task."""
    # Create activities for completed task
    TaskActivity.objects.create(
        task=completed_task,
        actor=users['qa'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(completed_task, users['qa'])
    
    # Verify completed task specific content
    assert "currently done" in summary
    assert "completed successfully" in summary
    assert "8 points" in summary
    assert "frontend and 'testing'" in summary  # Multiple tags
def test_generate_summary_deterministic(basic_task, users):
    """Test that summary generation is deterministic."""
    # Create activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    # Generate summary multiple times
    summary1 = AIService.generate_summary(basic_task, users['dev'])
    summary2 = AIService.generate_summary(basic_task, users['dev'])
    summary3 = AIService.generate_summary(basic_task, users['dev'])
    
    # All summaries should be identical
    assert summary1 == summary2
    assert summary2 == summary3
def test_generate_rewrite_basic_task(basic_task, users):
    """Test rewrite generation for a basic task."""
    rewrite = AIService.generate_rewrite(basic_task, users['dev'])
    
    # Verify structure
    assert 'title' in rewrite
    assert 'user_story' in rewrite
    
    # Verify title preservation
    assert rewrite['title'] == basic_task.title
    
    # Verify user story format
    user_story = rewrite['user_story']
    assert "As a developer" in user_story  # Based on username 'testdev'
    assert "I want to" in user_story
    assert "so that" in user_story
    assert "Acceptance Criteria:" in user_story
    assert "WHEN" in user_story
    assert "THEN" in user_story
    assert "SHALL" in user_story
def test_generate_rewrite_bug_fix_task(complex_task, users):
    """Test rewrite generation for a bug fix task."""
    rewrite = AIService.generate_rewrite(complex_task, users['dev'])
    
    user_story = rewrite['user_story']
    
    # Should detect bug fix pattern
    assert "resolve the issue" in user_story
    assert "system is more secure" in user_story  # Auth-related benefit
    assert "5 points of effort" in user_story  # Estimate-based criteria
    assert "backend changes" in user_story  # Tag-based criteria
def test_generate_rewrite_ui_task(completed_task, users):
    """Test rewrite generation for a UI task."""
    rewrite = AIService.generate_rewrite(completed_task, users['qa'])
    
    user_story = rewrite['user_story']
    
    # Should detect UI improvement pattern
    assert "As a QA engineer" in user_story  # Based on username 'testqa'
    assert "see the improvements" in user_story  # Update pattern
    assert "user experience is improved" in user_story  # UI benefit
    assert "frontend changes" in user_story  # Frontend tag
    assert "responsive and accessible" in user_story  # Frontend criteria
def test_generate_rewrite_deterministic(basic_task, users):
    """Test that rewrite generation is deterministic."""
    # Generate rewrite multiple times
    rewrite1 = AIService.generate_rewrite(basic_task, users['dev'])
    rewrite2 = AIService.generate_rewrite(basic_task, users['dev'])
    rewrite3 = AIService.generate_rewrite(basic_task, users['dev'])
    
    # All rewrites should be identical
    assert rewrite1 == rewrite2
    assert rewrite2 == rewrite3
def test_generate_rewrite_role_detection(basic_task, users):
    """Test user role detection based on username."""
    # Test developer role
    dev_rewrite = AIService.generate_rewrite(basic_task, users['dev'])
    assert "As a developer" in dev_rewrite['user_story']
    
    # Test QA role
    qa_rewrite = AIService.generate_rewrite(basic_task, users['qa'])
    assert "As a QA engineer" in qa_rewrite['user_story']
    
    # Test PM role
    pm_rewrite = AIService.generate_rewrite(basic_task, users['pm'])
    assert "As a project manager" in pm_rewrite['user_story']
@patch('ai_tools.services.logger')
def test_ai_invocation_logging(mock_logger, basic_task, users):
    """Test that AI tool invocations are properly logged."""
    # Generate summary (should log invocation)
    AIService.generate_summary(basic_task, users['dev'])
    
    # Verify logging was called
    mock_logger.info.assert_called()
    
    # Get the logged call
    call_args = mock_logger.info.call_args
    assert call_args[0][0] == "AI tool invocation"
    
    # Verify logged data structure
    extra_data = call_args[1]['extra']
    assert extra_data['tool_type'] == 'smart_summary'
    assert extra_data['task_id'] == str(basic_task.id)
    assert extra_data['user_id'] == users['dev'].id
    assert 'response_time_ms' in extra_data
    assert isinstance(extra_data['response_time_ms'], int)
@patch('ai_tools.services.logger')
def test_rewrite_invocation_logging(mock_logger, basic_task, users):
    """Test that rewrite tool invocations are properly logged."""
    # Generate rewrite (should log invocation)
    AIService.generate_rewrite(basic_task, users['dev'])
    
    # Verify logging was called
    mock_logger.info.assert_called()
    
    # Get the logged call
    call_args = mock_logger.info.call_args
    extra_data = call_args[1]['extra']
    assert extra_data['tool_type'] == 'smart_rewrite'
def test_summary_error_handling(users):
    """Test error handling in summary generation."""
    # Create a task with no activities to potentially cause issues
    empty_task = Task.objects.create(
        title='Empty task',
        status=TaskStatus.TODO
    )
    
    # Should not raise exception
    summary = AIService.generate_summary(empty_task, users['dev'])
    assert isinstance(summary, str)
    assert len(summary) > 0
def test_rewrite_error_handling(minimal_task, users):
    """Test error handling in rewrite generation."""
    # Should not raise exception
    rewrite = AIService.generate_rewrite(minimal_task, users['dev'])
    assert isinstance(rewrite, dict)
    assert 'title' in rewrite
    assert 'user_story' in rewrite
def test_summary_without_user(basic_task, users):
    """Test summary generation without user (for logging)."""
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    # Should work without user
    summary = AIService.generate_summary(basic_task)
    assert isinstance(summary, str)
    assert len(summary) > 0
def test_rewrite_without_user(basic_task):
    """Test rewrite generation without user (for logging)."""
    # Should work without user
    rewrite = AIService.generate_rewrite(basic_task)
    assert isinstance(rewrite, dict)
    assert 'title' in rewrite
    assert 'user_story' in rewrite
def test_summary_blocked_task_status(blocked_task, users):
    """Test summary generation for blocked task."""
    TaskActivity.objects.create(
        task=blocked_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(blocked_task, users['dev'])
    assert "currently blocked" in summary
    assert "may need attention" in summary
def test_summary_multiple_tags(multi_tag_task, users):
    """Test summary generation with multiple tags."""
    TaskActivity.objects.create(
        task=multi_tag_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(multi_tag_task, users['dev'])
    # Should handle multiple tags properly (tags are ordered alphabetically)
    assert "backend, frontend and 'testing'" in summary
def test_rewrite_task_patterns(users):
    """Test rewrite generation for different task title patterns."""
    # Test create pattern
    create_task = Task.objects.create(
        title='Create new dashboard',
        status=TaskStatus.TODO
    )
    create_rewrite = AIService.generate_rewrite(create_task, users['dev'])
    assert "have the functionality" in create_rewrite['user_story']
    
    # Test update pattern
    update_task = Task.objects.create(
        title='Update user profile page',
        status=TaskStatus.TODO
    )
    update_rewrite = AIService.generate_rewrite(update_task, users['dev'])
    assert "see the improvements" in update_rewrite['user_story']
    
    # Test performance pattern
    perf_task = Task.objects.create(
        title='Optimize database queries',
        status=TaskStatus.TODO
    )
    perf_rewrite = AIService.generate_rewrite(perf_task, users['dev'])
    assert "system performs better" in perf_rewrite['user_story']


# Additional pytest-specific tests using fixtures

def test_summary_with_task_activities_fixture(task_with_activities, users):
    """Test summary generation using the task_with_activities fixture."""
    summary = AIService.generate_summary(task_with_activities, users['dev'])
    
    # Should reflect multiple activities
    assert "activities" in summary
    assert "currently to do" in summary  # Final status after activities
    assert f"assigned to {users['dev'].username}" in summary


@pytest.mark.parametrize("task_key,expected_status", [
    ('basic', 'to do'),
    ('complex', 'in progress'),
    ('completed', 'done'),
    ('blocked', 'blocked')
])
def test_summary_status_variations(sample_tasks, users, task_key, expected_status):
    """Test summary generation for different task statuses using parametrize."""
    task = sample_tasks[task_key]
    
    # Create a basic activity for each task
    TaskActivity.objects.create(
        task=task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(task, users['dev'])
    assert f"currently {expected_status}" in summary


def test_rewrite_with_different_users(basic_task, users):
    """Test rewrite generation with different user types using fixture."""
    # Test each user type
    for user_key, user in users.items():
        rewrite = AIService.generate_rewrite(basic_task, user)
        
        # Verify user story contains appropriate role
        user_story = rewrite['user_story']
        if user_key == 'dev':
            assert "As a developer" in user_story
        elif user_key == 'qa':
            assert "As a QA engineer" in user_story
        elif user_key == 'pm':
            assert "As a project manager" in user_story
        else:
            assert "As a user" in user_story


def test_summary_with_similar_tasks_context(similar_tasks_set, users):
    """Test summary generation in context of similar tasks."""
    # Create a target task similar to the fixture tasks
    target_task = Task.objects.create(
        title='Basic test implementation',
        description='A simple task for testing similarity',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm']
    )
    
    TaskActivity.objects.create(
        task=target_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(target_task, users['dev'])
    
    # Should generate summary regardless of similar tasks existing
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert "currently to do" in summary


def test_rewrite_with_estimate_tasks(tasks_for_estimate_calculation, users):
    """Test rewrite generation when estimate calculation tasks exist."""
    # Create a new task that could be similar to estimate calculation tasks
    new_task = Task.objects.create(
        title='Another backend task',
        description='Similar to estimate calculation tasks',
        status=TaskStatus.TODO,
        assignee=users['dev'],
        reporter=users['pm']
    )
    
    rewrite = AIService.generate_rewrite(new_task, users['dev'])
    
    # Should generate rewrite successfully
    assert 'title' in rewrite
    assert 'user_story' in rewrite
    assert "As a developer" in rewrite['user_story']


@pytest.mark.parametrize("tag_count", [0, 1, 2, 3])
def test_summary_tag_handling(users, tags, tag_count):
    """Test summary generation with varying numbers of tags."""
    task = Task.objects.create(
        title=f'Task with {tag_count} tags',
        status=TaskStatus.TODO,
        assignee=users['dev']
    )
    
    # Add specified number of tags
    tag_list = list(tags.values())[:tag_count]
    for tag in tag_list:
        task.tags.add(tag)
    
    TaskActivity.objects.create(
        task=task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    summary = AIService.generate_summary(task, users['dev'])
    
    if tag_count == 0:
        # No tag information should be present
        assert "tagged with" not in summary
    elif tag_count == 1:
        # Single tag format
        assert f"tagged with '{tag_list[0].name}'" in summary
    else:
        # Multiple tags format
        assert "tagged with" in summary
        assert "and" in summary


def test_ai_service_error_resilience(users):
    """Test AI service handles edge cases gracefully."""
    # Test with task that has no assignee or reporter
    orphan_task = Task.objects.create(
        title='Orphan task',
        status=TaskStatus.TODO
    )
    
    # Should not raise exceptions
    summary = AIService.generate_summary(orphan_task, users['dev'])
    rewrite = AIService.generate_rewrite(orphan_task, users['dev'])
    
    assert isinstance(summary, str)
    assert isinstance(rewrite, dict)
    assert len(summary) > 0
    assert 'title' in rewrite
    assert 'user_story' in rewrite


def test_logging_with_different_tools(basic_task, users):
    """Test that different AI tools log with correct tool_type."""
    with patch('ai_tools.services.logger') as mock_logger:
        # Test summary logging
        AIService.generate_summary(basic_task, users['dev'])
        summary_call = mock_logger.info.call_args
        assert summary_call[1]['extra']['tool_type'] == 'smart_summary'
        
        # Reset mock
        mock_logger.reset_mock()
        
        # Test rewrite logging
        AIService.generate_rewrite(basic_task, users['dev'])
        rewrite_call = mock_logger.info.call_args
        assert rewrite_call[1]['extra']['tool_type'] == 'smart_rewrite'


def test_deterministic_output_across_fixtures(sample_tasks, users):
    """Test that AI outputs are deterministic across different fixture tasks."""
    for task_name, task in sample_tasks.items():
        # Generate outputs multiple times
        summary1 = AIService.generate_summary(task, users['dev'])
        summary2 = AIService.generate_summary(task, users['dev'])
        
        rewrite1 = AIService.generate_rewrite(task, users['dev'])
        rewrite2 = AIService.generate_rewrite(task, users['dev'])
        
        # Should be identical
        assert summary1 == summary2, f"Summary not deterministic for {task_name}"
        assert rewrite1 == rewrite2, f"Rewrite not deterministic for {task_name}"