"""Command-line interface for the weekend activity tracker."""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv
from rich.console import Console

from weekend_activity.tracker import WeekendActivityTracker

# Load environment variables from .env file
load_dotenv()

console = Console()


def validate_date(
    ctx: click.Context,
    param: click.Parameter,
    value: Optional[str],
) -> Optional[datetime]:
    """Validate and parse date parameter.

    Args:
        ctx: Click context
        param: Click parameter
        value: Date string in YYYY-MM-DD format

    Returns:
        Parsed datetime object or None
    """
    if not value:
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("Date must be in YYYY-MM-DD format")


@click.group()
def cli() -> None:
    """Track and summarize weekend GitHub activity."""
    pass


@cli.command()
@click.option(
    "--date",
    help="Target date (YYYY-MM-DD format)",
    callback=validate_date,
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    help="Path to config file",
    default="config.yaml",
)
@click.option(
    "--format",
    type=click.Choice(["text", "slack"]),
    help="Output format",
    default="text",
)
@click.option(
    "--notify/--no-notify",
    help="Send to Slack",
    default=False,
)
def report(
    date: Optional[datetime],
    config: str,
    format: str,
    notify: bool,
) -> None:
    """Generate an activity report for the specified weekend."""
    if not os.getenv("GITHUB_TOKEN"):
        console.print(
            "[red]Error: GITHUB_TOKEN environment variable not set. "
            "Please ensure you have a .env file with GITHUB_TOKEN set.[/red]"
        )
        raise click.Abort()

    try:
        tracker = WeekendActivityTracker(config_path=config)
        start_date, end_date = tracker.get_date_range(date)

        console.print(
            "Fetching activity from "
            f"{start_date.date()} to {end_date.date()}..."
        )

        activity = tracker.fetch_activity(start_date, end_date)
        summary = tracker.generate_summary(activity, format=format)

        if notify and format == "slack":
            tracker.send_slack_notification(summary)
        else:
            console.print(summary)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()


@cli.command()
@click.argument("repo")
@click.option(
    "--config",
    type=click.Path(),
    help="Path to config file",
    default="config.yaml",
)
def add_repo(repo: str, config: str) -> None:
    """Add a repository to track.

    Args:
        repo: Repository in owner/name format
        config: Path to config file
    """
    try:
        if "/" not in repo:
            raise click.BadParameter(
                "Repository must be in owner/name format "
                "(e.g., octocat/Hello-World)"
            )

        owner, name = repo.split("/")
        config_path = Path(config)

        if not config_path.exists():
            config_path.write_text("repositories: []\n")

        tracker = WeekendActivityTracker(config_path=str(config_path))
        tracker.add_repository(owner, name)

        console.print(f"[green]Added repository {repo} to tracking list[/green]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise click.Abort()


def main() -> None:
    """Run the CLI application."""
    cli()
