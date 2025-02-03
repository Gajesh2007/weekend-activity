"""AI-powered code summarization module."""

import os
from typing import Any, Dict, List, Optional

from openai import OpenAI
from rich.console import Console

from weekend_activity.github_client import github
from weekend_activity.models import (
    Commit,
    CommitSummary,
    PullRequest,
    PullRequestSummary,
)

console = Console()

# Initialize OpenAI client
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    console.print(
        "[yellow]Warning: OPENAI_API_KEY not set. AI summaries will be disabled.[/yellow]"
    )
else:
    console.print("[green]OpenAI API key found. AI summaries will be enabled.[/green]")
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Files to ignore in diffs
IGNORED_FILES = {
    # Lock files
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Gemfile.lock",
    "composer.lock",
    # Build artifacts
    "dist/",
    "build/",
    ".next/",
    # Dependencies
    "node_modules/",
    "vendor/",
    # Generated files
    "*.min.js",
    "*.min.css",
    # IDE files
    ".idea/",
    ".vscode/",
    # Misc
    ".DS_Store",
    "Thumbs.db",
}


def should_include_file(filename: str) -> bool:
    """Check if a file should be included in the diff."""
    # Check exact matches
    if filename in IGNORED_FILES:
        return False

    # Check directory patterns
    for pattern in IGNORED_FILES:
        if pattern.endswith("/") and filename.startswith(pattern):
            return False

    # Check file extensions
    if any(
        pattern[1:] in filename for pattern in IGNORED_FILES if pattern.startswith("*.")
    ):
        return False

    return True


def format_diff_for_prompt(diff_data: List[Dict[str, Any]], max_files: int = 5) -> str:
    """Format diff data into a readable string for the AI prompt."""
    if not diff_data:
        return "No changes available"

    # Filter and sort files by importance
    relevant_files = [
        file for file in diff_data if should_include_file(file.get("filename", ""))
    ]

    # Sort files by importance (source code first, then docs, etc.)
    def file_importance(file: Dict[str, Any]) -> int:
        filename = file.get("filename", "").lower()
        if any(ext in filename for ext in [".py", ".js", ".ts", ".go", ".rs", ".java"]):
            return 0  # Source code
        if any(ext in filename for ext in [".md", ".txt", ".rst"]):
            return 1  # Documentation
        if any(ext in filename for ext in [".json", ".yaml", ".yml", ".toml"]):
            return 2  # Config files
        return 3  # Other files

    relevant_files.sort(key=file_importance)

    # Take only the most important files
    selected_files = relevant_files[:max_files]

    formatted = []
    total_files = len(relevant_files)
    if total_files > max_files:
        formatted.append(
            f"Note: Showing {max_files} most important files out of {total_files} total files changed."
        )

    for file in selected_files:
        filename = file.get("filename", "")
        formatted.append(f"\nFile: {filename}")
        formatted.append(f"Changes: +{file.get('additions')} -{file.get('deletions')}")

        if file.get("patch"):
            patch = file.get("patch", "")
            # Only include the most relevant parts of the patch
            patch_lines = patch.split("\n")
            if len(patch_lines) > 50:  # If patch is too long
                # Take first 20 lines and last 20 lines
                formatted_patch = "\n".join(
                    [
                        *patch_lines[:20],
                        f"\n... {len(patch_lines) - 40} lines omitted ...\n",
                        *patch_lines[-20:],
                    ]
                )
            else:
                formatted_patch = patch

            formatted.append("Diff:")
            formatted.append(formatted_patch)

    if not formatted:
        return "No relevant changes to analyze"

    return "\n".join(formatted)


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


def get_commit_diff(commit: Commit) -> List[Dict[str, Any]]:
    """Get the diff for a commit using GitHub API."""
    try:
        # Access the repository through SQLAlchemy relationship
        repo = commit.repository
        gh_repo = github.get_repo(repo.full_name)
        gh_commit = gh_repo.get_commit(commit.sha)
        return gh_commit.raw_data.get("files", [])
    except Exception as e:
        console.print(
            f"[red]Error fetching diff for commit {commit.sha}: {str(e)}[/red]"
        )
        return []


def get_pr_diff(pr: PullRequest) -> List[Dict[str, Any]]:
    """Get the diff for a pull request using GitHub API."""
    try:
        repo = pr.repository
        gh_repo = github.get_repo(repo.full_name)
        gh_pr = gh_repo.get_pull(pr.number)
        files = gh_pr.get_files()
        return [
            {
                "filename": f.filename,
                "additions": f.additions,
                "deletions": f.deletions,
                "patch": f.patch,
            }
            for f in files
        ]
    except Exception as e:
        console.print(f"[red]Error fetching diff for PR #{pr.number}: {str(e)}[/red]")
        return []


def summarize_commit(commit: Commit) -> Optional[CommitSummary]:
    """Generate an AI summary for a commit."""
    if not client:
        console.print(
            "[yellow]Skipping commit summary: OpenAI API key not set[/yellow]"
        )
        return None

    try:
        console.print(f"[blue]Fetching diff for commit {commit.sha[:7]}...[/blue]")
        diff = get_commit_diff(commit)
        formatted_diff = format_diff_for_prompt(diff)

        if not diff:
            console.print(
                f"[yellow]No diff available for commit {commit.sha[:7]}. Skipping summary.[/yellow]"
            )
            return None

        # Prepare the prompt
        prompt = COMMIT_PROMPT.format(message=commit.message, diff=formatted_diff)

        console.print(
            f"[blue]Requesting OpenAI summary for commit {commit.sha[:7]}...[/blue]"
        )

        # Get summary from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Using a more widely available model
            messages=[
                {"role": "system", "content": "You are a code review assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
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

        if not summary_text:
            console.print(
                f"[yellow]Warning: Could not parse AI summary response for commit {commit.sha[:7]}[/yellow]"
            )
            return None

        console.print(
            f"[green]Successfully generated AI summary for commit {commit.sha[:7]}:[/green]"
        )
        console.print(f"[green]Summary: {summary_text}[/green]")
        console.print(f"[green]Impact: {impact_level}[/green]")

        return CommitSummary(
            commit=commit,
            summary=summary_text,
            impact_level=impact_level.lower(),
        )

    except Exception as e:
        console.print(f"[red]Error summarizing commit {commit.sha[:7]}: {str(e)}[/red]")
        return None


def summarize_pr(pr: PullRequest) -> Optional[PullRequestSummary]:
    """Generate an AI summary for a pull request."""
    if not client:
        console.print("[yellow]Skipping PR summary: OpenAI API key not set[/yellow]")
        return None

    try:
        console.print(f"[blue]Fetching diff for PR #{pr.number}...[/blue]")
        diff = get_pr_diff(pr)
        formatted_diff = format_diff_for_prompt(diff)

        if not diff:
            console.print(
                f"[yellow]No diff available for PR #{pr.number}. Skipping summary.[/yellow]"
            )
            return None

        # Prepare the prompt
        prompt = PR_PROMPT.format(
            title=pr.title,
            body=pr.body or "No description provided",
            diff=formatted_diff,
        )

        console.print(f"[blue]Requesting OpenAI summary for PR #{pr.number}...[/blue]")

        # Get summary from OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",  # Using a more widely available model
            messages=[
                {"role": "system", "content": "You are a code review assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
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

        if not summary_text:
            console.print(
                f"[yellow]Warning: Could not parse AI summary response for PR #{pr.number}[/yellow]"
            )
            return None

        console.print(
            f"[green]Successfully generated AI summary for PR #{pr.number}:[/green]"
        )
        console.print(f"[green]Summary: {summary_text}[/green]")
        console.print(f"[green]Impact: {impact_level}[/green]")

        return PullRequestSummary(
            pull_request=pr,
            summary=summary_text,
            impact_level=impact_level.lower(),
        )

    except Exception as e:
        console.print(f"[red]Error summarizing PR #{pr.number}: {str(e)}[/red]")
        return None
