"""
Configuration module for the AI Coding Agent.
Handles environment loading, provider selection, validation,
and settings management across the agent workflow.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class Config:
    """Central configuration class for the AI Coding Agent."""

    # LLM Provider Selection: 'openai' | 'gemini' | 'anthropic' | 'mock'
    llm_provider: str = field(default="openai")

    # OpenAI Settings
    openai_api_key: str = field(default="")
    openai_model: str = field(default="gpt-4o")

    # Gemini Settings
    gemini_api_key: str = field(default="")
    gemini_model: str = field(default="gemini-2.5-pro")

    # Anthropic Settings
    anthropic_api_key: str = field(default="")
    anthropic_model: str = field(default="claude-3-5-sonnet-20241022")

    # Target Repository
    target_repo_path: Path = field(default_factory=lambda: Path("./node-easy-notes-app"))

    # Agent Execution Settings
    log_level: str = field(default="INFO")
    confidence_threshold: float = field(default=80.0)
    max_analysis_passes: int = field(default=2)
    dry_run: bool = field(default=False)

    # Output & Logs Directories
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    logs_dir: Path = field(default_factory=lambda: Path("./logs"))

    @classmethod
    def load(cls, env_file: str | Path | None = None) -> "Config":
        """
        Load configuration from environment variables and optional .env file.
        
        Args:
            env_file: Optional path to a specific .env file.

        Returns:
            Config instance populated with environment settings.
        """
        if env_file:
            load_dotenv(dotenv_path=env_file, override=True)
        else:
            load_dotenv(override=True)

        target_repo = os.getenv("TARGET_REPO_PATH", "./node-easy-notes-app")
        output_dir = os.getenv("OUTPUT_DIR", "./output")
        logs_dir = os.getenv("LOGS_DIR", "./logs")
        dry_run_str = os.getenv("DRY_RUN", "false").lower()

        config = cls(
            llm_provider=os.getenv("LLM_PROVIDER", "openai").lower(),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-pro"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            anthropic_model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            target_repo_path=Path(target_repo).resolve(),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "80.0")),
            max_analysis_passes=int(os.getenv("MAX_ANALYSIS_PASSES", "2")),
            dry_run=dry_run_str in ("true", "1", "yes"),
            output_dir=Path(output_dir).resolve(),
            logs_dir=Path(logs_dir).resolve(),
        )

        config.ensure_directories()
        return config

    def ensure_directories(self) -> None:
        """Ensure that output and log directories exist on disk."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> list[str]:
        """
        Validate configuration settings.

        Returns:
            List of validation error messages, if any.
        """
        errors: list[str] = []
        valid_providers = {"openai", "gemini", "anthropic", "mock"}
        if self.llm_provider not in valid_providers:
            errors.append(f"Invalid LLM_PROVIDER '{self.llm_provider}'. Must be one of {valid_providers}")

        if self.llm_provider == "openai" and not self.openai_api_key:
            errors.append("OPENAI_API_KEY environment variable is missing for provider 'openai'.")
        elif self.llm_provider == "gemini" and not self.gemini_api_key:
            errors.append("GEMINI_API_KEY environment variable is missing for provider 'gemini'.")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY environment variable is missing for provider 'anthropic'.")

        if not (0 <= self.confidence_threshold <= 100):
            errors.append(f"CONFIDENCE_THRESHOLD must be between 0 and 100, got {self.confidence_threshold}")
        if self.max_analysis_passes < 1:
            errors.append(f"MAX_ANALYSIS_PASSES must be at least 1, got {self.max_analysis_passes}")
        return errors
