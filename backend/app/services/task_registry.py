import asyncio
from threading import Lock
from typing import TypeVar

from agents import Agent, Runner
from agents.result import RunResultStreaming

T = TypeVar("T")


class TaskRegistry:
    """Tracks active RunResultStreaming objects per session for cancellation."""

    def __init__(self) -> None:
        self._active: dict[str, list[RunResultStreaming]] = {}
        self._lock = Lock()

    def register(self, session_id: str, result: RunResultStreaming) -> None:
        with self._lock:
            self._active.setdefault(session_id, []).append(result)

    def unregister(self, session_id: str, result: RunResultStreaming) -> None:
        """Remove a specific result from tracking."""
        with self._lock:
            if session_id in self._active:
                try:
                    self._active[session_id].remove(result)
                    # Clean up empty lists
                    if not self._active[session_id]:
                        del self._active[session_id]
                except ValueError:
                    pass  # Already removed

    def cancel_all(self, session_id: str) -> None:
        with self._lock:
            results = self._active.pop(session_id, [])
        for result in results:
            if not result.is_complete:
                result.cancel(mode="immediate")

    def cleanup(self, session_id: str) -> None:
        with self._lock:
            self._active.pop(session_id, None)


task_registry = TaskRegistry()


async def run_agent_streamed(
    agent: Agent[T], agent_input: str, session_id: str, timeout: float
) -> T | None:
    """Run agent with streaming, cancellation support, and timeout.

    Replaces the repeated pattern of:
        result = await asyncio.wait_for(Runner.run(agent, input), timeout=...)
        return result.final_output

    Returns final_output (may be None if agent was cancelled mid-run).
    Automatically cleans up registry after completion or error.
    """
    result = Runner.run_streamed(agent, agent_input)
    task_registry.register(session_id, result)
    try:
        async def consume() -> None:
            async for _ in result.stream_events():
                pass

        await asyncio.wait_for(consume(), timeout=timeout)
        # result.final_output is typed as Any by the agents library
        # Safe to return since we validate agent output_type matches T
        return result.final_output  # type: ignore[no-any-return]
    except TimeoutError:
        result.cancel(mode="immediate")
        raise
    finally:
        # Always cleanup to prevent memory leak
        task_registry.unregister(session_id, result)
