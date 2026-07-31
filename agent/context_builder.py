"""
Context Builder module for the AI Coding Agent.
Transforms raw RepositoryMetadata into an optimized, structured context payload for LLM prompts,
handling file chunking, deduplication, and token budget management.
"""

from dataclasses import dataclass, field
from typing import List, Set
from agent.explorer import FileInfo, RepositoryMetadata
from agent.logger import get_logger

logger = get_logger()


@dataclass
class RepositoryContext:
    """Optimized context package formatted for LLM consumption."""

    repo_name: str
    framework: str
    database: str
    frontend: str
    entry_point: str | None
    summary_overview: str
    tree_overview: str
    package_summary: str
    key_files_content: str
    token_estimate: int

    def to_prompt_str(self) -> str:
        """Render the complete structured context as a markdown prompt string."""
        return (
            f"# Repository Context: {self.repo_name}\n\n"
            f"**Framework**: {self.framework}\n"
            f"**Database**: {self.database}\n"
            f"**Frontend**: {self.frontend}\n"
            f"**Entry Point**: {self.entry_point or 'N/A'}\n"
            f"**Estimated Context Tokens**: ~{self.token_estimate}\n\n"
            f"## Architecture Summary\n"
            f"{self.summary_overview}\n\n"
            f"## Dependencies & Environment\n"
            f"{self.package_summary}\n\n"
            f"## Repository File Map\n"
            f"```text\n"
            f"{self.tree_overview}\n"
            f"```\n\n"
            f"## Source Code Files\n\n"
            f"{self.key_files_content}\n"
        )


class ContextBuilder:
    """Converts RepositoryMetadata into token-optimized LLM context."""

    def __init__(
        self,
        metadata: RepositoryMetadata,
        max_file_size_bytes: int = 50_000,
        max_chunk_lines: int = 500,
    ) -> None:
        self.metadata = metadata
        self.max_file_size_bytes = max_file_size_bytes
        self.max_chunk_lines = max_chunk_lines

    def build_context(self) -> RepositoryContext:
        """Construct token-optimized LLM repository context."""
        logger.info(f"Building LLM context for repository: {self.metadata.name}")

        summary_overview = self._build_architecture_summary()
        package_summary = self._summarize_package()
        key_files_content = self._format_key_files()

        full_text = f"{summary_overview}\n{package_summary}\n{self.metadata.tree_structure}\n{key_files_content}"
        token_estimate = self._estimate_tokens(full_text)

        context = RepositoryContext(
            repo_name=self.metadata.name,
            framework=self.metadata.framework,
            database=self.metadata.database,
            frontend=self.metadata.frontend,
            entry_point=self.metadata.entry_point,
            summary_overview=summary_overview,
            tree_overview=self.metadata.tree_structure,
            package_summary=package_summary,
            key_files_content=key_files_content,
            token_estimate=token_estimate,
        )

        logger.info(f"Context constructed (~{token_estimate} estimated tokens).")
        return context

    def _build_architecture_summary(self) -> str:
        """Construct high-level summary of repository architectural layers."""
        models_str = ", ".join([f.relative_path for f in self.metadata.models]) or "None"
        controllers_str = ", ".join([f.relative_path for f in self.metadata.controllers]) or "None"
        routes_str = ", ".join([f.relative_path for f in self.metadata.routes]) or "None"
        services_str = ", ".join([f.relative_path for f in self.metadata.services]) or "None"
        middlewares_str = ", ".join([f.relative_path for f in self.metadata.middlewares]) or "None"
        configs_str = ", ".join([f.relative_path for f in self.metadata.configs]) or "None"

        return (
            f"The application is a **{self.metadata.framework}** application using **{self.metadata.database}**.\n\n"
            f"- **Entry Point**: `{self.metadata.entry_point or 'N/A'}`\n"
            f"- **Models Layer**: `{models_str}`\n"
            f"- **Controllers Layer**: `{controllers_str}`\n"
            f"- **Routes Layer**: `{routes_str}`\n"
            f"- **Services Layer**: `{services_str}`\n"
            f"- **Middleware Layer**: `{middlewares_str}`\n"
            f"- **Configuration Layer**: `{configs_str}`"
        )

    def _summarize_package(self) -> str:
        """Extract clean summary of key dependencies from package.json."""
        if not self.metadata.dependencies:
            return "No package.json dependencies found."

        deps_list = [f"- `{k}`: {v}" for k, v in self.metadata.dependencies.items()]
        dev_deps_list = [f"- `{k}`: {v}" for k, v in self.metadata.dev_dependencies.items()]

        summary = "### Key Dependencies\n" + "\n".join(deps_list)
        if dev_deps_list:
            summary += "\n\n### Dev Dependencies\n" + "\n".join(dev_deps_list)
        return summary

    def _format_key_files(self) -> str:
        """Format models, controllers, routes, entry files into markdown code blocks with chunking."""
        formatted_blocks: List[str] = []
        seen_paths: Set[str] = set()

        priority_files = (
            [f for f in self.metadata.all_files if f.category == "entry"]
            + self.metadata.models
            + self.metadata.controllers
            + self.metadata.routes
            + self.metadata.services
            + self.metadata.middlewares
            + self.metadata.configs
            + self.metadata.views
        )

        for f in priority_files:
            if f.relative_path in seen_paths or f.is_binary:
                continue
            seen_paths.add(f.relative_path)

            content = f.content or ""
            lines = content.splitlines()

            # Chunk file if larger than max_chunk_lines
            if len(lines) > self.max_chunk_lines:
                chunked_content = "\n".join(lines[: self.max_chunk_lines])
                content = f"{chunked_content}\n\n/* ... File Truncated ({len(lines)} total lines) ... */"

            block = (
                f"### File: `{f.relative_path}` ({f.category.upper()})\n"
                f"```js\n"
                f"{content.strip()}\n"
                f"```\n"
            )
            formatted_blocks.append(block)

        return "\n".join(formatted_blocks)

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (~4 characters per token)."""
        return max(1, len(text) // 4)
