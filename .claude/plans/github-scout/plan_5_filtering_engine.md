# Plan 5: Filtering Engine

**Branch:** `scout/05-filtering-engine`
**Depends on:** plan_1 (schemas for `RepoMetadata`)
**Blocks:** plan_7
**Parallel with:** plan_4, plan_6

## OpenSpec Context

- Proposal: `openspec/changes/add-github-scout/proposal.md` — "Rule-based filtering engine that reduces thousands of repos to ~20-50 candidates"
- Design: `openspec/changes/add-github-scout/design.md` — Decision 2 (two-phase filtering: server-side qualifiers + client-side rules)
- Tasks: `openspec/changes/add-github-scout/tasks.md` — Task 5.1-5.5

## Production Files (1)

### 1. CREATE `backend/app/services/repo_filtering.py`

Pure functions, no I/O, no state — the most testable module.

```python
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
_TUTORIAL_RE = re.compile("|".join(TUTORIAL_PATTERNS), re.IGNORECASE)


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
    score += min(repo.good_first_issue_count, 10) * 2.0   # up to 20
    score += min(repo.help_wanted_count, 10) * 1.5          # up to 15
    score += min(repo.open_issue_count, 100) * 0.1          # up to 10
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
```

- Regex compiled once at module level for performance
- Sorting by contribution score ensures the analysis cap (50 repos) picks the most promising candidates

## Test Files

- `backend/tests/test_repo_filtering.py`
  - `is_tutorial_or_awesome_list` detects "awesome-python" → `True`
  - `is_tutorial_or_awesome_list` detects "learn-go" → `True`
  - `is_tutorial_or_awesome_list` detects "tutorial" in description → `True`
  - `is_tutorial_or_awesome_list` allows "my-project" → `False`
  - `is_tutorial_or_awesome_list` allows repo with "awesome" not followed by `-` or `_` → `False` (e.g., "awesomeApp")
  - `has_open_issues` with 0 → `False`
  - `has_open_issues` with 1 → `True`
  - `compute_contribution_score` with 10 good-first-issues → 20.0
  - `compute_contribution_score` with 0 everything → 0.0
  - `compute_contribution_score` caps at maximums (>10 good-first-issues still 20.0)
  - `apply_filters` excludes tutorials
  - `apply_filters` excludes repos with 0 open issues
  - `apply_filters` excludes repos outside star range
  - `apply_filters` returns sorted by contribution score desc
  - `apply_filters` with empty input → `[]`
  - `apply_filters` where all repos filtered out → `[]`
  - Star boundary: `min_stars=10`, repo with `star_count=10` → included
  - Star boundary: `max_stars=100`, repo with `star_count=100` → included
  - Star boundary: `max_stars=100`, repo with `star_count=101` → excluded

## Edge Cases

- "awesome-python" → matches `\bawesome[-_]` (word boundary + hyphen)
- "awesomeApp" → does NOT match (no hyphen/underscore after "awesome")
- "my-awesome-project" → DOES match (word boundary before "awesome", hyphen after) — intentionally broad
- Repo with `None` description → `f"{repo.name} {''}"` works without error
- Empty repos list → `apply_filters` returns `[]`
- All repos filtered out → returns `[]`

## Verification

```bash
cd backend && uv run pytest tests/test_repo_filtering.py -v
```
