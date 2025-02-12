from cognition_core.memory.short_term import CustomShortTermMemory
from crewai.memory.long_term.long_term_memory import LongTermMemory
from cognition_core.memory.long_term import CustomLongTermMemory
from crewai.memory.entity.entity_memory import EntityMemory
from cognition_core.memory.entity import CustomEntityMemory
from cognition_core.memory.short_term import ShortTermMemory
from cognition_core.config import ConfigManager
from cognition_core.logger import logger
import logging

logger = logger.getChild(__name__)
logger.setLevel(logging.DEBUG)


class MemoryService:
    """
    Memory Service that provides CrewAI memory configuration with all memory components
    """

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.memory_config = {}
        self.embedder = {
            "provider": "openai",
            "config": {
                "model": "text-embedding-3-small",
            },
        }

        self._initialize_config()

    def get_storage_path(self) -> str:
        """Get the storage path for memory data"""
        logger.debug(f"Storage Path Requested: {self.storage_path}")
        return self.storage_path

    def _initialize_config(self):
        """Initialize memory configuration"""
        self.memory_config = self.config_manager.get_memory_config()
        self.storage_path = self.config_manager.storage_dir
        logger.debug(f"Memory Storage Path: {self.storage_path}")

        if self.memory_config is None:
            logger.warning("No memory configuration found")
            return

        if not self.memory_config.get("embedder"):
            msg = "No embedder configuration found --  Assign Ollama embedder config"
            logger.error(msg)
            raise ValueError(msg)

        self.embedder = self.memory_config.get("embedder", self.embedder)

        logger.debug(f"Embedder: {self.embedder}")

    def __init_default_long_term_memory(self) -> LongTermMemory:
        """Initialize default long term memory configuration"""
        return LongTermMemory()

    def __init_default_short_term_memory(self):
        """Initialize default short term memory configuration"""
        return ShortTermMemory(embedder_config=self.get_embedder_config())

    def __init_default_entity_memory(self):
        """Initialize default entity memory configuration"""
        return EntityMemory(embedder_config=self.get_embedder_config())

    def get_long_term_memory(self):
        """Get long term memory configuration"""
        settings = self.memory_config.get("long_term_memory", {})

        if settings is None:
            logger.debug("Long term memory configuration deactivated")
            return

        is_active = settings.get("enabled", False)
        is_external = settings.get("external", False)

        if not is_active:
            logger.debug("Long term memory configuration deactivated")
            return

        if is_active and is_external:
            # upstream connection string
            connection_string = settings.get("connection_string", None)

            if connection_string is None:
                logger.error(
                    "Connection string for external long term memory not found"
                )
                return

            # replace the password with the actual password
            connection_string = connection_string.replace(
                "your_password", self.config_manager.get_db_password()
            )

            memory = CustomLongTermMemory(connection_string)
            logger.debug(f"Long term memory: {memory.__class__.__name__}")
            return memory

        if is_active and not is_external:
            # downstream sqlite storage
            logger.debug("Long term memory default configuration activated")
            return self.__init_default_long_term_memory()

    def get_short_term_memory(self):
        """Get short term memory configuration"""
        settings = self.memory_config.get("short_term_memory", {})

        if settings is None:
            logger.debug("Short term memory configuration deactivated")
            return

        is_active = settings.get("enabled", False)
        is_external = settings.get("external", False)

        if not is_active:
            logger.debug("Short term memory configuration deactivated")
            return

        if is_active and is_external:
            host = settings.get("host")
            port = settings.get("port")
            collection_name = settings.get("collection_name", "short_term")

            if not all([host, port]):
                logger.error("Short term memory configuration incomplete")
                return

            memory = CustomShortTermMemory(
                host=host,
                port=port,
                collection_name=collection_name,
                embedder_config=self.get_embedder_config(),
            )
            logger.debug(f"Short term memory: {memory.__class__.__name__}")
            return memory

        return self.__init_default_short_term_memory()

    def get_entity_memory(self):
        """Get entity memory configuration"""
        settings = self.memory_config.get("entity_memory", {})

        if settings is None:
            logger.debug("Entity memory configuration deactivated")
            return

        is_active = settings.get("enabled", False)
        is_external = settings.get("external", False)

        if not is_active:
            logger.debug("Entity memory configuration deactivated")
            return

        if is_active and is_external:
            host = settings.get("host")
            port = settings.get("port")
            collection_name = settings.get("collection_name", "entities")

            if not all([host, port]):
                logger.error("Entity memory configuration incomplete")
                return

            memory = CustomEntityMemory(
                host=host,
                port=port,
                collection_name=collection_name,
                embedder_config=self.get_embedder_config(),
            )
            logger.debug(f"Entity memory: {memory.__class__.__name__}")
            return memory

        return self.__init_default_entity_memory()

    def get_embedder_config(self):
        """Get embedder configuration"""
        embedder_settings = self.memory_config.get("embedder", self.embedder)
        return embedder_settings
