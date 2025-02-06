from crewai.memory.entity.entity_memory import EntityMemory
from cognition_core.memory.storage import ChromaRAGStorage


class CustomEntityMemory(EntityMemory):
    def __init__(
        self, host: str, port: int, collection_name: str, embedder_config=None
    ):
        storage = ChromaRAGStorage(host, port, collection_name, embedder_config)
        super().__init__(storage=storage)
