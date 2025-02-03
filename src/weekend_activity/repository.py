"""GitHub repository interaction module."""

import os
from datetime import datetime
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from github import Github, GithubException
from rich.console import Console
from sqlalchemy.orm import Session

from weekend_activity.db import get_db
from weekend_activity.models import Commit, PullRequest, Repository
from weekend_activity.summarizer import summarize_commit, summarize_pr

# Load environment variables from .env file
load_dotenv()

console = Console()


class GitHubManager:
    """Manages GitHub repository interactions."""

    def __init__(self) -> None:
        """Initialize with GitHub token."""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError(
                "GITHUB_TOKEN environment variable not set. "
                "Please ensure you have a .env file with GITHUB_TOKEN set."
            )
        self.github = Github(token)

    def sync_repository(self, owner: str, name: str, db: Session) -> Repository:
        """Sync repository information to database."""
        try:
            # Check if repository exists
            repo = db.query(Repository).filter_by(owner=owner, name=name).first()

            if not repo:
                # Create new repository record
                repo = Repository(
                    owner=owner,
                    name=name,
                    full_name=f"{owner}/{name}",
                )
                db.add(repo)
                db.commit()
                db.refresh(repo)

            return repo

        except Exception as e:
            msg = f"Error syncing repository {owner}/{name}: {str(e)}"
            console.print(f"[red]{msg}[/red]")
            raise

    def fetch_weekend_activity(
        self,
        repo: Repository,
        start_date: datetime,
        end_date: datetime,
        db: Session,
    ) -> Tuple[List[Commit], List[PullRequest]]:
        """Fetch weekend activity for a repository."""
        try:
            gh_repo = self.github.get_repo(repo.full_name)
            commits: List[Commit] = []
            pull_requests: List[PullRequest] = []

            # Fetch commits
            gh_commits = gh_repo.get_commits(since=start_date, until=end_date)
            for gh_commit in gh_commits:
                if not gh_commit.author:
                    continue

                # Check if commit exists
                commit = db.query(Commit).filter_by(sha=gh_commit.sha).first()

                if not commit:
                    # Create new commit record
                    commit = Commit(
                        sha=gh_commit.sha,
                        message=gh_commit.commit.message,
                        author_name=gh_commit.commit.author.name,
                        author_email=gh_commit.commit.author.email,
                        author_username=gh_commit.author.login,
                        url=gh_commit.html_url,
                        committed_at=gh_commit.commit.author.date,
                        repository=repo,
                    )
                    db.add(commit)
                    commits.append(commit)

                    # Generate summary if enabled
                    if os.getenv("OPENAI_API_KEY"):
                        summary = summarize_commit(commit)
                        if summary:
                            db.add(summary)

            # Fetch pull requests
            gh_prs = gh_repo.get_pulls(
                state="all",
                sort="created",
                direction="desc",
            )
            for gh_pr in gh_prs:
                if gh_pr.created_at < start_date:
                    break
                if gh_pr.created_at >= end_date:
                    continue

                # Check if PR exists
                pr = (
                    db.query(PullRequest)
                    .filter_by(number=gh_pr.number, repository=repo)
                    .first()
                )

                if not pr:
                    # Create new PR record
                    pr = PullRequest(
                        number=gh_pr.number,
                        title=gh_pr.title,
                        body=gh_pr.body,
                        author_username=gh_pr.user.login,
                        url=gh_pr.html_url,
                        state=gh_pr.state,
                        created_at=gh_pr.created_at,
                        updated_at=gh_pr.updated_at,
                        merged_at=gh_pr.merged_at,
                        repository=repo,
                    )
                    db.add(pr)
                    pull_requests.append(pr)

                    # Generate summary if enabled
                    if os.getenv("OPENAI_API_KEY"):
                        summary = summarize_pr(pr)
                        if summary:
                            db.add(summary)

            db.commit()
            return commits, pull_requests

        except GithubException as e:
            msg = f"GitHub API error for {repo.full_name}: {str(e)}"
            console.print(f"[red]{msg}[/red]")
            raise
        except Exception as e:
            msg = f"Error fetching activity for {repo.full_name}: {str(e)}"
            console.print(f"[red]{msg}[/red]")
            raise

    def get_activity_summary(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> Dict[str, List[Commit | PullRequest]]:
        """Get summary of all weekend activity."""
        with get_db() as db:
            # Get all repositories
            repos = db.query(Repository).all()

            all_activity: Dict[str, List[Commit | PullRequest]] = {
                "commits": [],
                "pull_requests": [],
            }

            for repo in repos:
                commits, prs = self.fetch_weekend_activity(
                    repo,
                    start_date,
                    end_date,
                    db,
                )
                all_activity["commits"].extend(commits)
                all_activity["pull_requests"].extend(prs)

            return all_activity
