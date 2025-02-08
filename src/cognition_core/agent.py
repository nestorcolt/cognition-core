from crewai.agents.tools_handler import ToolsHandler
from cognition_core.tools.tool_svc import ToolService
from crewai.agents.tools_handler import ToolsHandler
from typing import List, Optional, Any, Callable
from crewai.utilities.converter import Converter
from pydantic import Field, ConfigDict
from crewai.tools import BaseTool
from crewai.task import Task
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

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Required CrewAI fields
    step_callback: Optional[Callable] = Field(default=None)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)
    function_calling_llm_internal: bool = Field(default=False)

    @property
    def function_calling_llm(self) -> bool:
        """Check if the LLM supports function calling"""
        return hasattr(self.llm, "function_calling") and self.llm.function_calling

    @function_calling_llm.setter
    def function_calling_llm(self, value: bool):
        """Set function calling LLM flag"""
        self.function_calling_llm_internal = value

    def __init__(self, *args, **kwargs):
        # Tools and tool_names should already be properly set by get_cognition_agent
        super().__init__(*args, **kwargs)

        # Store references for later use
        self.tool_names = kwargs.get("tool_names", [])
        self.tool_service = kwargs.get("tool_service")

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

    def create_agent_executor(
        self, tools: Optional[List[BaseTool]] = None, task: Optional[Task] = None
    ) -> None:
        """Create an agent executor with tool service integration.

        Args:
            tools: Optional list of tools to use
            task: Optional task being executed
        """
        # Initialize tools list
        all_tools = list(tools or [])

        # Add tools from service if available
        if self.tool_service and self.tool_names:
            service_tools = [
                self.tool_service.get_tool(name) for name in self.tool_names
            ]
            all_tools.extend(service_tools)

        # Call parent implementation with combined tools
        super().create_agent_executor(tools=all_tools, task=task)

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
