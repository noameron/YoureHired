"""
Tests for the repo analyst agent module.

These tests verify the RepoAnalysisBatch model that wraps
multiple AnalysisResult instances for batch processing.
"""

import pytest
from pydantic import ValidationError

from app.agents.repo_analyst_agent import RepoAnalysisBatch, repo_analyst_agent
from app.schemas.scout import AnalysisResult


def test_batch_validates_with_valid_results():
    """
    GIVEN a valid AnalysisResult
    WHEN creating a RepoAnalysisBatch with it
    THEN the batch should validate successfully
    """
    # GIVEN
    valid_result = AnalysisResult(
        repo="fastapi/fastapi",
        fit_score=8.5,
        reason="Great for learning web frameworks",
        contributions=["Add examples", "Improve docs"],
        reject=False,
    )

    # WHEN
    batch = RepoAnalysisBatch(results=[valid_result])

    # THEN
    assert len(batch.results) == 1
    assert batch.results[0].repo == "fastapi/fastapi"
    assert batch.results[0].fit_score == 8.5


def test_batch_rejects_score_outside_range():
    """
    GIVEN an AnalysisResult with fit_score > 10
    WHEN creating a RepoAnalysisBatch
    THEN ValidationError should be raised
    """
    # GIVEN
    invalid_result = {
        "repo": "owner/repo",
        "fit_score": 11.0,  # Invalid: > 10.0
        "reason": "Test",
        "reject": False,
    }

    # WHEN / THEN
    with pytest.raises(ValidationError) as exc_info:
        RepoAnalysisBatch(results=[invalid_result])

    assert "fit_score" in str(exc_info.value)


def test_batch_accepts_empty_results():
    """
    GIVEN no results
    WHEN creating a RepoAnalysisBatch with empty list
    THEN the batch should validate successfully
    """
    # GIVEN / WHEN
    batch = RepoAnalysisBatch(results=[])

    # THEN
    assert len(batch.results) == 0
    assert batch.results == []


def test_repo_analyst_agent_has_no_input_guardrails_but_has_output_guardrails():
    """
    GIVEN the repo_analyst_agent
    WHEN checking its guardrail configuration
    THEN it should have NO input guardrails (empty list)
    AND it should have output guardrails (non-empty list)
    """
    # GIVEN
    agent = repo_analyst_agent

    # WHEN
    input_guardrails = agent.input_guardrails
    output_guardrails = agent.output_guardrails

    # THEN
    assert input_guardrails == [], (
        f"Expected no input guardrails, but found: {input_guardrails}"
    )
    assert len(output_guardrails) > 0, (
        "Expected output guardrails to be present for data leakage protection"
    )
