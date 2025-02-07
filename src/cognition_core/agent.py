from cognition_core.tools.tool_svc import ToolService
from crewai import Agent
from typing import List, Optional
from pydantic import BaseModel


class CognitionAgent(Agent):
    """Enhanced Agent with integrated tool service support"""

    def __init__(
        self,
        tool_names: Optional[List[str]] = None,
        tool_service: Optional[ToolService] = None,
        **kwargs,
    ):
        # Initialize tool service if provided
        self.tool_service = tool_service

        # Get tools by name if tool service is available
        if tool_service and tool_names:
            tools = [tool_service.get_tool(name) for name in tool_names]
            kwargs["tools"] = tools

        super().__init__(**kwargs)

    @classmethod
    def from_config(
        cls, config: dict, tool_service: Optional[ToolService] = None
    ) -> "CognitionAgent":
        """Create agent from configuration with optional tool service integration"""
        # Extract tool names from config if present
        tool_names = config.pop("tools", [])

        return cls(tool_names=tool_names, tool_service=tool_service, **config)
