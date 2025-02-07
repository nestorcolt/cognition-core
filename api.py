from fastapi import FastAPI, HTTPException
from typing import Dict, List, Optional
from pydantic import BaseModel
import uvicorn
from schemas import ToolsConfig, Tool, ToolParameters, CacheRules

# Initialize FastAPI app
app = FastAPI(
    title="Cognition Core API",
    description="API for managing AI agents and tool integration",
    version="1.0.0",
)

# Example tool configuration
DEFAULT_TOOLS_CONFIG = {
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

# Initialize tools configuration
tools_config = ToolsConfig(**DEFAULT_TOOLS_CONFIG)


class CalculatorRequest(BaseModel):
    first_number: int
    second_number: int
    operation: str


# Tool endpoints
@app.get("/tools")
async def list_tools():
    try:
        return {
            "status": "success",
            "tools": [tool.dict() for tool in tools_config.tools],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tools/{tool_name}")
async def get_tool(tool_name: str):
    try:
        tool = next(
            (tool for tool in tools_config.tools if tool.name == tool_name), None
        )
        if not tool:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        return {"status": "success", "tool": tool.dict()}
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tools/calculator")
async def calculator(request: CalculatorRequest):
    try:
        result = None
        if request.operation == "multiply":
            result = request.first_number * request.second_number
        elif request.operation == "add":
            result = request.first_number + request.second_number
        elif request.operation == "subtract":
            result = request.first_number - request.second_number
        elif request.operation == "divide":
            if request.second_number == 0:
                raise HTTPException(status_code=400, detail="Division by zero")
            result = request.first_number / request.second_number
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported operation: {request.operation}"
            )

        return {
            "status": "success",
            "result": result,
            "operation": request.operation,
            "cached": False,  # You can implement caching logic here
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
