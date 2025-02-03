"""Activity reporting module."""

from datetime import datetime
from typing import Dict, List, Optional, TypedDict

from rich.console import Console

from weekend_activity.db import get_db
from weekend_activity.models import Commit, PullRequest, WeekendReport

console = Console()


class UserActivity(TypedDict):
    """Type for user activity data."""

    commits: List[Commit]
    prs: List[PullRequest]


class ActivityReporter:
    """Generates activity reports."""

    def __init__(self) -> None:
        """Initialize reporter."""
        pass

    def _format_commit_summary(self, commit: Commit) -> str:
        """Format a commit for the report.

        Args:
            commit: The commit to format

        Returns:
            Formatted commit summary
        """
        lines = []
        lines.append(f"    - {commit.message.split('\n')[0]}")
        lines.append(f"      {commit.url}")

        if commit.summary:
            lines.append(f"      AI Summary: {commit.summary.summary}")
            lines.append(f"      Impact: {commit.summary.impact_level.upper()}")

        return "\n".join(lines)

    def _format_pr_summary(self, pr: PullRequest) -> str:
        """Format a pull request for the report.

        Args:
            pr: The pull request to format

        Returns:
            Formatted PR summary
        """
        lines = []
        lines.append(f"    - {pr.title}")
        lines.append(f"      {pr.url}")

        if pr.summary:
            lines.append(f"      AI Summary: {pr.summary.summary}")
            lines.append(f"      Impact: {pr.summary.impact_level.upper()}")

        return "\n".join(lines)

    def generate_text_report(
        self,
        start_date: datetime,
        end_date: datetime,
        activity: Dict[str, List[Commit | PullRequest]],
    ) -> str:
        """Generate a text report of weekend activity.

        Args:
            start_date: Start of the weekend
            end_date: End of the weekend
            activity: Dictionary of commits and PRs

        Returns:
            Formatted text report
        """
        lines = [
            "Weekend Warriors Report",
            (
                f"Activity from {start_date.isoformat()} "
                f"to {end_date.isoformat()}\n"
            ),
        ]

        # Group by user
        user_activity: Dict[str, UserActivity] = {}

        # Process commits
        for commit in activity["commits"]:
            username = commit.author_username
            if username not in user_activity:
                user_activity[username] = {"commits": [], "prs": []}
            user_activity[username]["commits"].append(commit)

        # Process PRs
        for pr in activity["pull_requests"]:
            username = pr.author_username
            if username not in user_activity:
                user_activity[username] = {"commits": [], "prs": []}
            user_activity[username]["prs"].append(pr)

        # Generate user summaries
        for username in sorted(user_activity.keys()):
            user_data = user_activity[username]
            lines.append(f"\n👤 @{username}")

            if user_data["commits"]:
                lines.append(f"  • {len(user_data['commits'])} commits:")
                for commit in user_data["commits"]:
                    lines.append(self._format_commit_summary(commit))

            if user_data["prs"]:
                lines.append(f"  • {len(user_data['prs'])} pull requests:")
                for pr in user_data["prs"]:
                    lines.append(self._format_pr_summary(pr))

        return "\n".join(lines)

    def generate_slack_report(
        self,
        start_date: datetime,
        end_date: datetime,
        activity: Dict[str, List[Commit | PullRequest]],
    ) -> str:
        """Generate a Slack-formatted report of weekend activity.

        Args:
            start_date: Start of the weekend
            end_date: End of the weekend
            activity: Dictionary of commits and PRs

        Returns:
            Formatted Slack report
        """
        lines = [
            "🚀 *Weekend Warriors Report*",
            (
                f"_Activity from {start_date.isoformat()} "
                f"to {end_date.isoformat()}_\n"
            ),
        ]

        # Group by user
        user_activity: Dict[str, UserActivity] = {}

        # Process commits
        for commit in activity["commits"]:
            username = commit.author_username
            if username not in user_activity:
                user_activity[username] = {"commits": [], "prs": []}
            user_activity[username]["commits"].append(commit)

        # Process PRs
        for pr in activity["pull_requests"]:
            username = pr.author_username
            if username not in user_activity:
                user_activity[username] = {"commits": [], "prs": []}
            user_activity[username]["prs"].append(pr)

        # Generate user summaries
        for username in sorted(user_activity.keys()):
            user_data = user_activity[username]
            lines.append(f"\n👤 *@{username}*")

            if user_data["commits"]:
                lines.append(f"  • {len(user_data['commits'])} commits:")
                for commit in user_data["commits"]:
                    message = commit.message.split("\n")[0]
                    lines.append(f"    - <{commit.url}|{message}>")
                    if commit.summary:
                        lines.append(f"      _{commit.summary.summary}_")
                        lines.append(
                            f"      Impact: {commit.summary.impact_level.upper()}"
                        )

            if user_data["prs"]:
                lines.append(f"  • {len(user_data['prs'])} pull requests:")
                for pr in user_data["prs"]:
                    lines.append(f"    - <{pr.url}|{pr.title}>")
                    if pr.summary:
                        lines.append(f"      _{pr.summary.summary}_")
                        lines.append(
                            f"      Impact: {pr.summary.impact_level.upper()}"
                        )

        return "\n".join(lines)

    def save_report(
        self,
        start_date: datetime,
        end_date: datetime,
        report_text: str,
        sent_to_slack: bool = False,
    ) -> WeekendReport:
        """Save the report to the database.

        Args:
            start_date: Start of the weekend
            end_date: End of the weekend
            report_text: Generated report text
            sent_to_slack: Whether the report was sent to Slack

        Returns:
            Created WeekendReport instance
        """
        with get_db() as db:
            report = WeekendReport(
                start_date=start_date,
                end_date=end_date,
                report_text=report_text,
                sent_to_slack=sent_to_slack,
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            return report

    def get_report(self, report_id: int) -> Optional[WeekendReport]:
        """Get a report from the database.

        Args:
            report_id: ID of the report to retrieve

        Returns:
            WeekendReport instance if found, None otherwise
        """
        with get_db() as db:
            return db.query(WeekendReport).filter_by(id=report_id).first()
