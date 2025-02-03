# API Documentation

## Core Classes

### WeekendActivityTracker

The main class that handles fetching and processing GitHub activity.

```python
from weekend_activity.tracker import WeekendActivityTracker

tracker = WeekendActivityTracker(config_path="config.yaml")
```

#### Methods

##### `get_date_range(target_date: Optional[datetime] = None) -> Tuple[datetime, datetime]`

Get the start and end dates for the weekend containing or before the target date.

```python
start_date, end_date = tracker.get_date_range()
```

##### `fetch_activity(start_date: datetime, end_date: datetime) -> Dict[str, Any]`

Fetch GitHub activity for the specified date range.

```python
activity = tracker.fetch_activity(start_date, end_date)
```

Returns a dictionary with:
- `commits`: Dictionary mapping usernames to lists of commit data
- `prs`: Dictionary mapping usernames to lists of PR data
- `period`: Dictionary with start and end timestamps

##### `generate_summary(activity: Dict[str, Any], format: str = "slack") -> str`

Generate a summary of the activity in the specified format.

```python
summary = tracker.generate_summary(activity, format="text")
```

Supported formats:
- `"slack"`: Formatted for Slack with markdown and link formatting
- `"text"`: Plain text format for terminal output

##### `send_slack_notification(message: str) -> None`

Send a message to Slack using the configured webhook.

```python
tracker.send_slack_notification(summary)
```

## Configuration Schema

The configuration file (`config.yaml`) supports the following structure:

```yaml
repositories:
  - owner: str  # GitHub organization or username
    repo: str   # Repository name

timezone: str   # IANA timezone name

slack:
  channel: str       # Slack channel name
  username: str      # Bot username
  icon_emoji: str    # Bot emoji icon

summary:
  max_commits_per_user: int   # Maximum commits to show per user
  max_prs_per_user: int       # Maximum PRs to show per user
  include_commit_messages: bool
  include_pr_titles: bool
```

## CLI Interface

The command-line interface is implemented using Click and provides the following commands:

### `report`

Generate an activity report.

Options:
- `--date`: Target date (YYYY-MM-DD format)
- `--config`: Path to config file
- `--format`: Output format (text/slack)
- `--notify/--no-notify`: Send to Slack

### `add-repo`

Add a repository to track.

Arguments:
- `repo`: Repository in format "owner/repo"

Options:
- `--config`: Path to config file
