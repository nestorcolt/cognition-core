from cognition_core.tools.tool_svc import ToolService
from cognition_core.llm import init_portkey_llm
from cognition_core.logger import logger
from pydantic import Field, ConfigDict
from typing import List, Optional
from crewai import Agent
import logging


class CognitionAgent(Agent):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, config: dict, *args, **kwargs) -> None:

        if logger.isEnabledFor(logging.DEBUG):
            import json

            logger.debug(
                f"Agent Config:\n{json.dumps(config, indent=2)}\n-----------------------------------"
            )

        # The portkey config is optional
        portkey_on = config.pop("portkey_on", False)
        portkey_config = config.pop("portkey_config", {})
        trace_id = config.pop("trace_id", "cognition_agent")
        portkey_virtual_key = config.pop("portkey_virtual_key", "N/A")

        # If the portkey config is not None or empty, we initialize the llm with the portkey config
        if portkey_on:
            logger.info(f"Initializing the llm with the portkey config: {portkey_on}")
            config["llm"] = init_portkey_llm(
                portkey_virtual_key=portkey_virtual_key,
                portkey_config=portkey_config,
                model=config["llm"],
                trace_id=trace_id,
            )

        super().__init__(config=config, *args, **kwargs)
