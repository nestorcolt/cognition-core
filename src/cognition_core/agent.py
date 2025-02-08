from cognition_core.tools.tool_svc import ToolService
from typing import List, Optional
from pydantic import Field, ConfigDict
from crewai import Agent


class CognitionAgent(Agent):
    """Enhanced Agent with integrated tool service support"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, *args, **kwargs):
        # If we have tool service and tool names, get the tools
        tool_service = kwargs.get("tool_service")
        tool_names = kwargs.get("tool_names", [])

        if tool_service and tool_names:
            kwargs["tools"] = [tool_service.get_tool(name) for name in tool_names]

        super().__init__(*args, **kwargs)
