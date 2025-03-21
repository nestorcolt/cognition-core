from cognition_core.config import config_manager
from typing import Optional, TypeVar, Any
from pydantic import Field, ConfigDict
from crewai.flow.flow import Flow
from uuid import UUID

T = TypeVar("T")


class CognitionFlow(Flow):

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
        **kwargs,
    ):
        # Load flow config
        self._config_data = (
            config_manager.load_config(config_path) if config_path else {}
        )

        # Initialize parent classes
        super().__init__(*args, **kwargs)

        # Store config path
        self.config_path = config_path

        # Setup any additional services needed
        self._setup_services()

    def _setup_services(self):
        """Initialize any required services for the flow"""
        # Add service initialization as needed
        pass

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self._config_data.get(key, default)

    @classmethod
    def from_config(cls, config_path: str) -> "CognitionFlow":
        """Create flow instance from configuration file"""
        config = config_manager.load_config(config_path)
        return cls(
            name=config.get("name", "default_flow"),
            enabled=config.get("enabled", True),
            config_path=config_path,
        )
