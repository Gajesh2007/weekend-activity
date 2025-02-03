"""
Weekend Activity Tracker - Core functionality for tracking GitHub activity.
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

import pytz
import requests
import yaml
from dateutil import parser
from rich.console import Console

from weekend_activity.db import get_db
from weekend_activity.github_client import github
from weekend_activity.repository import GitHubManager

console = Console()


class WeekendActivityTracker:
    """Track weekend activity on GitHub repositories."""

    def __init__(self, config_path: str = "config.yaml") -> None:
        """Initialize the tracker.

        Args:
            config_path: Path to configuration file
        """
        # Initialize GitHub manager
        self.github_manager = GitHubManager()

        # Load configuration
        try:
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            self.config = {"repositories": []}

        # Ensure required config sections exist
        if "repositories" not in self.config:
            self.config["repositories"] = []
        if "summary" not in self.config:
            self.config["summary"] = {
                "max_commits_per_user": 10,
                "max_prs_per_user": 5,
                "include_commit_messages": True,
                "include_pr_titles": True,
            }

        self.timezone = pytz.timezone(self.config.get("timezone", "UTC"))

    def is_weekend(self, dt: datetime) -> bool:
        """Check if the given datetime falls on a weekend."""
        local_dt = dt.astimezone(self.timezone)
        return local_dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday

    def get_date_range(
        self, target_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """Get the date range for the weekend containing or before the target date."""
        if target_date is None:
            target_date = datetime.now(self.timezone)

        # Ensure target_date has timezone
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=self.timezone)

        weekday = target_date.weekday()

        if weekday == 0:  # Monday - look at previous weekend
            end_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=2)  # Go back to Saturday
        else:
            # Find the most recent weekend
            days_since_weekend = (weekday - 6) % 7
            end_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = end_date - timedelta(days=days_since_weekend)

        return start_date, end_date

    def fetch_activity(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Fetch GitHub activity for the specified date range."""
        activity = {
            "commits": {},  # user -> list of commits
            "prs": {},  # user -> list of PRs
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
        }

        with get_db() as db:
            for repo_config in self.config["repositories"]:
                # Sync repository to database
                repo = self.github_manager.sync_repository(
                    repo_config["owner"],
                    repo_config["repo"],
                    db,
                )

                # Fetch activity using GitHubManager
                commits, prs = self.github_manager.fetch_weekend_activity(
                    repo,
                    start_date,
                    end_date,
                    db,
                )

                # Process commits
                for commit in commits:
                    if not self.is_weekend(commit.committed_at):
                        continue

                    username = commit.author_username
                    if username not in activity["commits"]:
                        activity["commits"][username] = []

                    activity["commits"][username].append(
                        {
                            "message": commit.message,
                            "url": commit.url,
                            "repo": commit.repository.full_name,
                            "timestamp": commit.committed_at.isoformat(),
                        }
                    )

                # Process PRs
                for pr in prs:
                    if not self.is_weekend(pr.created_at):
                        continue

                    username = pr.author_username
                    if username not in activity["prs"]:
                        activity["prs"][username] = []

                    activity["prs"][username].append(
                        {
                            "title": pr.title,
                            "url": pr.url,
                            "repo": pr.repository.full_name,
                            "timestamp": pr.created_at.isoformat(),
                            "state": pr.state,
                        }
                    )

        return activity

    def generate_summary(self, activity: Dict[str, Any], format: str = "slack") -> str:
        """Generate a summary of weekend activity in the specified format."""
        if not activity["commits"] and not activity["prs"]:
            return "No weekend activity to report! 😴"

        if format == "slack":
            return self._generate_slack_summary(activity)
        else:
            return self._generate_text_summary(activity)

    def _generate_slack_summary(self, activity: Dict[str, Any]) -> str:
        """Generate a Slack-formatted summary."""
        summary = [
            "🚀 *Weekend Warriors Report*",
            f"_Activity from {activity['period']['start']} to {activity['period']['end']}_\n",
        ]

        contributors = set(
            list(activity["commits"].keys()) + list(activity["prs"].keys())
        )
        for username in sorted(contributors):
            user_summary = [f"\n👤 *@{username}*"]

            commits = activity["commits"].get(username, [])
            if commits:
                user_summary.append(f"  • {len(commits)} commits:")
                for commit in commits[: self.config["summary"]["max_commits_per_user"]]:
                    message = commit["message"].split("\n")[0]
                    user_summary.append(f"    - <{commit['url']}|{message}>")

            prs = activity["prs"].get(username, [])
            if prs:
                user_summary.append(f"  • {len(prs)} pull requests:")
                for pr in prs[: self.config["summary"]["max_prs_per_user"]]:
                    user_summary.append(f"    - <{pr['url']}|{pr['title']}>")

            summary.extend(user_summary)

        return "\n".join(summary)

    def _generate_text_summary(self, activity: Dict[str, Any]) -> str:
        """Generate a plain text summary."""
        summary = [
            "Weekend Warriors Report",
            f"Activity from {activity['period']['start']} to {activity['period']['end']}\n",
        ]

        contributors = set(
            list(activity["commits"].keys()) + list(activity["prs"].keys())
        )
        for username in sorted(contributors):
            user_summary = [f"\n@{username}"]

            commits = activity["commits"].get(username, [])
            if commits:
                user_summary.append(f"  • {len(commits)} commits:")
                for commit in commits[: self.config["summary"]["max_commits_per_user"]]:
                    message = commit["message"].split("\n")[0]
                    user_summary.append(f"    - {message}")
                    user_summary.append(f"      {commit['url']}")

            prs = activity["prs"].get(username, [])
            if prs:
                user_summary.append(f"  • {len(prs)} pull requests:")
                for pr in prs[: self.config["summary"]["max_prs_per_user"]]:
                    user_summary.append(f"    - {pr['title']}")
                    user_summary.append(f"      {pr['url']}")

            summary.extend(user_summary)

        return "\n".join(summary)

    def send_slack_notification(self, message: str) -> None:
        """Send the summary to Slack."""
        webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            raise ValueError("SLACK_WEBHOOK_URL environment variable not set")

        payload = {
            "channel": self.config["slack"]["channel"],
            "username": self.config["slack"]["username"],
            "icon_emoji": self.config["slack"]["icon_emoji"],
            "text": message,
        }

        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
