#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Setting up development environment...${NC}"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Poetry not found. Installing...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
poetry install --with dev

# Set up pre-commit hooks
echo -e "${GREEN}Setting up pre-commit hooks...${NC}"
poetry run pre-commit install

# Create config file if it doesn't exist
if [ ! -f config.yaml ]; then
    echo -e "${GREEN}Creating config file from example...${NC}"
    cp example.config.yaml config.yaml
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file...${NC}"
    cat > .env << EOL
# GitHub token with repo access
GITHUB_TOKEN=your_github_token_here

# Slack webhook URL (optional)
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
EOL
fi

echo -e "${GREEN}Development environment setup complete!${NC}"
echo -e "${YELLOW}Remember to:${NC}"
echo "1. Edit config.yaml with your repository settings"
echo "2. Set up your environment variables in .env"
echo "3. Run 'make help' to see available commands"
