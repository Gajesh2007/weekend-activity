"""Slack integration module."""

import os
from typing import Dict, Optional

import requests
from rich.console import Console

console = Console()


class SlackNotifier:
    """Handles sending notifications to Slack."""

    def __init__(self, webhook_url: Optional[str] = None):
        """Initialize the notifier with a webhook URL."""
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("Slack webhook URL not provided")

    def send_report(self, report_text: str) -> bool:
        """Send a report to Slack.

        Args:
            report_text: The formatted report text to send

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "text": report_text,
                "mrkdwn": True,
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                console.print("[green]Successfully sent report to Slack[/green]")
                return True
            else:
                console.print(
                    f"[red]Failed to send report to Slack: {response.text}[/red]"
                )
                return False

        except Exception as e:
            console.print(f"[red]Error sending report to Slack: {str(e)}[/red]")
            return False

    def send_error(self, error_message: str) -> bool:
        """Send an error notification to Slack.

        Args:
            error_message: The error message to send

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            payload = {
                "text": f"❌ *Weekend Activity Error*\n{error_message}",
                "mrkdwn": True,
            }

            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            )

            return response.status_code == 200

        except Exception:
            return False
