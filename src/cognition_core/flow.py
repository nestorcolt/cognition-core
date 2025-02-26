from crewai.flow.flow import Flow, listen, start, router
from cognition_core.base import CognitionComponent
from cognition_core.config import config_manager
from pydantic import Field, ConfigDict
from typing import Optional, TypeVar, Generic
from uuid import UUID

T = TypeVar('T')

class CognitionFlow(Flow[T], CognitionComponent, Generic[T]):
    """Enhanced Flow with Cognition configuration and component management"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core fields
    flow_id: UUID = Field(default_factory=UUID)
    config: dict = Field(default_factory=dict)
    
    def __init__(
        self,
        name: str = "default_flow",
        enabled: bool = True,
        config_path: Optional[str] = None,
        *args,
        **kwargs
    ):
        # Load flow config
        self.config = config_manager.load_config(config_path) if config_path else {}
        
        # Initialize component fields
        kwargs["name"] = name
        kwargs["enabled"] = enabled
        
        # Initialize parent classes
        super().__init__(*args, **kwargs)
        
        # Setup any additional services needed
        self._setup_services()

    def _setup_services(self):
        """Initialize any required services for the flow"""
        # Add service initialization as needed
        pass

    @classmethod
    def from_config(cls, config_path: str) -> "CognitionFlow":
        """Create flow instance from configuration file"""
        config = config_manager.load_config(config_path)
        return cls(
            name=config.get("name", "default_flow"),
            enabled=config.get("enabled", True),
            config_path=config_path
        ) 