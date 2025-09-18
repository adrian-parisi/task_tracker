"""
Unit tests for AI Tools services using pytest.
"""
import logging
from unittest.mock import patch
import pytest
from accounts.models import CustomUser
from tasks.models import Task, TaskActivity, ActivityType, TaskStatus
from ai_tools.services import MockedAIService

@pytest.mark.django_db
def test_generate_summary_basic_task(basic_task, users):
    """Test summary generation for a basic task with minimal activities."""
    # Create a creation activity
    TaskActivity.objects.create(
        task=basic_task,
        actor=users['dev'],
        type=ActivityType.CREATED
    )
    
    ai_service = MockedAIService()
    summary = ai_service.generate_summary(basic_task)
    
    # Verify deterministic output (account for potential signal-created activities)
    expected_parts = [
        "currently to do",
        f"assigned to {users['dev'].username}"
    ]
    
    for part in expected_parts:
        assert part in summary

# ... rest of the test methods would continue here