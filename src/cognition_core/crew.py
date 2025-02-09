from cognition_core.tools.tool_svc import ToolService, CognitionToolsHandler
from crewai.agents.agent_builder.base_agent import BaseAgent
from cognition_core.memory.mem_svc import MemoryService
from cognition_core.config import ConfigManager
from cognition_core.agent import CognitionAgent
from typing import List, Optional, Any, TypeVar
from pydantic import Field, ConfigDict
from crewai.project import CrewBase
from crewai.project import CrewBase
from crewai.tools import BaseTool
from crewai import Crew, Task
from pathlib import Path
import asyncio


T = TypeVar("T", bound=type)


# First, create a base decorator that inherits from CrewBase's WrappedClass
def CognitionCoreCrewBase(cls: T) -> T:
    """Enhanced CrewBase decorator with Cognition-specific functionality"""

    # Initialize config before class wrapping
    config_manager = ConfigManager()

    # Set config paths before CrewBase wrapping
    if config_manager.config_dir:
        cls.agents_config = str(Path(config_manager.config_dir) / "agents.yaml")
        cls.tasks_config = str(Path(config_manager.config_dir) / "tasks.yaml")

    # Now wrap with CrewBase
    BaseWrappedClass = CrewBase(cls)

    class CognitionWrappedClass(BaseWrappedClass):
        def __init__(self, *args, **kwargs):
            # Initialize services
            self.config_manager = ConfigManager()
            self.memory_service = MemoryService(self.config_manager)
            self.tool_service = ToolService()
            self.portkey_config = self.config_manager.get_portkey_config()

            # Initialize tool service
            asyncio.run(self.setup())

            # Initialize parent last
            super().__init__(*args, **kwargs)

        async def setup(self):
            """Initialize services including tool loading"""
            await self.tool_service.initialize()

        def get_tool(self, name: str):
            """Get a specific tool by name"""
            return self.tool_service.get_tool(name)

        def list_tools(self):
            """List all available tools"""
            return self.tool_service.list_tools()

        def get_cognition_agent(
            self, config: dict, llm: Any, verbose: bool = True
        ) -> CognitionAgent:
            """Create a CognitionAgent with tools from service."""
            available_tools = self.tool_service.list_tools()
            tool_instances = [
                self.tool_service.get_tool(name) for name in available_tools
            ]

            # Extract name from config or use a default
            agent_name = config.get("name", config.get("role", "default_agent"))

            return CognitionAgent(
                name=agent_name,  # Pass name from config
                config=config,
                llm=llm,
                verbose=verbose,
                tools=tool_instances,
                tool_names=available_tools,
                tool_service=self.tool_service,
            )

    return CognitionWrappedClass


class CognitionCrew(Crew):
    """Enhanced Crew with integrated tool service"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Core CrewAI fields
    tasks: List[Task] = Field(default_factory=list)
    agents: List[BaseAgent] = Field(default_factory=list)
    process: str = Field(default="sequential")
    verbose: bool = Field(default=False)

    # Our custom fields
    tool_service: Optional[ToolService] = Field(
        default=None, description="Tool service instance"
    )
    tools_handler: Optional[CognitionToolsHandler] = Field(
        default=None, description="Tools handler instance"
    )

    def __init__(self, tool_service: Optional[ToolService] = None, *args, **kwargs):
        # Pass both tool_service and tools_handler through kwargs
        kwargs["tool_service"] = tool_service
        kwargs["tools_handler"] = (
            CognitionToolsHandler(tool_service) if tool_service else None
        )
        super().__init__(*args, **kwargs)

    def _merge_tools(
        self, existing_tools: List[BaseTool], new_tools: List[BaseTool]
    ) -> List[BaseTool]:
        """Override to handle our dynamic tools"""
        if not new_tools:
            return existing_tools

        # Convert any string tool names to actual tools
        if self.tool_service:
            new_tools = [
                self.tool_service.get_tool(tool) if isinstance(tool, str) else tool
                for tool in new_tools
            ]

        return super()._merge_tools(existing_tools, new_tools)
