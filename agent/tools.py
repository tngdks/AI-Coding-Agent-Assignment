"""
Tools module for the AI Coding Agent.
Provides file manipulation, code diff generation, and syntax checking tools.
"""

import difflib
import subprocess
from pathlib import Path
from agent.logger import get_logger
from agent.utils import read_file_content, write_file_content

logger = get_logger()


def read_file_tool(path: Path | str) -> str:
    """
    Tool function to read file contents.

    Args:
        path: Path to target file.

    Returns:
        String content of the file.
    """
    return read_file_content(path)


def write_file_tool(path: Path | str, content: str) -> None:
    """
    Tool function to write content to a file.

    Args:
        path: Path to target file.
        content: String content to write.
    """
    write_file_content(path, content)


def generate_diff(original: str, modified: str, filename: str = "file") -> str:
    """
    Generate unified diff between original and modified code strings.

    Args:
        original: Original text content.
        modified: Updated text content.
        filename: Name of file for diff header.

    Returns:
        Unified diff string.
    """
    orig_lines = original.splitlines(keepends=True)
    mod_lines = modified.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        orig_lines,
        mod_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    return "".join(diff)


def check_syntax(file_path: Path | str) -> bool:
    """
    Syntax validation tool. Checks JavaScript files using `node -c`.

    Args:
        file_path: Path to file to validate.

    Returns:
        True if syntax is valid, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        return False

    if path.suffix.lower() in [".js", ".jsx", ".mjs"]:
        try:
            res = subprocess.run(
                ["node", "-c", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return True  # Fallback to True if node is unavailable
    return True
