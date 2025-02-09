from cognition_core.base import CognitionComponent
from cognition_core.tools.tool_svc import ToolService
from pydantic import Field, ConfigDict
from typing import List, Optional
from crewai import Task


class CognitionTask(Task, CognitionComponent):
    """Enhanced Task with component management support"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Tool integration fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, name: str, enabled: bool = True, *args, **kwargs):
        # Initialize CognitionComponent fields
        kwargs["name"] = name
        kwargs["enabled"] = enabled

        # Initialize both parent classes
        super().__init__(*args, **kwargs)

        # Load initial tools if service provided
        if self.tool_service:
            self._refresh_tools()

    def _refresh_tools(self):
        """Refresh tools from service"""
        if self.tool_service and self.tool_names:
            self.tools = [self.tool_service.get_tool(name) for name in self.tool_names]

    @classmethod
    def from_config(
        cls, config: dict, tool_service: Optional[ToolService] = None
    ) -> "CognitionTask":
        """Create task from configuration"""
        # Extract tool names from config
        tool_names = config.pop("tools", [])
        return cls(
            name=config.pop("name"),
            enabled=config.pop("enabled"),
            tool_names=tool_names,
            tool_service=tool_service,
            **config,
        )
