"""Tests for the weekend activity tracker."""

import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import pytz

from weekend_activity.tracker import WeekendActivityTracker


@pytest.fixture
def tracker():
    """Create a tracker instance with test configuration."""
    config = {
        "repositories": [{"owner": "test-org", "repo": "test-repo"}],
        "timezone": "UTC",
        "slack": {
            "channel": "#test-channel",
            "username": "Test Bot",
            "icon_emoji": ":test:",
        },
        "summary": {
            "max_commits_per_user": 5,
            "max_prs_per_user": 3,
            "include_commit_messages": True,
            "include_pr_titles": True,
        },
    }

    with patch(
        "weekend_activity.tracker.WeekendActivityTracker._load_config"
    ) as mock_config:
        mock_config.return_value = config
        tracker = WeekendActivityTracker()
        yield tracker


def test_is_weekend():
    """Test weekend detection logic."""
    tracker = WeekendActivityTracker()

    # Test Saturday (2024-02-03)
    saturday = datetime(2024, 2, 3, 12, 0, tzinfo=pytz.UTC)
    assert tracker.is_weekend(saturday) is True

    # Test Sunday (2024-02-04)
    sunday = datetime(2024, 2, 4, 12, 0, tzinfo=pytz.UTC)
    assert tracker.is_weekend(sunday) is True

    # Test Monday (2024-02-05)
    monday = datetime(2024, 2, 5, 12, 0, tzinfo=pytz.UTC)
    assert tracker.is_weekend(monday) is False


def test_get_date_range(tracker):
    """Test date range calculation for different scenarios."""
    # Test Monday
    monday = datetime(2024, 2, 5, 9, 0, tzinfo=pytz.UTC)
    with patch("weekend_activity.tracker.datetime") as mock_datetime:
        mock_datetime.now.return_value = monday
        start, end = tracker.get_date_range()
        assert start.weekday() == 5  # Saturday
        assert end.weekday() == 0  # Monday
        assert (end - start).days == 2

    # Test with specific date (Wednesday)
    wednesday = datetime(2024, 2, 7, 9, 0, tzinfo=pytz.UTC)
    start, end = tracker.get_date_range(wednesday)
    assert start.weekday() == 5  # Previous Saturday
    assert (end - start).days == 2


def test_generate_text_summary(tracker):
    """Test plain text summary generation."""
    activity = {
        "commits": {
            "user1": [
                {
                    "message": "Test commit",
                    "url": "https://github.com/test/1",
                    "repo": "test-org/test-repo",
                    "timestamp": "2024-02-03T12:00:00Z",
                }
            ]
        },
        "prs": {
            "user1": [
                {
                    "title": "Test PR",
                    "url": "https://github.com/test/pr/1",
                    "repo": "test-org/test-repo",
                    "timestamp": "2024-02-03T12:00:00Z",
                    "state": "open",
                }
            ]
        },
        "period": {"start": "2024-02-03T00:00:00Z", "end": "2024-02-05T00:00:00Z"},
    }

    summary = tracker.generate_summary(activity, format="text")
    assert "Weekend Warriors Report" in summary
    assert "@user1" in summary
    assert "Test commit" in summary
    assert "Test PR" in summary
    assert "https://github.com/test/1" in summary
    assert "https://github.com/test/pr/1" in summary


def test_generate_slack_summary(tracker):
    """Test Slack-formatted summary generation."""
    activity = {
        "commits": {
            "user1": [
                {
                    "message": "Test commit",
                    "url": "https://github.com/test/1",
                    "repo": "test-org/test-repo",
                    "timestamp": "2024-02-03T12:00:00Z",
                }
            ]
        },
        "prs": {
            "user1": [
                {
                    "title": "Test PR",
                    "url": "https://github.com/test/pr/1",
                    "repo": "test-org/test-repo",
                    "timestamp": "2024-02-03T12:00:00Z",
                    "state": "open",
                }
            ]
        },
        "period": {"start": "2024-02-03T00:00:00Z", "end": "2024-02-05T00:00:00Z"},
    }

    summary = tracker.generate_summary(activity, format="slack")
    assert "*Weekend Warriors Report*" in summary
    assert "*@user1*" in summary
    assert "<https://github.com/test/1|Test commit>" in summary
    assert "<https://github.com/test/pr/1|Test PR>" in summary


def test_empty_summary(tracker):
    """Test summary generation with no activity."""
    activity = {
        "commits": {},
        "prs": {},
        "period": {"start": "2024-02-03T00:00:00Z", "end": "2024-02-05T00:00:00Z"},
    }

    summary = tracker.generate_summary(activity)
    assert "No weekend activity to report" in summary


def test_slack_notification(tracker):
    """Test Slack notification sending."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.raise_for_status = MagicMock()

        with patch.dict(
            os.environ, {"SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"}
        ):
            tracker.send_slack_notification("Test message")

            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert args[0] == "https://hooks.slack.com/test"
            assert kwargs["json"]["text"] == "Test message"


def test_slack_notification_missing_webhook(tracker):
    """Test Slack notification with missing webhook URL."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError):
            tracker.send_slack_notification("Test message")
