"""Commit attribution tracking."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CommitRecord:
    """Record of a commit made during the session."""

    commit_id: str = ""
    branch: str = ""
    message: str = ""
    timestamp: float = 0.0


@dataclass
class PRRecord:
    """Record of a PR created during the session."""

    pr_number: int = 0
    url: str = ""
    title: str = ""
    repository: str = ""


@dataclass
class AttributionTracker:
    """Tracks commits and PRs made during a session."""

    commits: list[CommitRecord] = field(default_factory=list)
    prs: list[PRRecord] = field(default_factory=list)

    def record_commit(self, commit_id: str, branch: str = "", message: str = "") -> None:
        import time

        self.commits.append(
            CommitRecord(commit_id=commit_id, branch=branch, message=message, timestamp=time.time())
        )

    def record_pr(self, pr_number: int, url: str = "", title: str = "", repo: str = "") -> None:
        self.prs.append(PRRecord(pr_number=pr_number, url=url, title=title, repository=repo))
