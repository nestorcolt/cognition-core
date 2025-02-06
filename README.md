# Cognition Core

Core integration package for building AI agents with CrewAI, providing configuration management, memory systems, and tool integration.

## Architecture
![Cognition AI](./designs/cognition-core.jpg)
```
cognition-core/
├── config/                  # Configuration files
│   ├── agents.yaml         # Agent definitions
│   ├── crew.yaml          # Crew settings
│   ├── memory.yaml        # Memory configuration
│   ├── portkey.yaml       # LLM routing
│   ├── tasks.yaml         # Task definitions
│   └── tools.yaml         # Tool configuration
├── memory/                 # Memory implementations
│   ├── entity.py          # Entity memory
│   ├── long_term.py       # Long-term storage
│   ├── short_term.py      # Short-term memory
│   ├── storage.py         # Storage interfaces
│   └── mem_svc.py         # Memory service
├── tools/                  # Tool management
│   ├── custom_tool.py     # Custom tool base
│   ├── tool_svc.py        # Tool service
│   └── __init__.py
└── crew.py                # Core crew base class
```

## Features

### Configuration Management
- Hot-reloading YAML configuration
- Environment variable integration
- Centralized settings management

### Memory Systems
- Short-term memory (Redis)
- Long-term memory (Firestore)
- Entity memory for relationship tracking
- Configurable storage backends

### Tool Integration
- Tool registry and service
- API wrapper utilities
- Configuration-driven tool management

### LLM Integration
- Portkey routing and monitoring 
- Multi-model support
- Performance optimization

## Installation

```bash
pip install cognition-core
```

## Quick Start

```python
from cognition_core import CognitionCoreCrewBase
from crewai import Agent, Task, Crew

class YourCrew(CognitionCoreCrewBase):
    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            llm=self.init_portkey_llm(
                model="gpt-4",
                portkey_config=self.portkey_config
            ),
            verbose=True
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            verbose=True
        )
```

## Configuration

Example YAML configuration:

```yaml
# memory.yaml
short_term_memory:
  enabled: true
  external: true
  host: "redis.example.com"
  port: 6379

long_term_memory:
  enabled: true
  external: true
  connection_string: "${LONG_TERM_DB_CONNECTION_STRING}"
```

## Environment Variables

Required variables:
- `PORTKEY_API_KEY`: Portkey API key
- `PORTKEY_VIRTUAL_KEY`: Portkey virtual key
- `LONG_TERM_DB_PASSWORD`: Long-term storage password
- `CONFIG_DIR`: Configuration directory path (default: src/cognition-core/config)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with tests

## License

MIT