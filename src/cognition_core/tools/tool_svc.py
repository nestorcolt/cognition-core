from crewai.tools.structured_tool import CrewStructuredTool
from crewai.agents.tools_handler import ToolsHandler
from typing import Dict, List, Optional, Any, Type
from cognition_core.config import ConfigManager
from cognition_core.logger import logger
from pydantic import BaseModel, Field
import asyncio
import httpx
import os

logger = logger.getChild(__name__)
os.environ["CONFIG_DIR"] = "../cognition/src/cognition/config"


class CognitionToolsHandler(ToolsHandler):
    """Enhanced tools handler that integrates with ToolService"""

    def __init__(self, tool_service: "ToolService", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_service = tool_service

    def get_tools(self, tool_names: List[str]) -> List[Any]:
        """Fetch current tools from service"""
        return [self.tool_service.get_tool(name) for name in tool_names]


class ParameterDefinition(BaseModel):
    """Schema for parameter definition"""

    type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")


class ToolDefinition(BaseModel):
    """Schema for tool definitions received from API"""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Tool description")
    endpoint: str = Field(..., description="API endpoint for the tool")
    parameters: Dict[str, ParameterDefinition] = Field(
        default_factory=dict, description="Parameter definitions"
    )
    cache_enabled: bool = Field(default=False, description="Whether caching is enabled")


class ToolServiceConfig(BaseModel):
    """Schema for tool service configuration"""

    name: str
    enabled: bool
    base_url: str
    endpoints: List[Dict[str, str]]


class ToolService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.tools: Dict[str, CrewStructuredTool] = {}
        self._http_clients: Dict[str, httpx.AsyncClient] = {}
        self._refresh_lock = asyncio.Lock()
        self._load_config()

    def _load_config(self):
        """Load tool configuration from config manager"""
        try:
            self.config = self.config_manager.get_config("tools")
            self.settings = self.config.get("settings", {})
            self.tool_services = [
                ToolServiceConfig(**service)
                for service in self.config.get("tool_services", [])
                if service.get("enabled", False)
            ]
        except Exception as e:
            logger.error(f"Failed to load tool configuration: {e}")
            raise

    async def _init_clients(self):
        """Initialize HTTP clients for each service"""
        for service in self.tool_services:
            self._http_clients[service.name] = httpx.AsyncClient(
                base_url=service.base_url,
                timeout=self.settings.get("validation", {}).get("response_timeout", 30),
            )

    def _get_python_type(self, type_str: str) -> Type:
        """Convert string type to Python type"""
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        return type_mapping.get(type_str.lower(), str)

    async def fetch_tool_definitions(self) -> List[ToolDefinition]:
        """Fetch tool definitions from all configured services"""
        all_tools = []

        for service in self.tool_services:
            client = self._http_clients[service.name]
            logger.debug(f"Fetching tools from {service.name} at {service.base_url}")

            for endpoint in service.endpoints:
                if endpoint["method"] == "GET" and "/tools" in endpoint["path"]:
                    try:
                        response = await client.get(endpoint["path"])
                        response.raise_for_status()

                        response_data = response.json()
                        tools_data = response_data.get("tools", [])

                        for tool_data in tools_data:
                            try:
                                tool = ToolDefinition(**tool_data)
                                all_tools.append(tool)
                            except Exception as e:
                                logger.error(
                                    f"Failed to parse tool data: {tool_data}. Error: {e}"
                                )
                                continue

                    except Exception as e:
                        logger.error(
                            f"Error fetching tools from {service.name}: {str(e)}"
                        )
                        logger.debug("Full error details:", exc_info=True)
                        continue

        return all_tools

    async def load_tools(self):
        """Fetch and load all tools into memory"""
        tool_definitions = await self.fetch_tool_definitions()
        logger.info(f"Fetched {len(tool_definitions)} tool definitions")

        for tool_def in tool_definitions:
            logger.info(f"\nProcessing tool: {tool_def.name}")
            logger.info(f"Parameters: {tool_def.parameters}")

            # Create field definitions for parameters
            fields = {}
            for name, param in tool_def.parameters.items():
                python_type = self._get_python_type(param.type)
                fields[name] = (python_type, Field(..., description=param.description))
                logger.info(
                    f"Created field {name}: {python_type} - {param.description}"
                )

            # Create the parameter schema class
            param_schema = type(
                f"{tool_def.name}Params",
                (BaseModel,),
                {
                    "__annotations__": {k: v[0] for k, v in fields.items()},
                    **{k: v[1] for k, v in fields.items()},
                },
            )
            logger.info(f"Created parameter schema: {param_schema.__name__}")

            # Create the tool
            tool = CrewStructuredTool.from_function(
                name=tool_def.name,
                description=tool_def.description,
                args_schema=param_schema,
                func=self._create_tool_executor(tool_def),
            )
            logger.info(f"Created tool: {tool.name}")

            self.tools[tool_def.name] = tool
            logger.info(f"Registered tool {tool_def.name} in memory")

        logger.info(f"\nTotal tools loaded: {len(self.tools)}")
        logger.info(f"Available tools: {list(self.tools.keys())}")

        # Print tool details
        for name, tool in self.tools.items():
            logger.info(f"\nTool: {name}")
            logger.info(f"Description: {tool.description}")
            logger.info(f"Parameters: {tool.args_schema.model_json_schema()}")

    def _create_tool_executor(self, tool_def: ToolDefinition):
        """Creates an executor function for the tool"""

        async def execute(**kwargs):
            # Tool execution logic here
            return f"Executed {tool_def.name} with {kwargs}"

        return execute

    async def refresh_tools(self):
        """Refresh tools while maintaining existing ones"""
        async with self._refresh_lock:
            existing_tools = self.tools.copy()
            try:
                await self.load_tools()
                logger.info(f"Successfully refreshed {len(self.tools)} tools")
            except Exception as e:
                self.tools = existing_tools
                logger.error(f"Failed to refresh tools: {e}")
                raise

    async def initialize(self):
        """Initialize the tool service"""
        await self._init_clients()
        await self.load_tools()

    async def close(self):
        """Cleanup resources"""
        for client in self._http_clients.values():
            await client.aclose()

    def get_tool(self, name: str) -> Optional[CrewStructuredTool]:
        """Retrieve a specific tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """List all available tool names"""
        return list(self.tools.keys())


async def main():
    tool_service = ToolService()
    await tool_service.initialize()

    try:
        tools = tool_service.list_tools()
        print(f"Available tools: {tools}")

    finally:
        await tool_service.close()


if __name__ == "__main__":
    asyncio.run(main())
