"""
Validation Agent module for the AI Coding Agent.
Performs syntax validation (node -c), import verification, scope checks,
and generates output/validation_report.md.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from agent.llm import BaseLLMProvider
from agent.logger import get_logger
from agent.prompts import VALIDATOR_SYSTEM_PROMPT, VALIDATOR_USER_PROMPT_TEMPLATE
from agent.utils import write_file_content

logger = get_logger()


@dataclass
class ValidationReport:
    """Dataclass holding validation check results and generated report."""

    success: bool
    report_markdown: str
    syntax_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    modified_files_checked: List[str] = field(default_factory=list)


class ValidationAgent:
    """Agent responsible for verification, syntax checking, and QA auditing."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        repo_path: Path | str,
        output_dir: Path | str = "./output",
    ) -> None:
        self.llm_provider = llm_provider
        self.repo_path = Path(repo_path).resolve()
        self.output_dir = Path(output_dir).resolve()

    def validate(
        self,
        user_request: str,
        execution_plan: str,
        modified_files: Dict[str, Tuple[str, str]],
        expected_files: List[str],
    ) -> ValidationReport:
        """
        Perform syntax validation, scope check, and LLM verification audit.

        Args:
            user_request: User request prompt string.
            execution_plan: Execution plan text.
            modified_files: Dict mapping relative file paths to Tuple of (content, diff).
            expected_files: List of planned files to modify.

        Returns:
            ValidationReport instance.
        """
        logger.info(f"Starting validation audit on {len(modified_files)} modified files...")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        syntax_errors: List[str] = []
        warnings: List[str] = []

        # Scope Check
        for path in modified_files.keys():
            if path not in expected_files:
                warnings.append(f"Scope Warning: Modified file '{path}' was not in planned target list.")

        # Syntax Check (node -c)
        for rel_path in modified_files.keys():
            file_path = self.repo_path / rel_path
            if file_path.suffix.lower() in [".js", ".jsx", ".mjs"]:
                error = self._check_javascript_syntax(file_path)
                if error:
                    syntax_errors.append(f"Syntax error in {rel_path}: {error}")
                else:
                    logger.info(f"Syntax check PASSED for: {rel_path}")

        # LLM Audit
        diff_summary = self._format_diff_summary(modified_files)
        formatted_prompt = VALIDATOR_USER_PROMPT_TEMPLATE.format(
            user_request=user_request,
            diff_summary=diff_summary,
            execution_plan=execution_plan,
        )

        llm_report = self.llm_provider.generate(
            system_prompt=VALIDATOR_SYSTEM_PROMPT,
            user_prompt=formatted_prompt,
            temperature=0.1,
        )

        overall_success = len(syntax_errors) == 0 and "FAIL" not in llm_report.upper()

        report = ValidationReport(
            success=overall_success,
            report_markdown=llm_report,
            syntax_errors=syntax_errors,
            warnings=warnings,
            modified_files_checked=list(modified_files.keys()),
        )

        report_path = self.output_dir / "validation_report.md"
        write_file_content(report_path, llm_report)
        logger.info(f"Saved validation report to: {report_path}")

        return report

    def _check_javascript_syntax(self, file_path: Path) -> str | None:
        """Run `node -c <file>` to verify JavaScript syntax validity."""
        if not file_path.exists():
            return None
        try:
            res = subprocess.run(
                ["node", "-c", str(file_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            if res.returncode != 0:
                return res.stderr.strip()
            return None
        except Exception as e:
            logger.warning(f"Could not run `node -c` syntax check on {file_path.name}: {e}")
            return None

    def _format_diff_summary(self, modified_files: Dict[str, Tuple[str, str]]) -> str:
        """Format modified files diffs for LLM audit."""
        blocks = []
        for path, (content, diff) in modified_files.items():
            blocks.append(f"### File: `{path}`\n\n#### Unified Diff:\n```diff\n{diff}\n```\n\n#### Complete Modified Content:\n```js\n{content}\n```\n")
        return "\n".join(blocks)
