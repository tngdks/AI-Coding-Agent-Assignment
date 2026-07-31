"""
Repository Explorer module for the AI Coding Agent.
Recursively inspects target repositories, detects binary files via magic bytes/null byte checks,
extracts line counts, categorizes services/middleware/controllers/models/routes/views/tests,
and generates structured repository metadata.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from agent.logger import get_logger
from agent.utils import DEFAULT_IGNORE_PATTERNS, get_relative_path, read_file_content, should_ignore

logger = get_logger()


@dataclass
class FileInfo:
    """Metadata representing a single file in the repository."""

    path: Path
    relative_path: str
    extension: str
    size_bytes: int
    line_count: int
    category: str  # 'model', 'controller', 'route', 'service', 'middleware', 'config', 'entry', 'test', 'frontend', 'other'
    is_binary: bool = False
    content: Optional[str] = None


@dataclass
class RepositoryMetadata:
    """Structured overview of the explored repository."""

    repo_path: Path
    name: str
    framework: str
    database: str
    frontend: str
    entry_point: Optional[str]
    package_json: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)
    readme_content: Optional[str] = None
    models: List[FileInfo] = field(default_factory=list)
    controllers: List[FileInfo] = field(default_factory=list)
    routes: List[FileInfo] = field(default_factory=list)
    services: List[FileInfo] = field(default_factory=list)
    middlewares: List[FileInfo] = field(default_factory=list)
    views: List[FileInfo] = field(default_factory=list)
    configs: List[FileInfo] = field(default_factory=list)
    tests: List[FileInfo] = field(default_factory=list)
    all_files: List[FileInfo] = field(default_factory=list)
    tree_structure: str = ""

    def summary(self) -> str:
        """Return a human-readable high-level summary of the repository."""
        return (
            f"Repository: {self.name}\n"
            f"Framework: {self.framework}\n"
            f"Database: {self.database}\n"
            f"Frontend: {self.frontend}\n"
            f"Entry Point: {self.entry_point or 'Unknown'}\n"
            f"Total Files: {len(self.all_files)}\n"
            f"Models ({len(self.models)}): {[f.relative_path for f in self.models]}\n"
            f"Controllers ({len(self.controllers)}): {[f.relative_path for f in self.controllers]}\n"
            f"Routes ({len(self.routes)}): {[f.relative_path for f in self.routes]}\n"
            f"Services ({len(self.services)}): {[f.relative_path for f in self.services]}\n"
            f"Middlewares ({len(self.middlewares)}): {[f.relative_path for f in self.middlewares]}\n"
            f"Tests ({len(self.tests)}): {[f.relative_path for f in self.tests]}"
        )


class RepositoryExplorer:
    """Explores repository file structure and extracts semantic metadata."""

    def __init__(
        self,
        repo_path: Path | str,
        ignore_patterns: Optional[Set[str]] = None,
    ) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = ignore_patterns if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS

    def explore(self) -> RepositoryMetadata:
        """Perform complete analysis and extraction of target repository."""
        logger.info(f"Exploring repository at: {self.repo_path}")
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Target repository path does not exist: {self.repo_path}")

        all_files = self._walk_repository()
        package_json, dependencies, dev_dependencies, repo_name = self._parse_package_json()
        readme_content = self._read_readme()
        framework, database, frontend = self._detect_tech_stack(dependencies, dev_dependencies)
        entry_point = self._detect_entry_point(package_json, all_files)

        # Categorize files into layers
        models = [f for f in all_files if f.category == "model"]
        controllers = [f for f in all_files if f.category == "controller"]
        routes = [f for f in all_files if f.category == "route"]
        services = [f for f in all_files if f.category == "service"]
        middlewares = [f for f in all_files if f.category == "middleware"]
        views = [f for f in all_files if f.category in ("view", "frontend")]
        configs = [f for f in all_files if f.category == "config"]
        tests = [f for f in all_files if f.category == "test"]

        tree = self._generate_tree(all_files)

        metadata = RepositoryMetadata(
            repo_path=self.repo_path,
            name=repo_name or self.repo_path.name,
            framework=framework,
            database=database,
            frontend=frontend,
            entry_point=entry_point,
            package_json=package_json,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            readme_content=readme_content,
            models=models,
            controllers=controllers,
            routes=routes,
            services=services,
            middlewares=middlewares,
            views=views,
            configs=configs,
            tests=tests,
            all_files=all_files,
            tree_structure=tree,
        )

        logger.info(
            f"Exploration complete. Found {len(all_files)} files "
            f"({len(models)} models, {len(controllers)} controllers, {len(routes)} routes, {len(services)} services)."
        )
        return metadata

    def _walk_repository(self) -> List[FileInfo]:
        """Traverse the repository directory tree, analyzing files."""
        file_list: List[FileInfo] = []

        for p in sorted(self.repo_path.rglob("*")):
            if p.is_dir():
                continue
            if should_ignore(p, self.ignore_patterns):
                continue

            rel_path = get_relative_path(p, self.repo_path)
            is_binary = self._check_is_binary(p)
            category = self._classify_file(rel_path, p.name)

            content: Optional[str] = None
            line_count = 0

            if not is_binary and p.stat().st_size < 150_000:
                try:
                    content = read_file_content(p)
                    line_count = len(content.splitlines())
                except Exception as e:
                    logger.warning(f"Could not read text content of {rel_path}: {e}")

            info = FileInfo(
                path=p,
                relative_path=rel_path,
                extension=p.suffix.lower(),
                size_bytes=p.stat().st_size,
                line_count=line_count,
                category=category,
                is_binary=is_binary,
                content=content,
            )
            file_list.append(info)

        return file_list

    def _check_is_binary(self, file_path: Path) -> bool:
        """Detect binary files using null byte inspection in first 1024 bytes."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:
                    return True
            return False
        except Exception:
            return True

    def _classify_file(self, rel_path: str, filename: str) -> str:
        """Classify a file based on path conventions and file naming."""
        lower_path = rel_path.lower()
        lower_name = filename.lower()

        if "test" in lower_path or lower_name.endswith(".test.js") or lower_name.endswith(".spec.js"):
            return "test"
        elif "model" in lower_path or lower_name.endswith(".model.js"):
            return "model"
        elif "controller" in lower_path or lower_name.endswith(".controller.js"):
            return "controller"
        elif "route" in lower_path or lower_name.endswith(".routes.js") or lower_name.endswith(".route.js"):
            return "route"
        elif "service" in lower_path or lower_name.endswith(".service.js"):
            return "service"
        elif "middleware" in lower_path or lower_name.endswith(".middleware.js"):
            return "middleware"
        elif any(k in lower_path for k in ["view", "public", "html", "static", "templates", "components"]) or lower_name.endswith((".html", ".ejs", ".pug", ".jsx", ".tsx")):
            return "view"
        elif "config" in lower_path or "database" in lower_name:
            return "config"
        elif lower_name in ["server.js", "app.js", "index.js", "main.js"]:
            return "entry"
        else:
            return "other"

    def _parse_package_json(self) -> Tuple[Dict[str, Any], Dict[str, str], Dict[str, str], str]:
        """Read and parse package.json if available."""
        pkg_file = self.repo_path / "package.json"
        if not pkg_file.exists():
            return {}, {}, {}, ""

        try:
            content = read_file_content(pkg_file)
            data = json.loads(content)
            deps = data.get("dependencies", {})
            dev_deps = data.get("devDependencies", {})
            name = data.get("name", "")
            return data, deps, dev_deps, name
        except Exception as e:
            logger.warning(f"Error parsing package.json: {e}")
            return {}, {}, {}, ""

    def _read_readme(self) -> Optional[str]:
        """Read README file content if present."""
        for candidate in ["README.md", "readme.md", "README", "README.txt"]:
            readme_path = self.repo_path / candidate
            if readme_path.exists():
                try:
                    return read_file_content(readme_path)
                except Exception:
                    pass
        return None

    def _detect_tech_stack(
        self,
        dependencies: Dict[str, str],
        dev_dependencies: Dict[str, str],
    ) -> Tuple[str, str, str]:
        """Identify web framework, database libraries, and frontend framework."""
        all_deps = {**dependencies, **dev_dependencies}
        
        # Framework Detection
        framework = "Node.js App"
        if "express" in all_deps:
            framework = "Express.js (Node.js)"
        elif "koa" in all_deps:
            framework = "Koa (Node.js)"
        elif "nestjs" in all_deps or "@nestjs/core" in all_deps:
            framework = "NestJS"
        elif "next" in all_deps:
            framework = "Next.js"

        # Database Detection
        database = "None / Custom"
        if "mongoose" in all_deps:
            database = "MongoDB (Mongoose ODM)"
        elif "mongodb" in all_deps:
            database = "MongoDB Native Driver"
        elif "sequelize" in all_deps:
            database = "Sequelize ORM"
        elif "prisma" in all_deps or "@prisma/client" in all_deps:
            database = "Prisma ORM"

        # Frontend Detection
        frontend = "Server-Side Rendered / Static HTML"
        if "react" in all_deps:
            frontend = "React"
        elif "vue" in all_deps:
            frontend = "Vue.js"
        elif "@angular/core" in all_deps:
            frontend = "Angular"
        elif "ejs" in all_deps:
            frontend = "EJS Templates"

        return framework, database, frontend

    def _detect_entry_point(self, package_json: Dict[str, Any], files: List[FileInfo]) -> Optional[str]:
        """Determine main entry point file."""
        if main := package_json.get("main"):
            return main

        entry_names = ["server.js", "app.js", "index.js", "main.js"]
        for f in files:
            if f.path.name in entry_names:
                return f.relative_path
        return None

    def _generate_tree(self, files: List[FileInfo]) -> str:
        """Generate ASCII directory tree representation."""
        tree_lines = []
        for f in sorted(files, key=lambda x: x.relative_path):
            tree_lines.append(f"├── {f.relative_path} [{f.category}] ({f.line_count} lines, {f.size_bytes} B)")
        return "\n".join(tree_lines)
