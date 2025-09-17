import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from ..tag import Tag


@pytest.fixture
def sample_tag():
    """Create a sample tag for testing."""
    return Tag.objects.create(name='test-tag')


@pytest.fixture
def tags_ordered():
    """Create tags in specific order for ordering tests."""
    Tag.objects.create(name='z-tag')
    Tag.objects.create(name='a-tag')
    Tag.objects.create(name='m-tag')
    return Tag.objects.all()


class TestTagModel:
    """Test cases for Tag model."""
    
    def test_tag_creation(self, sample_tag):
        """Test that tag can be created with valid data."""
        assert sample_tag.name == 'test-tag'
        assert str(sample_tag) == 'test-tag'
    
    def test_tag_name_validation(self):
        """Test that tag name validation works."""
        # Test invalid tag name
        tag = Tag(name='a')  # Too short
        with pytest.raises(ValidationError):
            tag.full_clean()
    
    def test_tag_name_uniqueness(self):
        """Test that tag names must be unique."""
        Tag.objects.create(name='unique-tag')
        
        with pytest.raises(IntegrityError):
            Tag.objects.create(name='unique-tag')
    
    def test_tag_name_case_insensitive_uniqueness(self):
        """Test that tag names are unique case-insensitively."""
        Tag.objects.create(name='Test-Tag')
        
        with pytest.raises(IntegrityError):
            Tag.objects.create(name='test-tag')
    
    def test_tag_clean_method(self):
        """Test that tag clean method normalizes name."""
        tag = Tag(name='  test-tag  ')
        tag.clean()
        assert tag.name == 'test-tag'
    
    def test_tag_save_method(self):
        """Test that tag save method calls validation."""
        tag = Tag(name='a')  # Too short
        with pytest.raises(ValidationError):
            tag.save()
    
    def test_tag_meta_ordering(self, tags_ordered):
        """Test that tags are ordered by name."""
        tags = list(tags_ordered)
        assert tags[0].name == 'a-tag'
        assert tags[1].name == 'm-tag'
        assert tags[2].name == 'z-tag'
    
    @pytest.mark.parametrize("tag_name,expected_name", [
        ('  test-tag  ', 'test-tag'),
        ('Test-Tag', 'Test-Tag'),
        ('valid_tag', 'valid_tag'),
    ])
    def test_tag_clean_normalization(self, tag_name, expected_name):
        """Test that tag clean method normalizes various name formats."""
        tag = Tag(name=tag_name)
        tag.clean()
        assert tag.name == expected_name
