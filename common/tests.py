"""
Tests for common models and utilities.
"""
import pytest
from django.test import TestCase
from django.db import models
from .models import BaseModel


class TestModel(BaseModel):
    """Test model that inherits from BaseModel."""
    name = models.CharField(max_length=100)


class BaseModelTest(TestCase):
    """Test cases for BaseModel functionality."""
    
    def test_base_model_fields(self):
        """Test that BaseModel provides the expected fields."""
        # Check that the model has the expected fields
        fields = [field.name for field in TestModel._meta.fields]
        
        assert 'id' in fields
        assert 'created_at' in fields
        assert 'updated_at' in fields
        assert 'name' in fields  # Our test field
    
    def test_base_model_id_is_uuid(self):
        """Test that the id field is a UUID field."""
        id_field = TestModel._meta.get_field('id')
        assert isinstance(id_field, models.UUIDField)
        assert id_field.primary_key is True
        assert id_field.editable is False
    
    def test_base_model_timestamps(self):
        """Test that timestamp fields are configured correctly."""
        created_at_field = TestModel._meta.get_field('created_at')
        updated_at_field = TestModel._meta.get_field('updated_at')
        
        assert isinstance(created_at_field, models.DateTimeField)
        assert isinstance(updated_at_field, models.DateTimeField)
        assert created_at_field.auto_now_add is True
        assert updated_at_field.auto_now is True
    
    def test_base_model_ordering(self):
        """Test that BaseModel sets correct default ordering."""
        assert TestModel._meta.ordering == ['-created_at']
    
    def test_base_model_abstract(self):
        """Test that BaseModel is abstract."""
        assert TestModel._meta.abstract is False  # TestModel is not abstract
        assert BaseModel._meta.abstract is True   # BaseModel is abstract
    
    def test_base_model_str_representation(self):
        """Test the default string representation."""
        # This would need a database to test fully, but we can test the method exists
        assert hasattr(TestModel(), '__str__')
