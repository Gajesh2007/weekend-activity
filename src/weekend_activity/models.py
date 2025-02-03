"""Database models for the weekend activity tracker."""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class Repository(Base):
    """Repository model."""

    __tablename__ = "repositories"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(100))
    name: Mapped[str] = mapped_column(String(100))
    full_name: Mapped[str] = mapped_column(String(201))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    commits: Mapped[list["Commit"]] = relationship(back_populates="repository")
    pull_requests: Mapped[list["PullRequest"]] = relationship(
        back_populates="repository"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Repository {self.full_name}>"


class Commit(Base):
    """Commit model."""

    __tablename__ = "commits"

    id: Mapped[int] = mapped_column(primary_key=True)
    sha: Mapped[str] = mapped_column(String(40), unique=True)
    message: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String(100))
    author_email: Mapped[str] = mapped_column(String(100))
    author_username: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(255))
    committed_at: Mapped[datetime] = mapped_column(DateTime)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    repository: Mapped[Repository] = relationship(back_populates="commits")
    summary: Mapped[Optional["CommitSummary"]] = relationship(back_populates="commit")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Commit {self.sha[:7]} by {self.author_username}>"


class PullRequest(Base):
    """Pull request model."""

    __tablename__ = "pull_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int]
    title: Mapped[str] = mapped_column(String(255))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    author_username: Mapped[str] = mapped_column(String(100))
    url: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(20))  # open, closed, merged
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
    merged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    repository_id: Mapped[int] = mapped_column(ForeignKey("repositories.id"))

    repository: Mapped[Repository] = relationship(back_populates="pull_requests")
    summary: Mapped[Optional["PullRequestSummary"]] = relationship(
        back_populates="pull_request"
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<PR #{self.number} by {self.author_username}>"


class CommitSummary(Base):
    """AI-generated summary for a commit."""

    __tablename__ = "commit_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    commit_id: Mapped[int] = mapped_column(ForeignKey("commits.id"), unique=True)
    summary: Mapped[str] = mapped_column(Text)
    impact_level: Mapped[str] = mapped_column(String(20))  # low, medium, high
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    commit: Mapped[Commit] = relationship(back_populates="summary")

    def __repr__(self) -> str:
        """String representation."""
        return f"<CommitSummary for {self.commit.sha[:7]}>"


class PullRequestSummary(Base):
    """AI-generated summary for a pull request."""

    __tablename__ = "pr_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    pull_request_id: Mapped[int] = mapped_column(
        ForeignKey("pull_requests.id"), unique=True
    )
    summary: Mapped[str] = mapped_column(Text)
    impact_level: Mapped[str] = mapped_column(String(20))  # low, medium, high
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    pull_request: Mapped[PullRequest] = relationship(back_populates="summary")

    def __repr__(self) -> str:
        """String representation."""
        return f"<PRSummary for #{self.pull_request.number}>"


class WeekendReport(Base):
    """Generated weekend activity report."""

    __tablename__ = "weekend_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_date: Mapped[datetime] = mapped_column(DateTime)
    end_date: Mapped[datetime] = mapped_column(DateTime)
    report_text: Mapped[str] = mapped_column(Text)
    sent_to_slack: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """String representation."""
        return f"<WeekendReport {self.start_date.date()} to {self.end_date.date()}>"
