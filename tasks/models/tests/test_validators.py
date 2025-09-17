import pytest
from django.core.exceptions import ValidationError
from ..validators import validate_task_title, validate_task_estimate, validate_tag_name


class TestValidators:
    """Test cases for model validators."""
    
    @pytest.mark.parametrize("invalid_title,expected_message", [
        ('', 'Task title cannot be empty or just whitespace'),
        ('   ', 'Task title cannot be empty or just whitespace'),
        ('ab', 'Task title must be at least 3 characters long'),
    ])
    def test_validate_task_title_invalid(self, invalid_title, expected_message):
        """Test that invalid task titles raise ValidationError."""
        with pytest.raises(ValidationError, match=expected_message):
            validate_task_title(invalid_title)
    
    @pytest.mark.parametrize("valid_title", [
        'Valid Task Title',
        '  Valid Task Title  ',  # Should work with whitespace
        'Task',
        'A' * 200,  # Max length
    ])
    def test_validate_task_title_valid(self, valid_title):
        """Test that valid titles pass validation."""
        # Should not raise any exception
        validate_task_title(valid_title)
    
    @pytest.mark.parametrize("invalid_estimate,expected_message", [
        (-1, 'Task estimate cannot be negative'),
        (101, 'Task estimate cannot exceed 100 points'),
    ])
    def test_validate_task_estimate_invalid(self, invalid_estimate, expected_message):
        """Test that invalid estimates raise ValidationError."""
        with pytest.raises(ValidationError, match=expected_message):
            validate_task_estimate(invalid_estimate)
    
    @pytest.mark.parametrize("valid_estimate", [0, 50, 100, None])
    def test_validate_task_estimate_valid(self, valid_estimate):
        """Test that valid estimates pass validation."""
        # Should not raise any exception
        validate_task_estimate(valid_estimate)
    
    @pytest.mark.parametrize("invalid_tag_name,expected_message", [
        ('', 'Tag name cannot be empty or just whitespace'),
        ('   ', 'Tag name cannot be empty or just whitespace'),
        ('a', 'Tag name must be at least 2 characters long'),
        ('invalid@tag', 'Tag name can only contain letters, numbers, hyphens, and underscores'),
        ('invalid tag', 'Tag name can only contain letters, numbers, hyphens, and underscores'),
    ])
    def test_validate_tag_name_invalid(self, invalid_tag_name, expected_message):
        """Test that invalid tag names raise ValidationError."""
        with pytest.raises(ValidationError, match=expected_message):
            validate_tag_name(invalid_tag_name)
    
    @pytest.mark.parametrize("valid_tag_name", [
        'valid-tag',
        'valid_tag',
        'ValidTag123',
        '  valid-tag  ',  # Should work with whitespace
        'a' * 64,  # Max length
    ])
    def test_validate_tag_name_valid(self, valid_tag_name):
        """Test that valid tag names pass validation."""
        # Should not raise any exception
        validate_tag_name(valid_tag_name)
