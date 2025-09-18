"""
Tests for AI service factory.
"""
import pytest
from ai_tools.services.factory import get_ai_service, ServiceType
from ai_tools.services.mocked_ai_service import MockedAIService
from ai_tools.services.ai_service import AIService
from ai_tools.services.protocols import AIServiceProtocol


@pytest.fixture
def valid_service_types():
    """Valid service types for testing."""
    return ["ai", "mock_ai"]


def test_get_ai_service_mock_ai_default():
    """Test getting mocked AI service by default."""
    service = get_ai_service()
    
    assert isinstance(service, MockedAIService)



def test_get_ai_service_mock_ai_explicit():
    """Test getting mocked AI service explicitly."""
    service = get_ai_service("mock_ai")
    
    assert isinstance(service, MockedAIService)



def test_get_ai_service_real_ai():
    """Test getting real AI service."""
    service = get_ai_service("ai")
    
    assert isinstance(service, AIService)


@pytest.mark.parametrize("service_type", ["ai", "mock_ai"])
def test_service_type_literal(service_type):
    """Test ServiceType literal values."""
    service = get_ai_service(service_type)
    assert service is not None


def test_factory_returns_different_types():
    """Test that factory returns different service types."""
    mock_service = get_ai_service("mock_ai")
    real_service = get_ai_service("ai")
    
    assert isinstance(mock_service, MockedAIService)
    assert isinstance(real_service, AIService)
    assert not isinstance(mock_service, AIService)
    assert not isinstance(real_service, MockedAIService)


@pytest.mark.parametrize("service_type,expected_class", [
    ("mock_ai", MockedAIService),
    ("ai", AIService),
])
def test_service_implements_protocol(service_type, expected_class):
    """Test that returned services implement the protocol."""
    service = get_ai_service(service_type)
    
    # Check that service is correct type
    assert isinstance(service, expected_class)
    
    # Check that service has the required methods
    required_methods = ['generate_summary', 'generate_rewrite', 'generate_estimate']
    
    for method_name in required_methods:
        assert hasattr(service, method_name)
        assert callable(getattr(service, method_name))


def test_factory_docstring():
    """Test that factory function has proper docstring."""
    import inspect
    
    docstring = inspect.getdoc(get_ai_service)
    assert docstring is not None
    assert "Get an AI service instance" in docstring
    assert "mock_ai" in docstring
    assert "ai" in docstring
    assert "ValueError" in docstring


@pytest.mark.parametrize("service_type", ["mock_ai", "ai"])
def test_services_are_callable(service_type):
    """Test that all service methods are callable."""
    service = get_ai_service(service_type)
    
    # Test that methods exist and are callable
    assert callable(service.generate_summary)
    assert callable(service.generate_rewrite)
    assert callable(service.generate_estimate)
