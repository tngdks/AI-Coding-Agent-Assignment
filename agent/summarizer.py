"""
Summarizer module for the AI Coding Agent.
Generates an executive execution summary detailing files modified, features implemented,
key design decisions, architecture impact, limitations, and future enhancements roadmap,
saving output to output/summary.md.
"""

from pathlib import Path
from typing import Dict, Tuple

from agent.llm import BaseLLMProvider
from agent.logger import get_logger
from agent.prompts import SUMMARIZER_SYSTEM_PROMPT, SUMMARIZER_USER_PROMPT_TEMPLATE
from agent.utils import write_file_content
from agent.validator import ValidationReport

logger = get_logger()


class Summarizer:
    """Agent responsible for compiling final executive execution summaries."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        output_dir: Path | str = "./output",
    ) -> None:
        self.llm_provider = llm_provider
        self.output_dir = Path(output_dir).resolve()

    def summarize(
        self,
        user_request: str,
        modified_files: Dict[str, Tuple[str, str]],
        validation_report: ValidationReport,
    ) -> str:
        """
        Generate executive summary of changes made.

        Args:
            user_request: User prompt string.
            modified_files: Dict mapping relative file paths to Tuple of (content, diff).
            validation_report: ValidationReport instance.

        Returns:
            Summary markdown string.
        """
        logger.info("Generating executive execution summary...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        modified_files_list = "\n".join([f"- `{path}`" for path in modified_files.keys()])

        formatted_prompt = SUMMARIZER_USER_PROMPT_TEMPLATE.format(
            user_request=user_request,
            modified_files_list=modified_files_list,
            validation_report=validation_report.report_markdown,
        )

        summary_markdown = self.llm_provider.generate(
            system_prompt=SUMMARIZER_SYSTEM_PROMPT,
            user_prompt=formatted_prompt,
            temperature=0.2,
        )

        summary_path = self.output_dir / "summary.md"
        write_file_content(summary_path, summary_markdown)
        logger.info(f"Execution summary saved to: {summary_path}")

        return summary_markdown
