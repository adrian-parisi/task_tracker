"""
AI Service Factory for task management functionality.
"""
from typing import Literal
from .mocked_ai_service import MockedAIService
from .ai_service import AIService
from .protocols import AIServiceProtocol

# Service type literals
ServiceType = Literal["ai", "mock_ai"]


def get_ai_service(service_type: ServiceType = "mock_ai") -> AIServiceProtocol:
    """
    Get an AI service instance of the specified type.
    
    Args:
        service_type: The type of AI service to instantiate.
            - "mock_ai": Returns a MockedAIService instance (default)
            - "ai": Returns a real AIService instance (not yet implemented)
    
    Returns:
        AIServiceProtocol: The AI service instance
        
    Raises:
        ValueError: If an unsupported service type is provided
    """
    if service_type == "mock_ai":
        return MockedAIService()
    elif service_type == "ai":
        return AIService()  # Real AI service (will raise NotImplementedError when called)
    else:
        raise ValueError(f"Unsupported service type: {service_type}. Use 'mock_ai' or 'ai'.")
