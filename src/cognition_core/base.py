from pydantic import BaseModel, Field
from abc import ABC, abstractmethod
from typing import Optional


class CognitionComponent(BaseModel):
    """Base interface for all Cognition components"""

    enabled: bool = Field(default=True, description="Component enabled status")
    name: str = Field(..., description="Component name")
    description: Optional[str] = Field(None, description="Component description")

    @property
    def is_available(self) -> bool:
        """Check if component is enabled and available"""
        return self.enabled


class ComponentManager(ABC):
    """Abstract interface for component management"""

    @abstractmethod
    def activate_component(self, component_type: str, name: str) -> bool:
        """Activate a specific component"""
        pass

    @abstractmethod
    def deactivate_component(self, component_type: str, name: str) -> bool:
        """Deactivate a specific component"""
        pass

    @abstractmethod
    def _update_components(self) -> None:
        """Update available components"""
        pass

    @abstractmethod
    def get_active_workflow(self) -> dict:
        """Get currently active workflow components"""
        pass
