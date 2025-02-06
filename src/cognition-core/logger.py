from colorama import Fore, Style, init
from datetime import datetime
from typing import Optional
from pathlib import Path
import logging
import sys
import os


# Initialize colorama
init()
LOGGER_NAME = "COG"

# Define log levels
log_levels = {
    "CRITICAL": 50,
    "FATAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "WARN": 30,
    "INFO": 20,
    "DEBUG": 10,
    "NOTSET": 0,
}

# Get log level from environment variable first
env_log_level = os.getenv("APP_LOG_LEVEL", "INFO").upper()
DEFAULT_LOG_LEVEL = log_levels.get(env_log_level, logging.DEBUG)


class ColoredFormatter(logging.Formatter):
    """Custom formatter adding colors to log levels and messages"""

    COLORS = {
        "DEBUG": Fore.BLUE,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record):
        # Get the appropriate color
        color = self.COLORS.get(record.levelname, Fore.WHITE)

        # Color the entire message including timestamp and module name
        formatted_msg = super().format(record)
        return f"{color}{formatted_msg}{Style.RESET_ALL}"


class LoggerSetup:
    """Setup logging configuration for the entire application"""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LoggerSetup, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        log_level: int = DEFAULT_LOG_LEVEL,  # Use the environment-based default
        log_file: Optional[Path] = None,
        module_name: str = LOGGER_NAME,
    ):
        # Skip if already initialized
        if self._initialized:
            return

        self.log_file = log_file or Path(
            f"logs/{module_name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        self.module_name = module_name
        self.logger = logging.getLogger(module_name)
        self.logger.setLevel(log_level)  # Set the level during initialization

        # Prevent duplicate handlers
        self.logger.handlers = []

        self._setup_logger()
        LoggerSetup._initialized = True

    def _setup_logger(self) -> None:
        """Configure logger with console and file handlers"""
        self.logger.propagate = False  # Prevent propagation to root logger

        # Console handler with colored output
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )
        self.logger.addHandler(console_handler)

        # File handler
        try:
            self.log_file.parent.mkdir(exist_ok=True)
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")

    def get_logger(self) -> logging.Logger:
        """Get configured logger instance"""
        return self.logger


def setup_logger(
    module_name: str = LOGGER_NAME,
    log_level: int = DEFAULT_LOG_LEVEL,  # Use the environment-based default
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Utility function to get a configured logger"""
    logger_setup = LoggerSetup(
        log_level=log_level, log_file=log_file, module_name=module_name
    )
    return logger_setup.get_logger()


# Initialize default logger with environment-based level
logger = setup_logger(log_level=DEFAULT_LOG_LEVEL)
