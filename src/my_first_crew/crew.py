from crewai import Crew

from my_first_crew.dynamic_crew import DEFAULT_MODEL, build_managed_crew, load_agent_blueprints


class MyFirstCrew:
    """Factory for the managed multi-agent demo."""

    def crew(
        self,
        user_task: str = "Giai thich RAG la gi va Ollama dung de lam gi?",
        model: str = DEFAULT_MODEL,
    ) -> Crew:
        return build_managed_crew(
            user_task=user_task,
            blueprints=load_agent_blueprints(),
            model=model,
        )
