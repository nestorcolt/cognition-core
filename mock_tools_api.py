from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

app = FastAPI(
    title="Cognition Core API",
    description="Tool Discovery API",
    version="1.0.0",
)


class CalculatorRequest(BaseModel):
    first_number: int
    second_number: int
    operation: str


# Tool definitions that match our ToolDefinition schema
AVAILABLE_TOOLS = {
    "tools": [
        {
            "name": "calculator",
            "description": "Basic calculator for arithmetic operations",
            "endpoint": "/tools/calculator",
            "parameters": {
                "first_number": {
                    "type": "int",
                    "description": "First number for calculation",
                },
                "second_number": {
                    "type": "int",
                    "description": "Second number for calculation",
                },
                "operation": {
                    "type": "str",
                    "description": "Operation to perform (multiply, add, subtract, divide)",
                },
            },
            "cache_enabled": True,
        }
    ]
}


@app.get("/tools")
async def list_tools():
    """Return list of available tools"""
    return AVAILABLE_TOOLS


@app.post("/tools/calculator")
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
            "cached": False,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
