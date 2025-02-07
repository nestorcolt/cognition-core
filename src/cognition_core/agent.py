from cognition_core.tools.tool_svc import ToolService, CognitionToolsHandler
from crewai.agents.tools_handler import ToolsHandler
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from crewai import Agent


class CognitionToolsHandler(ToolsHandler):
    """Enhanced tools handler that integrates with ToolService"""

    def __init__(self, tool_service: ToolService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_service = tool_service

    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Fetch current tools from service"""
        return [self.tool_service.get_tool(name) for name in tool_names]


class CognitionAgent(Agent):
    """Enhanced Agent with integrated tool service support"""

    tool_names: List[str] = Field(
        default_factory=list, description="Names of tools to use"
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
        # Store tool names and service
        self.tool_names = tool_names or []
        self.tool_service = tool_service

        # Initialize with empty tools list
        kwargs["tools"] = []

        # Create our custom tools handler
        if tool_service:
            kwargs["tools_handler"] = CognitionToolsHandler(tool_service)

        super().__init__(**kwargs)

        # Load initial tools
        self._refresh_tools()

    def _refresh_tools(self):
        """Refresh tools from service"""
        if self.tool_service and self.tool_names:
            self.tools = self.tools_handler.get_tools(self.tool_names)
            # Recreate agent executor with new tools
            self.create_agent_executor()

    @classmethod
    def from_config(
        cls, config: dict, tool_service: Optional[ToolService] = None
    ) -> "CognitionAgent":
        """Create agent from configuration with optional tool service integration"""
        # Extract tool names from config if present
        tool_names = config.pop("tools", [])

        return cls(tool_names=tool_names, tool_service=tool_service, **config)

    def execute_task(self, *args, **kwargs):
        """Override execute_task to refresh tools before execution"""
        self._refresh_tools()
        return super().execute_task(*args, **kwargs)
