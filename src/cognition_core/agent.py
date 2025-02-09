from cognition_core.base import CognitionComponent
from cognition_core.tools.tool_svc import ToolService
from pydantic import Field, ConfigDict
from typing import List, Optional
from crewai import Agent


class CognitionAgent(Agent, CognitionComponent):
    """Enhanced Agent with component management support"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, name: str, enabled: bool = True, *args, **kwargs):
        # Initialize CognitionComponent fields
        kwargs["name"] = name
        kwargs["enabled"] = enabled

        # Initialize both parent classes
        super().__init__(*args, **kwargs)
