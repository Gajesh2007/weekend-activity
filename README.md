# Weekend Activity Tracker

A bot that tracks weekend activity (commits, PRs) on specified GitHub repositories and generates summaries for contributors who code during weekends. The goal is to encourage weekend hacking and recognize employees who show extra initiative.

## Features

- Track commits and PRs made during weekends (Saturday and Sunday)
- Generate a Monday morning summary of weekend activities
- AI-powered summaries of commits and PRs with impact assessment
- Send notifications to Slack with contributor shoutouts
- Support for monitoring multiple GitHub repositories
- Simple time zone handling (initially using UTC)
- CLI interface for easy testing and configuration

## Installation

1. Make sure you have Python 3.8+ and [Poetry](https://python-poetry.org/) installed
2. Clone the repository:
   ```bash
   git clone https://github.com/Gajesh2007/weekend-activity.git
   cd weekend-activity
   ```
3. Install dependencies:
   ```bash
   poetry install
   ```

## Configuration

1. Set up environment variables:
   ```bash
   export GITHUB_TOKEN=your_github_token
   export SLACK_WEBHOOK_URL=your_slack_webhook_url  # Optional, for Slack notifications
   export OPENAI_API_KEY=your_openai_api_key  # Required for AI-powered summaries
   ```

   Or create a `.env` file:
   ```
   GITHUB_TOKEN=your_github_token
   SLACK_WEBHOOK_URL=your_slack_webhook_url  # Optional
   OPENAI_API_KEY=your_openai_api_key  # Must be a regular API key starting with 'sk-'
   ```

2. Create a `config.yaml` file with your repositories:
   ```yaml
   repositories:
     - owner: "organization-name"
       repo: "repository-name"

   timezone: "UTC"  # Default timezone for weekend detection
   slack:
     channel: "#weekend-activity"
     username: "Weekend Activity Bot"
     icon_emoji: ":rocket:"

   summary:
     max_commits_per_user: 10
     max_prs_per_user: 5
     include_commit_messages: true
     include_pr_titles: true
   ```

## Database Setup

The application uses SQLite as its database. Follow these steps to set up the database:

1. Initialize the database and create tables:
   ```bash
   poetry run alembic upgrade head
   ```

This will create a `weekend_activity.db` file in your project directory with the following tables:
- `repositories`: Tracked GitHub repositories
- `commits`: Weekend commits from tracked repositories
- `pull_requests`: Weekend pull requests from tracked repositories
- `commit_summaries`: AI-generated summaries of commits
- `pr_summaries`: AI-generated summaries of pull requests
- `weekend_reports`: Generated weekend activity reports

The database will be automatically populated as you run the tracker and generate reports.

## Usage

The tool provides a CLI interface with several commands:

### Generate a Report

```bash
# Get activity for the most recent weekend
poetry run weekend-activity report

# Get activity for a specific date (finds the nearest weekend)
poetry run weekend-activity report --date 2024-02-03

# Generate a Slack-formatted report
poetry run weekend-activity report --format slack

# Send the report to Slack
poetry run weekend-activity report --format slack --notify

# Use a different config file
poetry run weekend-activity report --config custom-config.yaml
```

### Add a Repository

```bash
# Add a new repository to track
poetry run weekend-activity add-repo "owner/repo"
```

## Development

1. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

2. Run tests:
   ```bash
   poetry run pytest
   ```

3. Format code:
   ```bash
   poetry run black weekend_activity tests
   ```

4. Run linting:
   ```bash
   poetry run flake8 weekend_activity tests
   ```

## Deployment

### As a Cron Job

Add to your crontab:
```bash
0 9 * * 1 cd /path/to/weekend-activity && poetry run weekend-activity report --format slack --notify
```

### As a Systemd Service

1. Copy the service files:
   ```bash
   sudo cp weekend-activity.service /etc/systemd/system/
   sudo cp weekend-activity.timer /etc/systemd/system/
   ```

2. Edit the service file to set your environment variables and paths
3. Enable and start the timer:
   ```bash
   sudo systemctl enable weekend-activity.timer
   sudo systemctl start weekend-activity.timer
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
