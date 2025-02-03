# Weekend Activity Tracker

A bot that tracks weekend activity (commits, PRs) on specified GitHub repositories and generates summaries for contributors who code during weekends. The goal is to encourage weekend hacking and recognize employees who show extra initiative.

## Features

- Track commits and PRs made during weekends (Saturday and Sunday)
- Generate a Monday morning summary of weekend activities
- AI-powered summaries of commits and PRs with impact assessment
  - Smart filtering of diffs to focus on important code changes
  - Ignores lock files, build artifacts, and other non-essential changes
  - Provides impact level assessment (LOW/MEDIUM/HIGH)
- Send notifications to Slack with contributor shoutouts
- Support for monitoring multiple GitHub repositories
- Simple time zone handling (initially using UTC)
- CLI interface for easy testing and configuration
- SQLite database for persistent storage and caching

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

1. Create a `.env` file with your API keys:
   ```bash
   # Required: GitHub token with repo access
   GITHUB_TOKEN=your_github_token

   # Required for AI summaries: OpenAI API key
   # Must be a regular API key starting with 'sk-'
   OPENAI_API_KEY=your_openai_api_key

   # Optional: Slack webhook for notifications
   SLACK_WEBHOOK_URL=your_slack_webhook_url
   ```

2. Create a `config.yaml` file with your repositories:
   ```yaml
   # List of repositories to track
   repositories:
     - owner: "organization-name"
       repo: "repository-name"

   # Timezone for weekend detection (IANA timezone names)
   timezone: "UTC"

   # Slack notification settings (optional)
   slack:
     channel: "#weekend-activity"
     username: "Weekend Activity Bot"
     icon_emoji: ":rocket:"

   # Summary generation settings
   summary:
     max_commits_per_user: 10
     max_prs_per_user: 5
     include_commit_messages: true
     include_pr_titles: true
   ```

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

## AI Summaries

The tool uses OpenAI's GPT models to generate intelligent summaries of commits and PRs. For each new activity:

1. The diff is analyzed and filtered to focus on important changes:
   - Excludes lock files, build artifacts, and dependencies
   - Prioritizes source code files over documentation and config files
   - Truncates large diffs to focus on the most relevant parts

2. The AI generates:
   - A concise summary of the changes and their purpose
   - An impact assessment (LOW/MEDIUM/HIGH) based on:
     - Scope of changes (number of files, lines changed)
     - Complexity of modifications
     - Type of files modified (source code vs. config vs. docs)

3. Summaries are stored in the database and included in reports

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
