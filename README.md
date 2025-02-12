# Cognition Core

Core integration package for building AI agents with CrewAI, providing configuration management, memory systems, tool integration, and API capabilities.

## Architecture
![Cognition AI](./designs/cognition-core.jpg)
```
cognition-core/
├── src/
│   └── cognition_core/
│       ├── api.py              # Core API implementation
│       ├── crew.py             # Enhanced CrewAI base
│       ├── agent.py            # Enhanced Agent class
│       ├── task.py             # Enhanced Task class
│       ├── llm.py              # Portkey LLM integration
│       ├── logger.py           # Logging system
│       ├── config.py           # Configuration management
│       ├── memory/             # Memory implementations
│       │   ├── entity.py       # Entity memory with Chroma
│       │   ├── long_term.py    # PostgreSQL long-term memory
│       │   ├── short_term.py   # Chroma short-term memory
│       │   ├── storage.py      # ChromaDB storage implementation
│       │   └── mem_svc.py      # Memory service orchestration
│       └── tools/              # Tool management
│           ├── custom_tool.py  # Base for custom tools
│           └── tool_svc.py     # Dynamic tool service
```


## Core Features

### 1. Enhanced Crew Base
- Automatic API capability through `@CognitionCoreCrewBase` decorator
- Integrated tool service management
- Memory system initialization
- Configuration management
- Portkey LLM integration

### 2. Memory Systems
- **Short-term Memory**: ChromaDB-based implementation
- **Long-term Memory**: PostgreSQL-based storage
- **Entity Memory**: Relationship tracking with ChromaDB
- Configurable storage backends
- Embedder configuration support

### 3. Tool Integration
- Dynamic tool loading from HTTP endpoints
- Tool service with caching
- Async tool operations
- Tool refresh capability
- Structured tool definitions with Pydantic

### 4. API Integration
- Built-in FastAPI implementation
- Async task processing
- Health check endpoints
- Task status tracking
- Background task execution

### 5. Configuration Management
- Hot-reloading YAML configuration
- Environment variable integration
- Configurable paths
- Fallback to CrewAI defaults

## Environment Variables

Required:
- `PORTKEY_API_KEY`: API key for Portkey LLM routing
- `PORTKEY_VIRTUAL_KEY`: Virtual key for Portkey
- `COGNITION_CONFIG_DIR`: Path to your configuration directory (e.g., "/home/user/.cognition/cognition-config-demo/config")

Optional:
- `COGNITION_CONFIG_SOURCE`: Git repository URL to clone configuration (e.g., "git@github.com:user/config-repo.git")
  - If set, will clone the repository to ~/.cognition
  - `COGNITION_CONFIG_DIR` should then point to the config directory within the cloned repo
- `CONFIG_RELOAD_TIMEOUT`: Config reload timeout (default: 0.1)
- `LONG_TERM_DB_PASSWORD`: PostgreSQL database password
- `CHROMA_PASSWORD`: ChromaDB password
- `APP_LOG_LEVEL`: Logging level (default: INFO)

Note: When using remote configuration:
1. The repository will be cloned to ~/.cognition
2. Set `COGNITION_CONFIG_DIR` to point to the config directory within the cloned repository
3. Configuration is managed through a singleton pattern to prevent multiple clones/reloads

## Usage Example

```python
from cognition_core import CognitionCoreCrewBase
from crewai import Agent, Task

@CognitionCoreCrewBase
class YourCrew:
    @agent
    def researcher(self) -> Agent:
        return self.get_cognition_agent(
            config=self.agents_config["researcher"],
            llm=self.init_portkey_llm(
                model="gpt-4",
                portkey_config=self.portkey_config
            )
        )

    @task
    def research_task(self) -> Task:
        return CognitionTask(
            config=self.tasks_config["research"],
            tools=["calculator", "search"]
        )

    @crew
    def crew(self) -> Crew:
        return CognitionCrew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            tool_service=self.tool_service
        )

# Access API
app = YourCrew().api
```

## Configuration Files

### Memory Configuration (memory.yaml)
```yaml
short_term_memory:
  enabled: true
  external: true
  host: "localhost"
  port: 8000
  collection_name: "short_term"

long_term_memory:
  enabled: true
  external: true
  connection_string: "postgresql://user:${LONG_TERM_DB_PASSWORD}@localhost:5432/db"

entity_memory:
  enabled: true
  external: true
  host: "localhost"
  port: 8000
  collection_name: "entities"

embedder:
  provider: "ollama"
  config:
    model: "nomic-embed-text"
    vector_dimension: 384
```

### Tool Configuration (tools.yaml)
```yaml
tool_services:
  - name: "primary_service"
    enabled: true
    base_url: "http://localhost:8080/api/v1"
    endpoints:
      - path: "/tools"
        method: "GET"

settings:
  cache:
    enabled: true
    ttl: 3600
  validation:
    response_timeout: 30
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request with tests

## License

MIT