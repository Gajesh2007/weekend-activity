"""AI-powered code summarization module."""

import os
from typing import Dict, Optional

from openai import OpenAI
from rich.console import Console

from weekend_activity.models import (
    Commit,
    CommitSummary,
    PullRequest,
    PullRequestSummary,
)

console = Console()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COMMIT_PROMPT = """
Analyze this git commit and provide a concise summary:

Commit Message:
{message}

Changes:
{diff}

Please provide:
1. A brief (1-2 sentences) summary of the changes
2. Impact level (LOW/MEDIUM/HIGH) based on the scope and complexity of changes

Format the response as:
SUMMARY: <your summary>
IMPACT: <impact level>
"""

PR_PROMPT = """
Analyze this pull request and provide a concise summary:

Title: {title}
Description:
{body}

Changes:
{diff}

Please provide:
1. A brief (2-3 sentences) summary of the changes and their purpose
2. Impact level (LOW/MEDIUM/HIGH) based on the scope and complexity

Format the response as:
SUMMARY: <your summary>
IMPACT: <impact level>
"""


def get_commit_diff(commit: Commit) -> str:
    """Get the diff for a commit using GitHub API."""
    try:
        # Access the repository through SQLAlchemy relationship
        repo = commit.repository
        gh_repo = repo.github_client.get_repo(f"{repo.owner}/{repo.name}")
        gh_commit = gh_repo.get_commit(commit.sha)
        return gh_commit.raw_data.get("files", [])
    except Exception as e:
        console.print(
            f"[red]Error fetching diff for commit {commit.sha}: {str(e)}[/red]"
        )
        return ""


def get_pr_diff(pr: PullRequest) -> str:
    """Get the diff for a pull request using GitHub API."""
    try:
        repo = pr.repository
        gh_repo = repo.github_client.get_repo(f"{repo.owner}/{repo.name}")
        gh_pr = gh_repo.get_pull(pr.number)
        return gh_pr.get_files()
    except Exception as e:
        console.print(f"[red]Error fetching diff for PR #{pr.number}: {str(e)}[/red]")
        return ""


def format_diff_for_prompt(diff_data: Dict) -> str:
    """Format diff data into a readable string for the AI prompt."""
    if not diff_data:
        return "No changes available"

    formatted = []
    for file in diff_data:
        formatted.append(f"File: {file.get('filename')}")
        formatted.append(f"Changes: +{file.get('additions')} -{file.get('deletions')}")
        if file.get("patch"):
            formatted.append("Diff:")
            formatted.append(file.get("patch"))
        formatted.append("")

    return "\n".join(formatted)


def summarize_commit(commit: Commit) -> Optional[CommitSummary]:
    """Generate an AI summary for a commit."""
    try:
        diff = get_commit_diff(commit)
        formatted_diff = format_diff_for_prompt(diff)

        # Prepare the prompt
        prompt = COMMIT_PROMPT.format(message=commit.message, diff=formatted_diff)

        # Get summary from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a code review assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200,
        )

        # Parse response
        content = response.choices[0].message.content
        summary_lines = content.split("\n")

        summary_text = ""
        impact_level = "MEDIUM"  # default

        for line in summary_lines:
            if line.startswith("SUMMARY:"):
                summary_text = line.replace("SUMMARY:", "").strip()
            elif line.startswith("IMPACT:"):
                impact_level = line.replace("IMPACT:", "").strip()

        return CommitSummary(
            commit=commit, summary=summary_text, impact_level=impact_level.lower()
        )

    except Exception as e:
        console.print(f"[red]Error summarizing commit {commit.sha}: {str(e)}[/red]")
        return None


def summarize_pr(pr: PullRequest) -> Optional[PullRequestSummary]:
    """Generate an AI summary for a pull request."""
    try:
        diff = get_pr_diff(pr)
        formatted_diff = format_diff_for_prompt(diff)

        # Prepare the prompt
        prompt = PR_PROMPT.format(
            title=pr.title,
            body=pr.body or "No description provided",
            diff=formatted_diff,
        )

        # Get summary from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a code review assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=300,
        )

        # Parse response
        content = response.choices[0].message.content
        summary_lines = content.split("\n")

        summary_text = ""
        impact_level = "MEDIUM"  # default

        for line in summary_lines:
            if line.startswith("SUMMARY:"):
                summary_text = line.replace("SUMMARY:", "").strip()
            elif line.startswith("IMPACT:"):
                impact_level = line.replace("IMPACT:", "").strip()

        return PullRequestSummary(
            pull_request=pr, summary=summary_text, impact_level=impact_level.lower()
        )

    except Exception as e:
        console.print(f"[red]Error summarizing PR #{pr.number}: {str(e)}[/red]")
        return None
