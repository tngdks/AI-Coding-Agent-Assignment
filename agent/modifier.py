"""
Code Modifier module for the AI Coding Agent.
Safely reads target files, generates targeted code modifications, computes unified diffs,
validates syntax before writing, and supports dry-run mode.
"""

import re
from pathlib import Path
from typing import Dict, Tuple

from agent.context_builder import RepositoryContext
from agent.llm import BaseLLMProvider
from agent.logger import get_logger
from agent.prompts import MODIFIER_SYSTEM_PROMPT, MODIFIER_USER_PROMPT_TEMPLATE
from agent.tools import check_syntax, generate_diff
from agent.utils import read_file_content, write_file_content

logger = get_logger()


class CodeModifier:
    """Agent responsible for applying targeted, safe code modifications."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        repo_path: Path | str,
        dry_run: bool = False,
    ) -> None:
        self.llm_provider = llm_provider
        self.repo_path = Path(repo_path).resolve()
        self.dry_run = dry_run

    def modify(
        self,
        files_to_modify: list[str],
        execution_plan: str,
        change_impact: str,
        context: RepositoryContext,
    ) -> Dict[str, Tuple[str, str]]:
        """
        Modify target files safely.

        Args:
            files_to_modify: List of relative paths to modify.
            execution_plan: Execution plan markdown text.
            change_impact: Change impact analysis markdown text.
            context: RepositoryContext instance.

        Returns:
            Dict mapping relative path to Tuple of (updated_content, unified_diff).
        """
        logger.info(f"Modifying {len(files_to_modify)} target files (Dry Run: {self.dry_run}): {files_to_modify}")
        modified_files: Dict[str, Tuple[str, str]] = {}

        for rel_path in files_to_modify:
            target_file_path = self.repo_path / rel_path
            if not target_file_path.exists():
                logger.error(f"Target file does not exist: {target_file_path}")
                continue

            logger.info(f"Reading target file: {rel_path}")
            current_content = read_file_content(target_file_path)

            formatted_prompt = MODIFIER_USER_PROMPT_TEMPLATE.format(
                file_path=rel_path,
                execution_plan=execution_plan,
                change_impact=change_impact,
                file_content=current_content,
                context_files=context.key_files_content,
            )

            logger.info(f"Generating code modifications for: {rel_path}")
            raw_response = self.llm_provider.generate(
                system_prompt=MODIFIER_SYSTEM_PROMPT,
                user_prompt=formatted_prompt,
                temperature=0.1,
            )

            cleaned_code = self._extract_code(raw_response)
            diff_text = generate_diff(current_content, cleaned_code, filename=rel_path)

            # Pre-write syntax validation check
            temp_file = target_file_path.with_suffix(target_file_path.suffix + ".tmp")
            try:
                write_file_content(temp_file, cleaned_code)
                if not check_syntax(temp_file):
                    logger.warning(f"Syntax validation issue detected in generated code for {rel_path}. Proceeding with caution.")
            finally:
                if temp_file.exists():
                    temp_file.unlink()

            if not self.dry_run:
                write_file_content(target_file_path, cleaned_code)
                logger.info(f"Successfully modified file on disk: {rel_path}")
            else:
                logger.info(f"[DRY-RUN] Modified file content computed for {rel_path} (Disk write skipped)")

            modified_files[rel_path] = (cleaned_code, diff_text)

        return modified_files

    def _extract_code(self, response_text: str) -> str:
        """Extract clean source code from markdown code fences."""
        code_block_pattern = r"```(?:js|javascript|json|html|css)?\n(.*?)```"
        match = re.search(code_block_pattern, response_text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response_text.strip()
