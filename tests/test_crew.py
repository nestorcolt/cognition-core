from cognition_core.crew import CognitionCrew, CognitionCoreCrewBase
from crewai.project import crew, agent, task
from cognition_core.agent import CognitionAgent
from cognition_core.task import CognitionTask
from cognition_core.agent import CognitionAgent
from cognition_core.llm import init_portkey_llm
from crewai.project import CrewBase, agent, task, crew, before_kickoff, after_kickoff


@CognitionCoreCrewBase
class mock_crew_base:

    agents_config = "agents.yaml"
    tasks_config = "tasks.yaml"

    @agent
    def analyzer(self) -> CognitionAgent:
        """Analysis specialist agent"""
        llm = init_portkey_llm(
            model=self.agents_config["analyzer"]["llm"],
            portkey_config=self.portkey_config,
        )
        return self.get_cognition_agent(config=self.agents_config["analyzer"], llm=llm)

    @task
    def analysis_task(self) -> CognitionTask:
        """Input analysis task"""
        task_config = self.tasks_config["analysis_task"]
        return CognitionTask(
            name="analysis_task",
            config=task_config,
            tool_names=self.list_tools(),
            tool_service=self.tool_service,
        )

    @crew
    def crew(self) -> CognitionCrew:
        return CognitionCrew(
            agents=self.agents,
            tasks=self.tasks,
            memory=False,
            verbose=True,
            # embedder=self.memory_service.embedder,
            # tool_service=self.tool_service,
            # short_term_memory=self.memory_service.get_short_term_memory(),
            # entity_memory=self.memory_service.get_entity_memory(),
            # long_term_memory=self.memory_service.get_long_term_memory(),
        )


class TestCognitionCrew:
    def test_initialization(self):
        """Test that CognitionCrew initializes correctly with default values."""

        crew_mock = mock_crew_base().crew()

        # Assert
        assert crew_mock.tasks != []
        assert crew_mock.agents != []
        assert crew_mock.process == "sequential"
        assert crew_mock.verbose is True
        assert crew_mock.tool_service is None
        assert crew_mock.tools_handler is None
