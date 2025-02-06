from crewai.tools.structured_tool import CrewStructuredTool
from typing import Dict, List, Optional, Any
from cognition.config import ConfigManager
from pydantic import BaseModel, Field
from cognition.logger import logger
import asyncio
import httpx
import os


class ToolServiceConfig(BaseModel):
    """Schema for tool service configuration"""

    name: str
    enabled: bool
    base_url: str
    endpoints: List[Dict[str, str]]
    headers: Optional[Dict[str, str]] = None


class ToolDefinition(BaseModel):
    """Schema for tool definitions received from API"""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Tool description")
    endpoint: str = Field(..., description="API endpoint for the tool")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter definitions"
    )
    cache_enabled: bool = Field(default=False, description="Whether caching is enabled")
    cache_rules: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom caching rules"
    )


class ToolService:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.tools: Dict[str, CrewStructuredTool] = {}
        self._http_clients: Dict[str, httpx.AsyncClient] = {}
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
            headers = {}
            if service.headers:
                # Process environment variables in headers
                headers = {
                    k: (
                        v.format(**dict(os.environ))
                        if isinstance(v, str) and v.startswith("${")
                        else v
                    )
                    for k, v in service.headers.items()
                }

            self._http_clients[service.name] = httpx.AsyncClient(
                base_url=service.base_url,
                headers=headers,
                timeout=self.settings.get("validation", {}).get("response_timeout", 30),
            )

    async def fetch_tool_definitions(self) -> List[ToolDefinition]:
        """Fetch tool definitions from all configured services"""
        all_tools = []

        for service in self.tool_services:
            client = self._http_clients[service.name]

            for endpoint in service.endpoints:
                if endpoint["method"] == "GET" and "/tools" in endpoint["path"]:
                    try:
                        response = await client.get(endpoint["path"])
                        response.raise_for_status()
                        tools = response.json()
                        all_tools.extend([ToolDefinition(**tool) for tool in tools])
                    except Exception as e:
                        logger.error(f"Error fetching tools from {service.name}: {e}")
                        continue

        return all_tools

    def _create_cache_function(self, tool_def: ToolDefinition):
        """Creates a cache function based on tool definition and global settings"""
        if not self.settings["cache"]["enabled"] or not tool_def.cache_enabled:
            return None

        def cache_func(args: Dict[str, Any], result: Any) -> bool:
            if not tool_def.cache_rules:
                return True

            # Apply custom cache rules
            for rule_key, rule_value in tool_def.cache_rules.items():
                if rule_key in args and args[rule_key] != rule_value:
                    return False
            return True

        return cache_func

    async def initialize(self):
        """Initialize the tool service"""
        await self._init_clients()
        await self.load_tools()

    async def load_tools(self):
        """Fetch and load all tools into memory"""
        tool_definitions = await self.fetch_tool_definitions()

        for tool_def in tool_definitions:
            # Create parameter schema dynamically
            param_schema = type(
                f"{tool_def.name}Params",
                (BaseModel,),
                {
                    field_name: (field_type, Field(..., description=field_desc))
                    for field_name, (
                        field_type,
                        field_desc,
                    ) in tool_def.parameters.items()
                },
            )

            tool = CrewStructuredTool.from_function(
                name=tool_def.name,
                description=tool_def.description,
                args_schema=param_schema,
                func=self._create_tool_executor(tool_def),
            )

            if self.settings["cache"]["enabled"] and tool_def.cache_enabled:
                tool.cache_function = self._create_cache_function(tool_def)

            self.tools[tool_def.name] = tool

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
    # Initialize tool service
    tool_service = ToolService()
    await tool_service.initialize()

    try:
        # Get available tools
        tools = tool_service.list_tools()
        print(f"Available tools: {tools}")

        # Get a specific tool
        calculator = tool_service.get_tool("calculator")
        if calculator:
            result = await calculator.run(first_number=5, second_number=3)
            print(f"Calculation result: {result}")

    finally:
        await tool_service.close()


if __name__ == "__main__":
    asyncio.run(main())
