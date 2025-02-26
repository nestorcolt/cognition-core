from unittest.mock import MagicMock
from cognition_core.agent import CognitionAgent
from cognition_core.tools.tool_svc import ToolService
from pathlib import Path
import yaml
import os


class TestCognitionAgent:
    def test_initialization(self):
        """Test that CognitionAgent initializes correctly with default values."""
        # Arrange & Act
        agent = CognitionAgent(
            name="test_agent",
            role="Test Role",
            goal="Test Goal",
            backstory="Test Backstory",
        )

        # Assert
        assert agent.name == "test_agent"
        assert agent.enabled is True
        assert agent.role == "Test Role"
        assert agent.goal == "Test Goal"
        assert agent.backstory == "Test Backstory"
        assert agent.tool_names == []
        assert agent.tool_service is None

    def test_with_tools(self):
        """Test that CognitionAgent can be initialized with tools."""
        # Arrange
        mock_tool_service = MagicMock(spec=ToolService)
        tool_names = ["tool1", "tool2"]

        # Act
        agent = CognitionAgent(
            name="tool_agent",
            role="Tool User",
            goal="Use tools",
            backstory="I use tools",
            tool_names=tool_names,
            tool_service=mock_tool_service,
            enabled=False,
        )

        # Assert
        assert agent.name == "tool_agent"
        assert agent.enabled is False
        assert agent.tool_names == tool_names
        assert agent.tool_service == mock_tool_service

    def test_from_yaml_config(self):
        """Test creating agents from YAML configuration."""
        # Arrange
        # Use __file__ to get the current test file's directory
        current_dir = Path(__file__).parent
        config_path = current_dir / "agents.yaml"

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Act
        manager_agent = CognitionAgent(
            name="manager",
            role=config["manager"]["role"],
            goal=config["manager"]["goal"].format(message="Test message"),
            backstory=config["manager"]["backstory"],
            llm=config["manager"]["llm"],
            max_tokens=config["manager"]["max_tokens"],
            max_iter=config["manager"]["max_iter"],
        )

        analyzer_agent = CognitionAgent(
            name="analyzer",
            role=config["analyzer"]["role"],
            goal=config["analyzer"]["goal"].format(message="Test message"),
            backstory=config["analyzer"]["backstory"],
            llm=config["analyzer"]["llm"],
            max_tokens=config["analyzer"]["max_tokens"],
            max_iter=config["analyzer"]["max_iter"],
        )

        # Assert
        assert manager_agent.name == "manager"
        assert manager_agent.role == "Strategic Manager"
        assert "Test message" in manager_agent.goal

        # Skip LLM assertion - it's an object without a simple way to check the model

        assert analyzer_agent.name == "analyzer"
        assert analyzer_agent.role == "Analysis Specialist"
        assert "Test message" in analyzer_agent.goal

        # Skip LLM assertion - it's an object without a simple way to check the model
