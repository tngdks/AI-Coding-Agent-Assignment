"""
Planning Agent module for the AI Coding Agent.
Analyzes the repository context and user request to generate a comprehensive execution plan
including assumptions, risks, implementation order, rollback plan, estimated complexity, and confidence score,
saved automatically to output/plan.md.
"""

from pathlib import Path

from agent.context_builder import RepositoryContext
from agent.llm import BaseLLMProvider
from agent.logger import get_logger
from agent.prompts import PLANNER_SYSTEM_PROMPT, PLANNER_USER_PROMPT_TEMPLATE
from agent.utils import write_file_content

logger = get_logger()


class PlanningAgent:
    """Agent responsible for formulating architectural implementation plans."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        output_dir: Path | str = "./output",
    ) -> None:
        self.llm_provider = llm_provider
        self.output_dir = Path(output_dir).resolve()

    def plan(
        self,
        user_request: str,
        context: RepositoryContext,
    ) -> str:
        """
        Formulate high-level implementation plan based on repository context.

        Args:
            user_request: High-level user goal.
            context: RepositoryContext instance.

        Returns:
            Plan markdown string.
        """
        logger.info(f"Generating execution plan for request: '{user_request}'")

        formatted_user_prompt = PLANNER_USER_PROMPT_TEMPLATE.format(
            user_request=user_request,
            repo_context=context.to_prompt_str(),
        )

        plan_markdown = self.llm_provider.generate(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=formatted_user_prompt,
            temperature=0.2,
        )

        self.output_dir.mkdir(parents=True, exist_ok=True)
        plan_file_path = self.output_dir / "plan.md"
        write_file_content(plan_file_path, plan_markdown)

        logger.info(f"Execution plan successfully saved to: {plan_file_path}")
        return plan_markdown
