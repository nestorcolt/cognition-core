from cognition_core.memory.mem_svc import MemoryService
from cognition_core.tools.tool_svc import ToolService
from cognition_core.config import ConfigManager
from crewai.project import CrewBase
from pathlib import Path


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
