from cognition_core.tools.tool_svc import ToolService
from pydantic import Field, ConfigDict
from typing import List, Optional
from crewai import Agent


class CognitionAgent(Agent):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, name: str, enabled: bool = True, *args, **kwargs):
        super().__init__(*args, **kwargs)
