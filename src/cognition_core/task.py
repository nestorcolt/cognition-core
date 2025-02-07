from cognition_core.tools.tool_svc import ToolService
from typing import List, Optional
from crewai import Task


class CognitionTask(Task):
    """Enhanced Task with tool service integration"""

    tool_names: List[str] = Field(
        default_factory=list, description="Names of tools to use from tool service"
    )

    tool_service: Optional[ToolService] = Field(
        default=None, description="Tool service instance"
    )

    def __init__(
        self,
        tool_names: Optional[List[str]] = None,
        tool_service: Optional[ToolService] = None,
        **kwargs,
    ):
        # Store tool service reference
        self.tool_service = tool_service
        self.tool_names = tool_names or []

        # Initialize with empty tools list
        kwargs["tools"] = []
        super().__init__(**kwargs)

        # Load initial tools if service provided
        if tool_service:
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

        return cls(tool_names=tool_names, tool_service=tool_service, **config)
