from pydantic import BaseModel
from typing import Dict, List, Literal, Union


class CacheRules(BaseModel):
    operation: str = "multiply"


class ToolParameters(BaseModel):
    first_number: tuple[Literal["int"], str] = ("int", "First number for calculation")
    second_number: tuple[Literal["int"], str] = ("int", "Second number for calculation")
    operation: tuple[Literal["str"], str] = ("str", "Mathematical operation to perform")


class Tool(BaseModel):
    name: str = "calculator"
    description: str = "Performs mathematical calculations"
    endpoint: str = "/api/tools/calculator"
    parameters: ToolParameters
    cache_enabled: bool = True
    cache_rules: CacheRules


class ToolsConfig(BaseModel):
    tools: List[Tool]


# Example usage:
example_config = {
    "tools": [
        {
            "name": "calculator",
            "description": "Performs mathematical calculations",
            "endpoint": "/api/tools/calculator",
            "parameters": {
                "first_number": ["int", "First number for calculation"],
                "second_number": ["int", "Second number for calculation"],
                "operation": ["str", "Mathematical operation to perform"],
            },
            "cache_enabled": True,
            "cache_rules": {"operation": "multiply"},
        }
    ]
}
