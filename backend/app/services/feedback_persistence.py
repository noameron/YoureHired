"""
Feedback persistence service for saving evaluation results as markdown files.
"""
import re
from datetime import datetime
from pathlib import Path

from app.schemas.evaluation import SolutionFeedback

# Base directory for feedback files (relative to project root)
FEEDBACKS_BASE_DIR = Path("docs/drills/feedbacks")


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use in filenames."""
    # Replace spaces and special chars with underscores
    sanitized = re.sub(r"[^\w\-]", "_", name.lower())
    # Collapse multiple underscores
    sanitized = re.sub(r"_+", "_", sanitized)
    # Remove leading/trailing underscores
    return sanitized.strip("_")


def generate_feedback_path(
    company_name: str,
    role: str,
    timestamp: datetime | None = None,
) -> Path:
    """
    Generate the file path for saving feedback.

    Format: docs/drills/feedbacks/<dd-mm-yyyy_hh-mm>/<company_name>_<role>.md

    Args:
        company_name: The target company name
        role: The target role
        timestamp: Optional timestamp (defaults to now)

    Returns:
        Path to the feedback file
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Format timestamp as dd-mm-yyyy_hh-mm
    timestamp_dir = timestamp.strftime("%d-%m-%Y_%H-%M")

    # Sanitize company and role for filename
    safe_company = sanitize_filename(company_name)
    safe_role = sanitize_filename(role)

    filename = f"{safe_company}_{safe_role}.md"

    return FEEDBACKS_BASE_DIR / timestamp_dir / filename


def resolve_duplicate_path(base_path: Path) -> Path:
    """
    If the file already exists, add a numeric suffix.

    Args:
        base_path: The original file path

    Returns:
        A unique path (may have _1, _2, etc. suffix)
    """
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1


def format_feedback_markdown(
    feedback: SolutionFeedback,
    company_name: str,
    role: str,
    drill_title: str,
    timestamp: datetime | None = None,
) -> str:
    """
    Format feedback as a markdown document.

    Args:
        feedback: The evaluation feedback
        company_name: Target company
        role: Target role
        drill_title: Title of the drill that was evaluated
        timestamp: Optional timestamp

    Returns:
        Formatted markdown string
    """
    if timestamp is None:
        timestamp = datetime.now()

    # Format score color indicator
    if feedback.score >= 7:
        score_indicator = "Good"
    elif feedback.score >= 5:
        score_indicator = "Adequate"
    else:
        score_indicator = "Needs Improvement"

    lines = [
        f"# Feedback: {drill_title}",
        "",
        f"**Company:** {company_name}",
        f"**Role:** {role}",
        f"**Date:** {timestamp.strftime('%Y-%m-%d %H:%M')}",
        f"**Score:** {feedback.score}/10 ({score_indicator})",
        "",
        "---",
        "",
        "## Strengths",
        "",
    ]

    for strength in feedback.strengths:
        lines.extend([
            f"### {strength.title}",
            "",
            strength.description,
            "",
        ])

    if not feedback.strengths:
        lines.append("_No specific strengths noted._\n")

    lines.extend([
        "---",
        "",
        "## Areas for Improvement",
        "",
    ])

    for improvement in feedback.improvements:
        lines.extend([
            f"### {improvement.title}",
            "",
            improvement.description,
            "",
            f"**Suggestion:** {improvement.suggestion}",
            "",
        ])

    if not feedback.improvements:
        lines.append("_No specific improvements noted._\n")

    lines.extend([
        "---",
        "",
        "## Summary for Next Practice",
        "",
        feedback.summary_for_next_drill,
        "",
    ])

    return "\n".join(lines)


def save_feedback(
    feedback: SolutionFeedback,
    company_name: str,
    role: str,
    drill_title: str,
    project_root: Path | None = None,
) -> Path:
    """
    Save feedback to a markdown file.

    Args:
        feedback: The evaluation feedback
        company_name: Target company
        role: Target role
        drill_title: Title of the drill
        project_root: Optional project root path (defaults to cwd)

    Returns:
        Path to the saved file (relative to project root)
    """
    if project_root is None:
        project_root = Path.cwd()

    timestamp = datetime.now()

    # Generate path
    relative_path = generate_feedback_path(company_name, role, timestamp)
    absolute_path = project_root / relative_path

    # Handle duplicates
    absolute_path = resolve_duplicate_path(absolute_path)

    # Create directories
    absolute_path.parent.mkdir(parents=True, exist_ok=True)

    # Format content
    content = format_feedback_markdown(
        feedback, company_name, role, drill_title, timestamp
    )

    # Write file
    absolute_path.write_text(content, encoding="utf-8")

    # Return path relative to project root
    return absolute_path.relative_to(project_root)
