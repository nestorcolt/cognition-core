import pytest
import tempfile
import os
import yaml
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from cognition.config import (
    ConfigManager,
    ConfigValidationError,
    ConfigSchema,
    EnvManager,
)


class TestConfig(BaseModel):
    name: str
    value: int


@pytest.fixture
def temp_config_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)


@pytest.fixture
def config_manager(temp_config_dir):
    # Create a test config file
    test_config = {"version": "1.0", "environment": "test", "test_value": 42}

    config_path = temp_config_dir / "test.yaml"
    with config_path.open("w") as f:
        yaml.dump(test_config, f)

    with patch.dict(os.environ, {"CONFIG_DIR": str(temp_config_dir)}):
        manager = ConfigManager()
        yield manager
        # Cleanup
        manager.__del__()


def test_config_loading(config_manager):
    config = config_manager.get_config("test")
    assert config["version"] == "1.0"
    assert config["test_value"] == 42


def test_nested_value(config_manager):
    assert config_manager.get_nested_value("test", "version") == "1.0"
    assert (
        config_manager.get_nested_value("test", "nonexistent", default="default")
        == "default"
    )


def test_validation(config_manager):
    with pytest.raises(ConfigValidationError):
        config_manager.validate_config("test", TestConfig)


def test_hot_reload(config_manager, temp_config_dir):
    # Initial config
    initial_config = config_manager.get_config("test")
    assert initial_config["test_value"] == 42

    # Update config file
    new_config = {"version": "1.0", "environment": "test", "test_value": 100}

    config_path = temp_config_dir / "test.yaml"
    with config_path.open("w") as f:
        yaml.dump(new_config, f)

    # Wait for hot reload with multiple checks
    max_attempts = 10
    for _ in range(max_attempts):
        time.sleep(0.2)  # Shorter intervals, more attempts
        updated_config = config_manager.get_config("test")
        if updated_config["test_value"] == 100:
            break

    assert config_manager.get_config("test")["test_value"] == 100


def test_env_override(config_manager):
    with patch.dict(os.environ, {"CREW_TEST_VALUE": "200"}):
        config = config_manager.get_config("test")
        assert config["test_value"] == "200"


def test_missing_config():
    with tempfile.TemporaryDirectory() as tmpdirname:
        nonexistent_dir = Path(tmpdirname) / "nonexistent"
        with patch.dict(os.environ, {"CONFIG_DIR": str(nonexistent_dir)}):
            with pytest.raises(FileNotFoundError):
                ConfigManager()


def test_invalid_yaml(temp_config_dir):
    # Create invalid YAML file
    config_path = temp_config_dir / "invalid.yaml"
    with config_path.open("w") as f:
        f.write(
            "invalid:\n  - unclosed:\n    - list\n  missing: value"
        )  # More realistic invalid YAML

    with patch.dict(os.environ, {"CONFIG_DIR": str(temp_config_dir)}):
        with pytest.raises(ConfigValidationError) as exc_info:
            ConfigManager()
        assert "Config loading error" in str(exc_info.value)


def test_password_getters(config_manager):
    with patch.dict(
        os.environ,
        {"LONG_TERM_DB_PASSWORD": "db_pass", "CHROMA_PASSWORD": "chroma_pass"},
    ):
        assert config_manager.get_db_password() == "db_pass"
        assert config_manager.get_chroma_password() == "chroma_pass"


def test_missing_passwords(config_manager):
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            config_manager.get_db_password()
        with pytest.raises(ValueError):
            config_manager.get_chroma_password()


def test_config_scope(config_manager):
    with config_manager.config_scope() as cm:
        assert cm.get_config("test")["version"] == "1.0"

    # Verify observer is stopped after context
    assert not config_manager.observer.is_alive()


@pytest.mark.parametrize(
    "config_name,prefix,expected",
    [
        ("memory", "CREW_MEMORY_", {}),
        (
            "portkey",
            "PORTKEY_",
            {
                "cache": {"mode": "semantic"},
                "metadata": {"environment": "development", "project": "cognition"},
            },
        ),
    ],
)
def test_specific_configs(config_manager, config_name, prefix, expected):
    method = getattr(config_manager, f"get_{config_name}_config")
    result = method()
    if expected:
        assert result == expected
