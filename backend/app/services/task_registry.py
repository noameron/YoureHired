import asyncio
from typing import Any

from agents import Agent, Runner
from agents.result import RunResultStreaming


class TaskRegistry:
    """Tracks active RunResultStreaming objects per session for cancellation."""

    def __init__(self) -> None:
        self._active: dict[str, list[RunResultStreaming]] = {}

    def register(self, session_id: str, result: RunResultStreaming) -> None:
        self._active.setdefault(session_id, []).append(result)

    def cancel_all(self, session_id: str) -> None:
        for result in self._active.pop(session_id, []):
            if not result.is_complete:
                result.cancel(mode="immediate")

    def cleanup(self, session_id: str) -> None:
        self._active.pop(session_id, None)


task_registry = TaskRegistry()


async def run_agent_streamed(
    agent: Agent, input: str, session_id: str, timeout: float
) -> Any:
    """Run agent with streaming, cancellation support, and timeout.

    Replaces the repeated pattern of:
        result = await asyncio.wait_for(Runner.run(agent, input), timeout=...)
        return result.final_output

    Returns final_output (may be None if agent was cancelled mid-run).
    """
    result = Runner.run_streamed(agent, input)
    task_registry.register(session_id, result)
    try:
        async def consume():
            async for _ in result.stream_events():
                pass

        await asyncio.wait_for(consume(), timeout=timeout)
        return result.final_output
    except asyncio.TimeoutError:
        result.cancel(mode="immediate")
        raise
