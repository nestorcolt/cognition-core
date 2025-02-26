import pytest
from unittest.mock import Mock
from typing import Dict, Any

class MockCrewResponse:
    """Mock crew response object"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

@pytest.fixture
def mock_crew_factory():
    """Factory for creating mock crews with custom responses"""
    def create_mock_crew(**response_data) -> Mock:
        mock_crew = Mock()
        mock_crew.kickoff.return_value = MockCrewResponse(**response_data)
        return mock_crew
    return create_mock_crew

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    return {
        "name": "test_flow",
        "enabled": True,
        "settings": {
            "risk_thresholds": {
                "high": 0.7,
                "medium": 0.4
            }
        }
    }

@pytest.fixture
def mock_state_factory():
    """Factory for creating mock flow states"""
    def create_mock_state(**state_data) -> Dict[str, Any]:
        return {
            "id": "test-flow-id",
            **state_data
        }
    return create_mock_state 