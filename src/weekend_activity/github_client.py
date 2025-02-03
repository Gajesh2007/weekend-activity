"""Shared GitHub client module."""

import os

from dotenv import load_dotenv
from github import Github
from rich.console import Console

console = Console()

# Load environment variables first
load_dotenv()

# Initialize GitHub client
github_token = os.getenv("GITHUB_TOKEN")
if not github_token:
    raise ValueError("GITHUB_TOKEN environment variable not set")

console.print(
    f"[blue]Initializing GitHub client with token: {github_token[:8]}...[/blue]"
)
github = Github(github_token)
