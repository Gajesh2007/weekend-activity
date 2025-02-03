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
from github import Github
from rich.console import Console

console = Console()


class WeekendActivityTracker:
    """Track weekend activity on GitHub repositories."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the tracker with configuration."""
        self.config = self._load_config(config_path)
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.timezone = pytz.timezone(self.config["timezone"])

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, "r") as f:
            return yaml.safe_load(f)

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

        for repo_config in self.config["repositories"]:
            repo = self.github.get_repo(f"{repo_config['owner']}/{repo_config['repo']}")
            console.log(f"Fetching activity for {repo.full_name}...")

            # Fetch commits
            commits = repo.get_commits(since=start_date, until=end_date)
            for commit in commits:
                if not commit.author:
                    continue

                commit_time = parser.parse(commit.last_modified)
                if not self.is_weekend(commit_time):
                    continue

                username = commit.author.login
                if username not in activity["commits"]:
                    activity["commits"][username] = []

                activity["commits"][username].append(
                    {
                        "message": commit.commit.message,
                        "url": commit.html_url,
                        "repo": repo.full_name,
                        "timestamp": commit_time.isoformat(),
                    }
                )

            # Fetch PRs
            prs = repo.get_pulls(state="all", sort="created", direction="desc")
            for pr in prs:
                created_at = pr.created_at.replace(tzinfo=pytz.UTC)
                if created_at < start_date:
                    break
                if created_at >= end_date:
                    continue
                if not self.is_weekend(created_at):
                    continue

                username = pr.user.login
                if username not in activity["prs"]:
                    activity["prs"][username] = []

                activity["prs"][username].append(
                    {
                        "title": pr.title,
                        "url": pr.html_url,
                        "repo": repo.full_name,
                        "timestamp": created_at.isoformat(),
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
