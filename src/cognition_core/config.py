from watchdog.events import FileSystemEventHandler
from crewai.utilities.paths import db_storage_path
from pydantic import BaseModel, ValidationError
from cognition_core.logger import logger
from watchdog.observers import Observer
from contextlib import contextmanager
from typing import Dict, Any, Type
from pathlib import Path
import subprocess
import threading
import shutil
import yaml
import time
import os


class ConfigValidationError(Exception):
    pass


class ConfigSchema(BaseModel):
    version: str
    environment: str


class ConfigManager:
    def __init__(self):
        self.reload_timeout = float(os.environ.get("CONFIG_RELOAD_TIMEOUT", "0.1"))
        self.last_reload = {}
        self.storage_dir = Path(db_storage_path()).resolve()
        self._cache = {}

        # Clone remote repo if specified
        remote_config = os.environ.get("COGNITION_CONFIG_SOURCE")

        if remote_config:
            clone_result = self._setup_remote_config(remote_config)
            if not clone_result:
                logger.error("Failed to clone remote config")

        # Set config directory (either local or within cloned repo)
        config_dir = os.environ.get("COGNITION_CONFIG_DIR")

        if config_dir:
            # Expand tilde to handle home directory paths
            self.config_dir = Path(os.path.expanduser(config_dir))

            if not self.config_dir.exists():
                logger.warning(f"Config directory not found: {self.config_dir}")
                self.config_dir = None
        else:
            logger.warning("No config directory set, will use CrewAI defaults")
            self.config_dir = None
        
        # Setup hot reload if we have a config directory
        if self.config_dir:
            self._setup_hot_reload()
            self._load_configs()

    def _load_configs(self):
        """Load all YAML configs from config directory"""
        for config_file in self.config_dir.glob("*.yaml"):
            logger.debug(f"Loading config file: {config_file}")
            self._load_file(config_file)
            
    def _setup_remote_config(self, remote_url: str) -> Path:
        """Clone remote config repository"""
        try:
            home_dir = Path.home()
            config_dir = home_dir / ".cognition"

            logger.info(f"Cloning config from {remote_url} to {config_dir}")

            if config_dir.exists():
                logger.info(f"Removing existing config directory: {config_dir}")
                shutil.rmtree(config_dir)

            result = subprocess.run(
                ["git", "clone", remote_url, str(config_dir)],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                raise Exception(f"Git clone failed: {result.stderr}")

            logger.info(f"Successfully cloned config to {config_dir}")
            return config_dir

        except Exception as e:
            logger.error(f"Failed to setup remote config: {e}")
            return None

    def _refresh_remote_config(self):
        """Update remote config as part of hot reload"""
        if not self.config_dir or "cognition_config" not in str(self.config_dir):
            return

        try:
            logger.info("Refreshing remote config")
            result = subprocess.run(
                ["git", "pull"], cwd=self.config_dir, capture_output=True, text=True
            )
            if result.returncode == 0:
                self._load_configs()  # Reload after pull
            else:
                logger.error(f"Failed to pull remote config: {result.stderr}")
        except Exception as e:
            logger.error(f"Error refreshing remote config: {e}")

    def get_db_password(self) -> str:
        password = os.getenv("LONG_TERM_DB_PASSWORD")
        if not password:
            raise ValueError("LONG_TERM_DB_PASSWORD environment variable is not set")
        return password

    def get_chroma_password(self) -> str:
        password = os.getenv("CHROMA_PASSWORD")
        if not password:
            raise ValueError("CHROMA_PASSWORD environment variable is not set")
        return password

    def _setup_hot_reload(self):
        event_handler = ConfigReloader(self)
        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.config_dir), recursive=False)
        self.observer.start()

    def __del__(self):
        if hasattr(self, "observer"):
            self.observer.stop()
            self.observer.join()

    def _load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load and parse a single config file with debouncing"""
        current_time = time.time()
        last_reload = self.last_reload.get(file_path, 0)

        # More permissive debouncing
        if (
            current_time - last_reload < self.reload_timeout
            and file_path.stem in self._cache
        ):
            return self._cache[file_path.stem]

        try:
            with file_path.open() as f:
                config = yaml.safe_load(f)

                # Additional validation
                if config is None:
                    raise ConfigValidationError(f"Empty config file: {file_path}")
                if not isinstance(config, dict):
                    raise ConfigValidationError(
                        f"Invalid YAML structure in {file_path}"
                    )

                # Force cache update
                self._cache[file_path.stem] = config
                self.last_reload[file_path] = current_time
                return config
            
        except (yaml.YAMLError, OSError) as e:
            logger.error(f"Error loading config {file_path}: {str(e)}")

            if file_path.stem in self._cache:
                return self._cache[file_path.stem]  # Return last valid config
            
            raise ConfigValidationError(
                f"Config loading error in {file_path}: {str(e)}"
            )

    def validate_config(self, config_name: str, schema: Type[BaseModel]) -> None:
        try:
            schema(**self.get_config(config_name))
        except ValidationError as e:
            raise ConfigValidationError(f"Invalid config {config_name}: {str(e)}")

    def get_config(self, name: str, validate: bool = True) -> Dict[str, Any]:
        """Get config with retry mechanism"""
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            try:
                config = self._cache.get(name)

                if config is None:
                    raise KeyError(f"Configuration '{name}' not found")

                if validate:
                    config = EnvManager.override_config(config)
                return config
            
            except Exception as e:
                if attempt == max_retries - 1:
                    raise

                time.sleep(retry_delay)
                continue

    def get_nested_value(self, config_name: str, path: str, default: Any = None) -> Any:
        """Get nested config value using dot notation (e.g. 'database.host')"""
        config = self.get_config(config_name)
        keys = path.split(".")

        for key in keys:
            if not isinstance(config, dict):
                return default
            config = config.get(key, default)
        return config

    @contextmanager
    def config_scope(self):
        """Context manager for safe config handling"""
        try:
            yield self
        finally:
            self.observer.stop()
            self.observer.join()

    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory-specific configuration"""
        try:
            config = self.get_config("memory", validate=False)

            if not config:
                logger.warning("Custom memory configuration is empty")

            return EnvManager.override_config(config, prefix="CREW_MEMORY_")

        except KeyError:
            logger.warning("Memory configuration not found")

    def get_portkey_config(self) -> Dict[str, Any]:
        """Get Portkey-specific configuration"""
        try:
            config = self.get_config("portkey", validate=False)
            if not config:
                return {
                    "cache": {
                        "mode": "semantic",
                    },
                    "metadata": {"environment": "development", "project": "cognition"},
                }
            return EnvManager.override_config(config, prefix="PORTKEY_")
        except KeyError:
            return {
                "cache": {
                    "mode": "semantic",
                },
                "metadata": {"environment": "development", "project": "cognition"},
            }


class EnvManager:
    @staticmethod
    def get_env_value(key: str, default: Any = None) -> Any:
        return os.environ.get(key, default)

    @staticmethod
    def override_config(config: dict, prefix: str = "CREW_") -> dict:
        for key in config:
            env_key = f"{prefix}{key.upper()}"
            if env_key in os.environ:
                config[key] = os.environ[env_key]
        return config


class ConfigReloader(FileSystemEventHandler):
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.lock = threading.Lock()

    def on_modified(self, event):
        if not event.src_path.endswith(".yaml"):
            return

        with self.lock:
            try:
                path = Path(event.src_path)
                # Force reload by clearing last reload time
                self.config_manager.last_reload[path] = 0
                self.config_manager._load_file(path)
            except Exception as e:
                logger.error(f"Error reloading config: {str(e)}")


# Create the singleton instance
config_manager = ConfigManager()

# Export only the singleton instance
__all__ = ["config_manager"]
