from cognition_core.tools.tool_svc import ToolService, CognitionToolsHandler
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.agents.tools_handler import ToolsHandler
from crewai.utilities.converter import Converter
from typing import List, Optional, Any
from pydantic import Field, ConfigDict


class CognitionToolsHandler(ToolsHandler):
    """Enhanced tools handler that integrates with ToolService"""

    def __init__(self, tool_service: ToolService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_service = tool_service

    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Fetch current tools from service"""
        return [self.tool_service.get_tool(name) for name in tool_names]


class CognitionAgent(BaseAgent):
    """Enhanced Agent with integrated tool service support"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    tool_names: List[str] = Field(
        default_factory=list, description="Names of tools to use"
    )
    tool_service: Optional[ToolService] = Field(
        default=None, description="Tool service instance"
    )
    function_calling_llm_internal: bool = Field(default=False)

    @property
    def function_calling_llm(self) -> bool:
        """Check if the LLM supports function calling"""
        return hasattr(self.llm, "function_calling") and self.llm.function_calling

    @function_calling_llm.setter
    def function_calling_llm(self, value: bool):
        """Set function calling LLM flag"""
        self.function_calling_llm_internal = value

    def __init__(
        self,
        tool_names: Optional[List[str]] = None,
        tool_service: Optional[ToolService] = None,
        **kwargs,
    ):
        # Store tool names and service
        kwargs["tool_names"] = tool_names or []
        kwargs["tool_service"] = tool_service

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

    def _parse_tools(self, tools: List[Any]) -> List[Any]:
        """Parse and validate tools"""
        if not tools and self.tool_service and self.tool_names:
            return self.tools_handler.get_tools(self.tool_names)
        return tools

    def create_agent_executor(self):
        """Create the agent executor with current tools"""
        self.tools = self._parse_tools(self.tools)
        return super().create_agent_executor()

    def get_delegation_tools(self) -> List[Any]:
        """Get tools available for delegation"""
        return self.tools

    def get_output_converter(self) -> Optional[Converter]:
        """Get output converter for the agent"""
        return None  # Or implement your custom converter

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
