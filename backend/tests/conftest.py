"""Shared test fixtures and utilities."""

from unittest.mock import MagicMock


def mock_streamed_result(final_output):
    """Create a mock that behaves like RunResultStreaming.

    This helper is used across multiple test files to simulate
    the behavior of agents.result.RunResultStreaming objects.
    """
    mock = MagicMock()
    mock.final_output = final_output
    mock.is_complete = True

    async def empty_stream():
        return
        yield  # makes it an async generator

    mock.stream_events = empty_stream
    return mock
