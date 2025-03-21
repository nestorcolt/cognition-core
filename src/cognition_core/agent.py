from cognition_core.tools.tool_svc import ToolService
from cognition_core.llm import init_portkey_llm
from pydantic import Field, ConfigDict
from typing import List, Optional
from logger import logger
from crewai import Agent


class CognitionAgent(Agent):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Our custom fields
    tool_names: List[str] = Field(default_factory=list)
    tool_service: Optional[ToolService] = Field(default=None)

    def __init__(self, name: str, *args, **kwargs) -> None:
        # Get the parsed config
        agent_config = kwargs[name]

        # The portkey config is optional
        portkey_config = agent_config.get("portkey_on", None)

        # If the portkey config is not None or empty, we initialize the llm with the portkey config
        if portkey_config is not None or portkey_config != {}:
            logger.info(
                f"Initializing the llm with the portkey config: {portkey_config}"
            )
            agent_config["llm"] = init_portkey_llm(
                model=agent_config["llm"],
                portkey_config=portkey_config,
            )
            agent_config.pop("portkey_on")

        super().__init__(config=agent_config, *args, **kwargs)
