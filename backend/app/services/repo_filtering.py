"""Client-side filtering engine for GitHub repositories.

Pure functions — no I/O, no state. Filters out non-contribution-worthy
repos (tutorials, awesome-lists, inactive) and scores the rest by
contribution-friendliness signals.
"""

import re

from app.schemas.scout import RepoMetadata

TUTORIAL_PATTERNS = [
    r"\bawesome[-_]",
    r"\btutorial\b",
    r"\blearn[-_]",
    r"\bcheatsheet\b",
    r"\bcourse\b",
    r"\binterview[-_]prep\b",
    r"\bcurated\s+list\b",
    r"\bcoding[-_]challenge\b",
]
_TUTORIAL_RE: re.Pattern[str] = re.compile("|".join(TUTORIAL_PATTERNS), re.IGNORECASE)


def is_tutorial_or_awesome_list(repo: RepoMetadata) -> bool:
    """Detect tutorial, awesome-list, cheatsheet, or course repos."""
    text = f"{repo.name} {repo.description or ''}"
    return bool(_TUTORIAL_RE.search(text))


def has_open_issues(repo: RepoMetadata) -> bool:
    """Repos must have at least one open issue to be contribution-worthy."""
    return repo.open_issue_count > 0


def compute_contribution_score(repo: RepoMetadata) -> float:
    """Score contribution-welcome signals. Higher = more welcoming.

    Max possible: 20 + 15 + 10 = 45.
    """
    score = 0.0
    score += min(repo.good_first_issue_count, 10) * 2.0  # up to 20
    score += min(repo.help_wanted_count, 10) * 1.5  # up to 15
    score += min(repo.open_issue_count, 100) * 0.1  # up to 10
    return score


def apply_filters(
    repos: list[RepoMetadata],
    min_stars: int = 0,
    max_stars: int = 50000,
) -> list[RepoMetadata]:
    """Apply all client-side filters and return sorted candidates.

    Excludes tutorials/awesome-lists, repos with no open issues,
    and repos outside the star range.
    Returns results sorted by contribution score (descending).
    """
    filtered = []
    for repo in repos:
        if is_tutorial_or_awesome_list(repo):
            continue
        if not has_open_issues(repo):
            continue
        if repo.star_count < min_stars or repo.star_count > max_stars:
            continue
        filtered.append(repo)
    filtered.sort(key=lambda r: compute_contribution_score(r), reverse=True)
    return filtered
