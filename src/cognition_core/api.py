from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, Request
from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any
import asyncio
import uuid


class AgentRequest(BaseModel):
    """Base request model for agent interactions"""
    topic: str = "AI LLMs"
    current_year: str = str(datetime.now().year)


class AgentResponse(BaseModel):
    """Base response model for agent tasks"""
    task_id: str
    status: str
    message: str


class CoreAPIService:
    """Core API service that can be used by any Cognition-based agent"""
    
    def __init__(self):
        self.app = FastAPI()
        self.tasks = {}
        self.executor = ThreadPoolExecutor()
        self._setup_routes()

    def _setup_routes(self):
        """Initialize API routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}

        @self.app.post("/v1/agent/run", response_model=AgentResponse)
        async def run_agent(request: Request, agent_request: AgentRequest):
            crew = request.app.state.crew
            return await self._run_task(crew, agent_request.dict())

    async def _run_task(self, crew, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a crew task asynchronously"""
        task_id = str(uuid.uuid4())
        
        # Start task processing in background
        asyncio.create_task(self._process_task(task_id, crew, inputs))
        
        return {
            "task_id": task_id,
            "status": "processing",
            "message": "Task started successfully"
        }

    async def _process_task(self, task_id: str, crew, inputs: Dict):
        """Process the crew task and store results"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: crew.kickoff(inputs=inputs)
            )
            self.tasks[task_id] = {
                "status": "completed",
                "result": result
            }
        except Exception as e:
            self.tasks[task_id] = {
                "status": "failed",
                "error": str(e)
            }

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app


def create_crew_api(crew) -> FastAPI:
    """Create a FastAPI application for a crew"""
    api_service = CoreAPIService()
    app = api_service.get_app()
    app.state.crew = crew
    return app