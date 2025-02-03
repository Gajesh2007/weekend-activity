# Usage Guide

## Basic Usage

Generate a report for the most recent weekend:

```bash
weekend-activity report
```

## Command Options

### Report Command

```bash
# Get activity for a specific date
weekend-activity report --date 2024-02-03

# Generate a Slack-formatted report
weekend-activity report --format slack

# Send the report directly to Slack
weekend-activity report --format slack --notify

# Use a different config file
weekend-activity report --config custom-config.yaml
```

### Repository Management

Add a new repository to track:

```bash
weekend-activity add-repo "owner/repo"
```

## Output Formats

### Text Format

The text format is designed for terminal output and includes:
- Weekend date range
- List of contributors
- Commit messages with URLs
- PR titles with URLs

Example:
```
Weekend Warriors Report
Activity from 2024-02-03T00:00:00Z to 2024-02-05T00:00:00Z

@username
  • 3 commits:
    - Update documentation
      https://github.com/org/repo/commit/123
    - Fix bug in parser
      https://github.com/org/repo/commit/456
  • 1 pull request:
    - Add new feature
      https://github.com/org/repo/pull/789
```

### Slack Format

The Slack format includes:
- Rich formatting with emojis
- Clickable links
- Compact layout for better readability

## Automation

### Cron Job

Add to your crontab to run every Monday morning:

```bash
0 9 * * 1 cd /path/to/weekend-activity && poetry run weekend-activity report --format slack --notify
```

### Systemd Service

1. Copy service files:
```bash
sudo cp scripts/systemd/weekend-activity.* /etc/systemd/system/
```

2. Edit service file to set environment variables
3. Enable and start the timer:
```bash
sudo systemctl enable weekend-activity.timer
sudo systemctl start weekend-activity.timer
```

## Troubleshooting

Common issues and solutions:

1. **GitHub Token Issues**
   - Ensure the token has repo access
   - Check the token is correctly set in environment

2. **Timezone Issues**
   - Use IANA timezone names (e.g., "America/New_York")
   - UTC is used by default

3. **No Activity Found**
   - Verify repository configuration
   - Check date range is correct
   - Ensure commits/PRs are in the weekend timeframe
