from cognition_core.tools.tool_svc import ToolService
from cognition_core.llm import init_portkey_llm
from cognition_core.logger import logger
from pydantic import Field, ConfigDict
from typing import List, Optional
from crewai import Agent
import logging
import litellm

# litellm._turn_on_debug()


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
        llm = config.pop("llm")

        # If the portkey config is not None or empty, we initialize the llm with the portkey config
        if portkey_on:
            logger.info(f"Initializing the llm with the portkey config: {portkey_on}")
            llm = init_portkey_llm(
                model=llm,
                portkey_config=portkey_config,
            )

        super().__init__(config=config, llm=llm, *args, **kwargs)
