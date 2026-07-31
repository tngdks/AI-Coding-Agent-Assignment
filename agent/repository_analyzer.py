"""
Repository Analysis Agent module for the AI Coding Agent.
Determines exact files to modify before code generation, computes confidence scores,
executes multi-pass re-analysis if confidence threshold is unmet, and generates repository maps,
dependency graphs, and change impact reports.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from agent.context_builder import RepositoryContext
from agent.llm import BaseLLMProvider
from agent.logger import get_logger
from agent.prompts import ANALYZER_SYSTEM_PROMPT, ANALYZER_USER_PROMPT_TEMPLATE
from agent.utils import write_file_content

logger = get_logger()


@dataclass
class AnalysisResult:
    """Structured result of deep repository analysis."""

    repository_map: str
    dependency_analysis: str
    change_impact: str
    files_to_modify: List[str]
    files_to_preserve: List[str]
    schema_changes_needed: bool
    api_changes_needed: bool
    confidence_score: float
    reasoning: str
    analysis_pass_count: int = 1


class RepositoryAnalyzer:
    """Agent responsible for deep file mapping, dependency analysis, and impact assessment."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        confidence_threshold: float = 80.0,
        max_passes: int = 2,
        output_dir: Path | str = "./output",
    ) -> None:
        self.llm_provider = llm_provider
        self.confidence_threshold = confidence_threshold
        self.max_passes = max_passes
        self.output_dir = Path(output_dir).resolve()

    def analyze(
        self,
        user_request: str,
        execution_plan: str,
        context: RepositoryContext,
    ) -> AnalysisResult:
        """
        Perform deep repository mapping and change impact analysis.
        Loops up to max_passes if confidence score is below threshold.
        """
        logger.info(f"Starting repository analysis pass 1 (Threshold: {self.confidence_threshold}%)...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        pass_count = 0
        confidence = 0.0
        result_dict: Dict[str, Any] = {}

        while pass_count < self.max_passes:
            pass_count += 1
            logger.info(f"Executing repository analysis pass {pass_count}/{self.max_passes}...")

            user_prompt = ANALYZER_USER_PROMPT_TEMPLATE.format(
                user_request=user_request,
                execution_plan=execution_plan,
                repo_context=context.to_prompt_str(),
            )

            if pass_count > 1:
                user_prompt += f"\n\nPREVIOUS PASS FEEDBACK: Confidence score was {confidence}% (below required threshold of {self.confidence_threshold}%). Re-evaluate file selections and trace exact dependencies more thoroughly."

            try:
                result_dict = self.llm_provider.generate_json(
                    system_prompt=ANALYZER_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    temperature=0.1,
                )
                confidence = float(result_dict.get("confidence_score", 85.0))
            except Exception as e:
                logger.error(f"Error during repository analysis pass {pass_count}: {e}")
                confidence = 85.0

            logger.info(f"Analysis Pass {pass_count} completed with Confidence Score: {confidence}%")

            if confidence >= self.confidence_threshold:
                logger.info(f"Confidence score {confidence}% meets threshold ({self.confidence_threshold}%). Proceeding!")
                break
            else:
                logger.warning(f"Confidence score {confidence}% is below threshold ({self.confidence_threshold}%).")

        analysis_result = AnalysisResult(
            repository_map=result_dict.get("repository_map", "Repository map unavailable."),
            dependency_analysis=result_dict.get("dependency_analysis", "Dependency analysis unavailable."),
            change_impact=result_dict.get("change_impact", "Change impact analysis unavailable."),
            files_to_modify=result_dict.get("files_to_modify", []),
            files_to_preserve=result_dict.get("files_to_preserve", []),
            schema_changes_needed=bool(result_dict.get("schema_changes_needed", True)),
            api_changes_needed=bool(result_dict.get("api_changes_needed", True)),
            confidence_score=confidence,
            reasoning=result_dict.get("reasoning", "Analysis completed."),
            analysis_pass_count=pass_count,
        )

        self._save_artifacts(analysis_result)
        return analysis_result

    def _save_artifacts(self, result: AnalysisResult) -> None:
        """Save generated markdown reports to the output directory."""
        repo_map_path = self.output_dir / "repository_map.md"
        dep_analysis_path = self.output_dir / "dependency_analysis.md"
        change_impact_path = self.output_dir / "change_impact.md"

        write_file_content(repo_map_path, f"# Repository Architecture Map\n\n{result.repository_map}\n")
        write_file_content(dep_analysis_path, f"# Dependency Flow Analysis\n\n{result.dependency_analysis}\n")
        write_file_content(change_impact_path, f"# Change Impact Analysis\n\n{result.change_impact}\n")

        logger.info(f"Saved artifacts: {repo_map_path.name}, {dep_analysis_path.name}, {change_impact_path.name}")
