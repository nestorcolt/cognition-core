from portkey_ai import createHeaders, PORTKEY_GATEWAY_URL
from typing import Dict, Any
from crewai import LLM
import os


def init_portkey_llm(
    model: str,
    portkey_virtual_key: str,
    portkey_config: Dict[str, Any] = None,
    trace_id: str = "cognition_agent",
) -> LLM:
    """Initialize LLM with Portkey integration"""

    # Get API keys from environment variables
    portkey_api_key = os.getenv("PORTKEY_API_KEY")
    virtual_key = os.getenv(portkey_virtual_key)

    if not portkey_api_key or not virtual_key:
        raise ValueError(
            "PORTKEY_API_KEY and PORTKEY_VIRTUAL_KEY must be set in environment variables"
        )

    # Configure LLM with Portkey integration
    llm = LLM(
        model=model,
        base_url=PORTKEY_GATEWAY_URL,
        api_key="dummy",  # Using Virtual key instead
        extra_headers=createHeaders(
            api_key=portkey_api_key,
            virtual_key=virtual_key,
            config=portkey_config,
            trace_id=trace_id,
        ),
    )

    return llm
