from cognition_core.tools.tool_svc import ToolService, CognitionToolsHandler
from cognition_core.memory.mem_svc import MemoryService
from cognition_core.config import ConfigManager
from crewai.project import CrewBase
from crewai.agents import BaseAgent
from crewai.tools import BaseTool
from pathlib import Path
from crewai import Crew
from crewai import Task
from typing import List


@CrewBase
class CognitionCoreCrewBase:
    """Cognition crew base class with integrated tool service"""

    def __init__(self):
        super().__init__()
        # Initialize config manager with config directory
        self.config_manager = ConfigManager()

        # Initialize memory service with config manager
        self.memory_service = MemoryService(self.config_manager)

        # Initialize tool service
        self.tool_service = ToolService()

        # Get configs using ConfigManager
        self.agents_config = str(Path(self.config_manager.config_dir) / "agents.yaml")
        self.tasks_config = str(Path(self.config_manager.config_dir) / "tasks.yaml")
        self.crew_config = str(Path(self.config_manager.config_dir) / "crew.yaml")

        # LLM GATEWAY CONFIG
        self.portkey_config = self.config_manager.get_portkey_config()

    async def setup(self):
        """Initialize services including tool loading"""
        await self.tool_service.initialize()

    def get_tool(self, name: str):
        """Get a specific tool by name"""
        return self.tool_service.get_tool(name)

    def list_tools(self):
        """List all available tools"""
        return self.tool_service.list_tools()


class CognitionCrew(Crew):
    def __init__(self, tool_service: ToolService, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_service = tool_service
        self.tools_handler = CognitionToolsHandler(tool_service)

    def _prepare_tools(
        self, agent: BaseAgent, task: Task, tools: List[str]
    ) -> List[BaseTool]:
        # First get base tools from parent
        tools = super()._prepare_tools(agent, task, tools)

        # Then add our dynamic tools
        if isinstance(tools, list) and all(isinstance(t, str) for t in tools):
            # If tools are string names, fetch from service
            tools = self.tools_handler.get_tools(tools)

        return tools

    def _merge_tools(
        self, existing_tools: List[BaseTool], new_tools: List[BaseTool]
    ) -> List[BaseTool]:
        """Override to handle our dynamic tools"""
        if not new_tools:
            return existing_tools

        # Convert any string tool names to actual tools
        new_tools = [
            self.tool_service.get_tool(tool) if isinstance(tool, str) else tool
            for tool in new_tools
        ]

        return super()._merge_tools(existing_tools, new_tools)
