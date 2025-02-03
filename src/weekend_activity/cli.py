"""
Command-line interface for the Weekend Activity Tracker.
"""

import os
from datetime import datetime
from typing import Optional

import click
import pytz
import yaml
from rich.console import Console

from .tracker import WeekendActivityTracker

console = Console()


def validate_date(ctx, param, value: Optional[str]) -> Optional[datetime]:
    """Validate and parse date string."""
    if value is None:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise click.BadParameter("Date must be in YYYY-MM-DD format")


@click.group()
def cli():
    """Weekend Activity Tracker - Monitor GitHub activity during weekends."""
    pass


@cli.command()
@click.option(
    "--date",
    type=str,
    help="Target date in YYYY-MM-DD format. Defaults to today.",
    callback=validate_date,
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Path to config file",
)
@click.option(
    "--format",
    type=click.Choice(["text", "slack"]),
    default="text",
    help="Output format",
)
@click.option(
    "--notify/--no-notify",
    default=False,
    help="Send to Slack (requires SLACK_WEBHOOK_URL)",
)
def report(date: Optional[str], config: str, format: str, notify: bool):
    """Generate a report of weekend activity."""
    if not os.getenv("GITHUB_TOKEN"):
        console.print("[red]Error: GITHUB_TOKEN environment variable not set[/red]")
        return

    try:
        tracker = WeekendActivityTracker(config)
        start_date, end_date = tracker.get_date_range(date)

        console.print(
            f"[yellow]Analyzing weekend activity for {start_date.date()} to {end_date.date()}[/yellow]"
        )

        activity = tracker.fetch_activity(start_date, end_date)
        summary = tracker.generate_summary(activity, format=format)

        if notify and format == "slack":
            if not os.getenv("SLACK_WEBHOOK_URL"):
                console.print(
                    "[red]Error: SLACK_WEBHOOK_URL environment variable not set[/red]"
                )
                return
            tracker.send_slack_notification(summary)
            console.print("[green]Summary sent to Slack![/green]")
        else:
            console.print("\n[bold]Weekend Activity Summary[/bold]")
            console.print(summary)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


@cli.command()
@click.argument("repo", required=True)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default="config.yaml",
    help="Path to config file",
)
def add_repo(repo: str, config: str):
    """Add a repository to track (format: owner/repo)."""
    try:
        owner, repo_name = repo.split("/")
    except ValueError:
        console.print("[red]Error: Repository must be in format owner/repo[/red]")
        return

    try:
        with open(config, "r") as f:
            config_data = yaml.safe_load(f)

        if "repositories" not in config_data:
            config_data["repositories"] = []

        new_repo = {"owner": owner, "repo": repo_name}
        if new_repo not in config_data["repositories"]:
            config_data["repositories"].append(new_repo)

            with open(config, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)

            console.print(f"[green]Added {repo} to tracked repositories[/green]")
        else:
            console.print("[yellow]Repository already being tracked[/yellow]")

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")


def main():
    """Main entry point for the CLI."""
    cli()
