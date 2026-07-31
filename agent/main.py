"""
Main Orchestrator module for the AI Coding Agent.
Executes the full multi-agent pipeline with stage timing, execution statistics,
and Rich console graphics:
Explorer -> ContextBuilder -> Planner -> Analyzer -> Modifier -> Validator -> Summarizer
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure root workspace directory is in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# Configure stdout/stderr for UTF-8 on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agent.config import Config
from agent.context_builder import ContextBuilder
from agent.explorer import RepositoryExplorer
from agent.llm import LLMProviderFactory
from agent.logger import setup_logger
from agent.modifier import CodeModifier
from agent.planner import PlanningAgent
from agent.repository_analyzer import RepositoryAnalyzer
from agent.summarizer import Summarizer
from agent.validator import ValidationAgent

console = Console()

DEFAULT_USER_REQUEST = "Improve the application so users can better organise and search their notes."


class AgentOrchestrator:
    """Main Orchestrator driving the AI Coding Agent pipeline."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()
        self.logger = setup_logger(
            log_level=self.config.log_level,
            log_file=self.config.logs_dir / "agent.log",
        )
        self.llm_provider = LLMProviderFactory.create_provider(self.config)

    def run(self, user_request: str = DEFAULT_USER_REQUEST) -> bool:
        """Execute the complete AI agent workflow with stage timing and metrics."""
        start_time = time.time()
        console.print(
            Panel.fit(
                f"[bold cyan]AI Coding Agent (Principal Architect Edition)[/bold cyan]\n"
                f"[yellow]User Request:[/yellow] {user_request}\n"
                f"[yellow]LLM Provider:[/yellow] [green]{self.config.llm_provider.upper()}[/green]\n"
                f"[yellow]Target Repository:[/yellow] {self.config.target_repo_path}\n"
                f"[yellow]Dry-Run Mode:[/yellow] {self.config.dry_run}",
                title="[bold green]Pipeline Initialized[/bold green]",
                border_style="cyan",
            )
        )

        try:
            # Stage 1: Repository Exploration
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 1: Exploring repository structure...", total=None)
                explorer = RepositoryExplorer(self.config.target_repo_path)
                metadata = explorer.explore()
            t1_duration = round(time.time() - t0, 2)
            console.print(
                f"[bold green][OK] Stage 1 Complete ({t1_duration}s):[/bold green] Discovered {len(metadata.all_files)} files "
                f"({metadata.framework}, {metadata.database}, {metadata.frontend})"
            )

            # Stage 2: Context Building
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 2: Building token-optimized LLM context...", total=None)
                cb = ContextBuilder(metadata)
                context = cb.build_context()
            t2_duration = round(time.time() - t0, 2)
            console.print(f"[bold green][OK] Stage 2 Complete ({t2_duration}s):[/bold green] Built LLM Context (~{context.token_estimate} tokens)")

            # Stage 3: Planning Agent
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 3: Generating architectural execution plan...", total=None)
                planner = PlanningAgent(self.llm_provider, output_dir=self.config.output_dir)
                plan = planner.plan(user_request, context)
            t3_duration = round(time.time() - t0, 2)
            console.print(f"[bold green][OK] Stage 3 Complete ({t3_duration}s):[/bold green] Generated output/plan.md")

            # Stage 4: Repository Analysis Agent
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 4: Performing dependency mapping & change impact analysis...", total=None)
                analyzer = RepositoryAnalyzer(
                    llm_provider=self.llm_provider,
                    confidence_threshold=self.config.confidence_threshold,
                    max_passes=self.config.max_analysis_passes,
                    output_dir=self.config.output_dir,
                )
                analysis_result = analyzer.analyze(user_request, plan, context)
            t4_duration = round(time.time() - t0, 2)
            console.print(
                f"[bold green][OK] Stage 4 Complete ({t4_duration}s):[/bold green] Confidence {analysis_result.confidence_score}% | "
                f"Files to modify: {analysis_result.files_to_modify}"
            )

            # Stage 5: Code Modifier
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 5: Applying safe code modifications...", total=None)
                modifier = CodeModifier(
                    llm_provider=self.llm_provider,
                    repo_path=self.config.target_repo_path,
                    dry_run=self.config.dry_run,
                )
                modified_files = modifier.modify(
                    files_to_modify=analysis_result.files_to_modify,
                    execution_plan=plan,
                    change_impact=analysis_result.change_impact,
                    context=context,
                )
            t5_duration = round(time.time() - t0, 2)
            console.print(f"[bold green][OK] Stage 5 Complete ({t5_duration}s):[/bold green] Modified {len(modified_files)} target files")

            # Stage 6: Validation Agent
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 6: Running syntax validation & quality audit...", total=None)
                validator = ValidationAgent(
                    llm_provider=self.llm_provider,
                    repo_path=self.config.target_repo_path,
                    output_dir=self.config.output_dir,
                )
                validation_report = validator.validate(
                    user_request=user_request,
                    execution_plan=plan,
                    modified_files=modified_files,
                    expected_files=analysis_result.files_to_modify,
                )
            t6_duration = round(time.time() - t0, 2)
            status_color = "green" if validation_report.success else "red"
            console.print(f"[bold {status_color}][OK] Stage 6 Complete ({t6_duration}s):[/bold {status_color}] Validation status: {'PASS' if validation_report.success else 'FAIL'}")

            # Stage 7: Execution Summarizer
            t0 = time.time()
            with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
                progress.add_task(description="[cyan]Stage 7: Compiling executive execution summary...", total=None)
                summarizer = Summarizer(self.llm_provider, output_dir=self.config.output_dir)
                summarizer.summarize(user_request, modified_files, validation_report)
            t7_duration = round(time.time() - t0, 2)
            console.print(f"[bold green][OK] Stage 7 Complete ({t7_duration}s):[/bold green] Saved output/summary.md")

            total_duration = round(time.time() - start_time, 2)

            # Display Execution Metrics Table
            metrics_table = Table(title="Agent Execution Statistics", border_style="cyan")
            metrics_table.add_column("Metric", style="cyan")
            metrics_table.add_column("Value", style="yellow")

            metrics_table.add_row("LLM Provider", self.config.llm_provider.upper())
            metrics_table.add_row("Total Execution Time", f"{total_duration} seconds")
            metrics_table.add_row("Repository Files Explored", str(len(metadata.all_files)))
            metrics_table.add_row("Estimated Context Tokens", f"~{context.token_estimate}")
            metrics_table.add_row("Analysis Confidence Score", f"{analysis_result.confidence_score}%")
            metrics_table.add_row("Target Files Modified", str(len(modified_files)))
            metrics_table.add_row("Dry-Run Mode", str(self.config.dry_run))

            console.print("\n", metrics_table)

            # Display Artifacts Summary Table
            artifacts_table = Table(title="Generated Output Artifacts", border_style="green")
            artifacts_table.add_column("Artifact", style="cyan")
            artifacts_table.add_column("Path", style="yellow")
            artifacts_table.add_column("Status", style="green")

            artifacts = [
                ("Execution Plan", "output/plan.md", "Generated"),
                ("Repository Architecture Map", "output/repository_map.md", "Generated"),
                ("Dependency Flow Analysis", "output/dependency_analysis.md", "Generated"),
                ("Change Impact Analysis", "output/change_impact.md", "Generated"),
                ("Validation Report", "output/validation_report.md", "Generated"),
                ("Execution Summary", "output/summary.md", "Generated"),
            ]

            for name, path, status in artifacts:
                artifacts_table.add_row(name, path, status)

            console.print("\n", artifacts_table)
            console.print(
                Panel.fit(
                    "[bold green]AI Coding Agent Execution Completed Successfully![/bold green]",
                    border_style="green",
                )
            )
            return True

        except Exception as e:
            console.print(f"[bold red]Pipeline Execution Failed:[/bold red] {e}")
            self.logger.exception("Pipeline failure trace:")
            return False


def main() -> None:
    """CLI Entry point for the AI Coding Agent."""
    parser = argparse.ArgumentParser(description="AI Coding Agent for automated repository analysis and code editing.")
    parser.add_argument(
        "--request",
        type=str,
        default=DEFAULT_USER_REQUEST,
        help="User request prompt for the agent.",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "gemini", "anthropic", "mock"],
        help="Override LLM provider choice.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run agent without writing changes to disk.",
    )
    args = parser.parse_args()

    config = Config.load()
    if args.provider:
        config.llm_provider = args.provider
    if args.dry_run:
        config.dry_run = True

    orchestrator = AgentOrchestrator(config=config)
    success = orchestrator.run(args.request)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
