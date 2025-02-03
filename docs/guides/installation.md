# Installation Guide

## Requirements

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/) for dependency management
- A GitHub token with repository access
- (Optional) A Slack webhook URL for notifications

## Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/weekend-activity.git
cd weekend-activity

# Install with poetry
poetry install

# Create your config file
cp example.config.yaml config.yaml
```

## Development Setup

For development, you can use our setup script:

```bash
./scripts/setup-dev.sh
```

This will:
1. Install Poetry if not present
2. Install all dependencies including development tools
3. Set up pre-commit hooks
4. Create initial configuration files

## Environment Variables

Create a `.env` file in the project root:

```bash
# Required: GitHub token with repo access
GITHUB_TOKEN=your_github_token_here

# Optional: Slack webhook URL for notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
```

## Configuration

Edit `config.yaml` to specify which repositories to track:

```yaml
repositories:
  - owner: "your-org"
    repo: "your-repo"

timezone: "UTC"  # Or your preferred timezone
```

See `example.config.yaml` for all available options.

## Verifying Installation

Test your installation:

```bash
# Activate the poetry environment
poetry shell

# Run the CLI
weekend-activity --help

# Run tests
pytest
```
