"""
Shared utilities module for the AI Coding Agent.
Provides robust helper functions for file I/O, path normalization,
markdown formatting, and ignore filtering.
"""

from pathlib import Path
from typing import Any

# Default ignore list for repository exploration
DEFAULT_IGNORE_PATTERNS: set[str] = {
    "node_modules",
    ".git",
    ".github",
    ".vscode",
    "dist",
    "build",
    "coverage",
    ".DS_Store",
    "package-lock.json",
    "yarn.lock",
}


def read_file_content(path: Path | str) -> str:
    """
    Safely read and return text content from a file.

    Args:
        path: Path to the target file.

    Returns:
        String content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_file_content(path: Path | str, content: str) -> None:
    """
    Safely write string content to a file, ensuring parent directories exist.

    Args:
        path: Path where file should be saved.
        content: String content to write.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def get_relative_path(path: Path | str, base_path: Path | str) -> str:
    """
    Convert an absolute or nested path into a standardized relative path string
    normalized with forward slashes.

    Args:
        path: Target file/directory path.
        base_path: Root directory path.

    Returns:
        Relative path string with forward slashes (e.g. 'app/controllers/note.controller.js').
    """
    target = Path(path).resolve()
    base = Path(base_path).resolve()

    try:
        rel_path = target.relative_to(base)
        return rel_path.as_posix()
    except ValueError:
        return target.as_posix()


def should_ignore(
    path: Path | str,
    ignore_patterns: set[str] | None = None,
) -> bool:
    """
    Check whether a given file or directory path matches ignore criteria.

    Args:
        path: File or directory path to check.
        ignore_patterns: Custom set of ignore pattern strings.

    Returns:
        True if the path should be ignored, False otherwise.
    """
    patterns = ignore_patterns if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS
    path_parts = Path(path).parts

    for part in path_parts:
        if part in patterns or part.startswith("."):
            return True
    return False


def format_markdown_section(title: str, body: str, level: int = 2) -> str:
    """
    Format a markdown section with header and body.

    Args:
        title: Section title.
        body: Markdown body text.
        level: Heading level (1-6).

    Returns:
        Formatted markdown string.
    """
    header = "#" * max(1, min(level, 6))
    return f"{header} {title}\n\n{body.strip()}\n"


def compute_confidence_score(
    identified_components: int,
    expected_components: int,
    architecture_clarity_factor: float = 1.0,
) -> float:
    """
    Compute confidence score (0-100%) for repository analysis.

    Args:
        identified_components: Number of relevant files/components found.
        expected_components: Total expected components for complete flow.
        architecture_clarity_factor: Scaling factor based on structural clarity (0.5 - 1.0).

    Returns:
        Confidence score percentage (0.0 to 100.0).
    """
    if expected_components <= 0:
        return 100.0

    ratio = min(1.0, identified_components / expected_components)
    score = ratio * architecture_clarity_factor * 100.0
    return round(max(0.0, min(100.0, score)), 2)
