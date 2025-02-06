from crewai.memory.short_term.short_term_memory import ShortTermMemory
from cognition_core.memory.storage import ChromaRAGStorage


class CustomShortTermMemory(ShortTermMemory):
    def __init__(
        self, host: str, port: int, collection_name: str, embedder_config=None
    ):
        storage = ChromaRAGStorage(host, port, collection_name, embedder_config)
        super().__init__(storage=storage)
