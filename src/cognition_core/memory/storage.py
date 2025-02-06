from crewai.utilities import EmbeddingConfigurator
from crewai.utilities.paths import db_storage_path
from typing import Any, Dict, List, Optional
from chromadb.config import Settings
from chromadb.api import ClientAPI
import chromadb
import contextlib
import logging
import shutil
import uuid
import io


@contextlib.contextmanager
def suppress_logging(
    logger_name="chromadb.segment.impl.vector.local_persistent_hnsw",
    level=logging.ERROR,
):
    logger = logging.getLogger(logger_name)
    original_level = logger.getEffectiveLevel()
    logger.setLevel(level)
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.suppress(UserWarning),
    ):
        yield
    logger.setLevel(original_level)


class ChromaRAGStorage:
    """
    Storage class to handle embeddings for memory entries using ChromaDB.
    """

    app: ClientAPI | None = None

    def __init__(
        self, host: str, port: int, collection_name: str, embedder_config=None
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedder_config = embedder_config
        self._initialize_app()

    def _set_embedder_config(self):
        configurator = EmbeddingConfigurator()
        self.embedder_config = configurator.configure_embedder(self.embedder_config)

    def _initialize_app(self):
        self._set_embedder_config()
        print(f"Initializing ChromaDB client: HttpClient")
        try:
            chroma_client = chromadb.HttpClient(
                host=self.host, port=self.port, settings=Settings(allow_reset=True)
            )
        except Exception as e:
            raise Exception(
                f"Failed to connect to ChromaDB at {self.host}:{self.port}: {e}"
            )

        self.app = chroma_client
        self.collection = self.app.get_or_create_collection(
            name=self.collection_name, embedding_function=self.embedder_config
        )

    def save(self, value: Any, metadata: Dict[str, Any]) -> None:
        if not hasattr(self, "app") or not hasattr(self, "collection"):
            self._initialize_app()
        try:
            self._generate_embedding(value, metadata)
        except Exception as e:
            logging.error(f"Error during save to {self.collection_name}: {str(e)}")

    def search(
        self,
        query: str,
        limit: int = 3,
        filter: Optional[dict] = None,
        score_threshold: float = 0.35,
    ) -> List[Any]:
        if not hasattr(self, "app"):
            self._initialize_app()

        try:
            with suppress_logging():
                response = self.collection.query(query_texts=query, n_results=limit)

            results = []
            for i in range(len(response["ids"][0])):
                result = {
                    "id": response["ids"][0][i],
                    "metadata": response["metadatas"][0][i],
                    "context": response["documents"][0][i],
                    "score": response["distances"][0][i],
                }
                if result["score"] >= score_threshold:
                    results.append(result)

            return results
        except Exception as e:
            logging.error(f"Error during search in {self.collection_name}: {str(e)}")
            return []

    def _generate_embedding(self, text: str, metadata: Dict[str, Any]) -> None:
        if not hasattr(self, "app") or not hasattr(self, "collection"):
            self._initialize_app()

        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())],
        )

    def reset(self) -> None:
        try:
            if self.app:
                self.app.reset()
                shutil.rmtree(f"{db_storage_path()}/{self.collection_name}")
                self.app = None
                self.collection = None
        except Exception as e:
            if "attempt to write a readonly database" in str(e):
                # Ignore this specific error
                pass
            else:
                raise Exception(
                    f"An error occurred while resetting {self.collection_name} memory: {e}"
                )
