"""Tests for task registry module."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from app.services.task_registry import TaskRegistry, run_agent_streamed


class TestTaskRegistry:
    """Tests for TaskRegistry class."""

    def test_register_adds_result_to_session(self):
        # GIVEN a registry and a mock result
        registry = TaskRegistry()
        result = MagicMock()

        # WHEN registering the result
        registry.register("session-1", result)

        # THEN the result is tracked
        assert "session-1" in registry._active
        assert result in registry._active["session-1"]

    def test_register_multiple_results_for_same_session(self):
        # GIVEN a registry with one result
        registry = TaskRegistry()
        result1 = MagicMock()
        result2 = MagicMock()
        registry.register("session-1", result1)

        # WHEN registering another result for the same session
        registry.register("session-1", result2)

        # THEN both results are tracked
        assert len(registry._active["session-1"]) == 2
        assert result1 in registry._active["session-1"]
        assert result2 in registry._active["session-1"]

    def test_register_different_sessions(self):
        # GIVEN a registry
        registry = TaskRegistry()
        result1 = MagicMock()
        result2 = MagicMock()

        # WHEN registering results for different sessions
        registry.register("session-1", result1)
        registry.register("session-2", result2)

        # THEN both sessions are tracked separately
        assert "session-1" in registry._active
        assert "session-2" in registry._active
        assert result1 in registry._active["session-1"]
        assert result2 in registry._active["session-2"]

    def test_unregister_removes_result(self):
        # GIVEN a registry with a result
        registry = TaskRegistry()
        result = MagicMock()
        registry.register("session-1", result)

        # WHEN unregistering the result
        registry.unregister("session-1", result)

        # THEN the result is removed and session is cleaned up
        assert "session-1" not in registry._active

    def test_unregister_keeps_other_results(self):
        # GIVEN a registry with multiple results
        registry = TaskRegistry()
        result1 = MagicMock()
        result2 = MagicMock()
        registry.register("session-1", result1)
        registry.register("session-1", result2)

        # WHEN unregistering one result
        registry.unregister("session-1", result1)

        # THEN only that result is removed
        assert "session-1" in registry._active
        assert result1 not in registry._active["session-1"]
        assert result2 in registry._active["session-1"]

    def test_unregister_nonexistent_session(self):
        # GIVEN an empty registry
        registry = TaskRegistry()
        result = MagicMock()

        # WHEN unregistering from nonexistent session
        # THEN no error is raised
        registry.unregister("session-1", result)
        assert "session-1" not in registry._active

    def test_unregister_nonexistent_result(self):
        # GIVEN a registry with a different result
        registry = TaskRegistry()
        result1 = MagicMock()
        result2 = MagicMock()
        registry.register("session-1", result1)

        # WHEN unregistering a result that was never added
        # THEN no error is raised and existing result remains
        registry.unregister("session-1", result2)
        assert result1 in registry._active["session-1"]

    def test_cancel_all_cancels_incomplete_results(self):
        # GIVEN a registry with incomplete results
        registry = TaskRegistry()
        result1 = MagicMock(is_complete=False)
        result2 = MagicMock(is_complete=False)
        registry.register("session-1", result1)
        registry.register("session-1", result2)

        # WHEN cancelling all
        registry.cancel_all("session-1")

        # THEN all results are cancelled
        result1.cancel.assert_called_once_with(mode="immediate")
        result2.cancel.assert_called_once_with(mode="immediate")
        assert "session-1" not in registry._active

    def test_cancel_all_skips_complete_results(self):
        # GIVEN a registry with mixed complete/incomplete results
        registry = TaskRegistry()
        result1 = MagicMock(is_complete=True)
        result2 = MagicMock(is_complete=False)
        registry.register("session-1", result1)
        registry.register("session-1", result2)

        # WHEN cancelling all
        registry.cancel_all("session-1")

        # THEN only incomplete results are cancelled
        result1.cancel.assert_not_called()
        result2.cancel.assert_called_once_with(mode="immediate")

    def test_cancel_all_nonexistent_session(self):
        # GIVEN an empty registry
        registry = TaskRegistry()

        # WHEN cancelling nonexistent session
        # THEN no error is raised
        registry.cancel_all("session-1")

    def test_cleanup_removes_session(self):
        # GIVEN a registry with an incomplete result
        registry = TaskRegistry()
        result = MagicMock(is_complete=False)
        registry.register("session-1", result)

        # WHEN cleaning up
        registry.cleanup("session-1")

        # THEN incomplete result is cancelled and session is removed
        result.cancel.assert_called_once_with(mode="immediate")
        assert "session-1" not in registry._active

    def test_cleanup_nonexistent_session(self):
        # GIVEN an empty registry
        registry = TaskRegistry()

        # WHEN cleaning up nonexistent session
        # THEN no error is raised
        registry.cleanup("session-1")

    def test_cleanup_cancels_incomplete_results(self):
        # GIVEN a registry with 2 incomplete results
        registry = TaskRegistry()
        result1 = MagicMock(is_complete=False)
        result2 = MagicMock(is_complete=False)
        registry.register("session-1", result1)
        registry.register("session-1", result2)

        # WHEN cleaning up
        registry.cleanup("session-1")

        # THEN both results are cancelled
        result1.cancel.assert_called_once_with(mode="immediate")
        result2.cancel.assert_called_once_with(mode="immediate")
        # AND session is removed
        assert "session-1" not in registry._active

    def test_cleanup_skips_complete_results(self):
        # GIVEN a registry with 1 complete and 1 incomplete result
        registry = TaskRegistry()
        result_complete = MagicMock(is_complete=True)
        result_incomplete = MagicMock(is_complete=False)
        registry.register("session-1", result_complete)
        registry.register("session-1", result_incomplete)

        # WHEN cleaning up
        registry.cleanup("session-1")

        # THEN only incomplete result is cancelled
        result_complete.cancel.assert_not_called()
        result_incomplete.cancel.assert_called_once_with(mode="immediate")
        # AND session is removed
        assert "session-1" not in registry._active

    def test_register_after_cancel_all_immediately_cancels(self):
        # GIVEN a session that has been cancelled
        registry = TaskRegistry()
        result1 = MagicMock(is_complete=False)
        registry.register("session-1", result1)
        registry.cancel_all("session-1")

        # WHEN registering a new result after cancellation
        result2 = MagicMock(is_complete=False)
        registry.register("session-1", result2)

        # THEN the new result is immediately cancelled
        result2.cancel.assert_called_once_with(mode="immediate")
        # AND the result is not left in _active (cleaned up)
        active_results = registry._active.get("session-1", [])
        assert "session-1" not in registry._active or result2 not in active_results

    def test_cleanup_clears_cancelled_flag(self):
        # GIVEN a session with a result that gets cancelled
        registry = TaskRegistry()
        result_initial = MagicMock(is_complete=False)
        registry.register("session-1", result_initial)
        registry.cancel_all("session-1")

        # WHEN cleanup is called to clear the cancelled flag
        registry.cleanup("session-1")

        # THEN a newly registered result is NOT cancelled
        result_new = MagicMock(is_complete=False)
        registry.register("session-1", result_new)

        # AND the new result was not cancelled
        result_new.cancel.assert_not_called()
        # AND the new result is in _active
        assert "session-1" in registry._active
        assert result_new in registry._active["session-1"]

    def test_cancel_then_register_then_cleanup_full_cycle(self):
        # GIVEN a registry with an initial result
        registry = TaskRegistry()
        result1 = MagicMock(is_complete=False)
        registry.register("session-1", result1)

        # WHEN cancelling all (result1 cancelled, session marked cancelled)
        registry.cancel_all("session-1")

        # THEN result1 is cancelled
        result1.cancel.assert_called_once_with(mode="immediate")

        # WHEN registering result2 (should be immediately cancelled)
        result2 = MagicMock(is_complete=False)
        registry.register("session-1", result2)

        # THEN result2 is immediately cancelled
        result2.cancel.assert_called_once_with(mode="immediate")

        # WHEN calling cleanup (clears cancelled flag)
        registry.cleanup("session-1")

        # WHEN registering result3 (should NOT be cancelled)
        result3 = MagicMock(is_complete=False)
        registry.register("session-1", result3)

        # THEN result3 is NOT cancelled
        result3.cancel.assert_not_called()
        # AND result3 is in _active
        assert "session-1" in registry._active
        assert result3 in registry._active["session-1"]

    def test_thread_safety_concurrent_register(self):
        # GIVEN a registry
        registry = TaskRegistry()
        results = [MagicMock() for _ in range(100)]

        # WHEN registering from multiple threads
        import threading

        def register_results(start, end):
            for i in range(start, end):
                registry.register("session-1", results[i])

        threads = [
            threading.Thread(target=register_results, args=(i * 10, (i + 1) * 10))
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # THEN all results are registered
        assert len(registry._active["session-1"]) == 100

    def test_is_cancelled_returns_false_for_unknown_session(self):
        # GIVEN a fresh registry
        registry = TaskRegistry()

        # WHEN checking if an unknown session is cancelled
        result = registry.is_cancelled("session-1")

        # THEN it returns False
        assert result is False

    def test_is_cancelled_returns_true_after_cancel_all(self):
        # GIVEN a registry with a result that gets cancelled
        registry = TaskRegistry()
        result = MagicMock(is_complete=False)
        registry.register("session-1", result)

        # WHEN calling cancel_all
        registry.cancel_all("session-1")

        # THEN is_cancelled returns True
        assert registry.is_cancelled("session-1") is True

    def test_is_cancelled_returns_false_after_cleanup(self):
        # GIVEN a session that has been cancelled
        registry = TaskRegistry()
        result = MagicMock(is_complete=False)
        registry.register("session-1", result)
        registry.cancel_all("session-1")

        # WHEN calling cleanup
        registry.cleanup("session-1")

        # THEN is_cancelled returns False
        assert registry.is_cancelled("session-1") is False


class TestRunAgentStreamed:
    """Tests for run_agent_streamed function."""

    @pytest.mark.asyncio
    async def test_successful_completion(self):
        # GIVEN a mock agent and result
        agent = MagicMock()
        result_mock = MagicMock()
        result_mock.final_output = "test output"
        result_mock.is_complete = True

        async def mock_stream():
            return
            yield  # Make it an async generator

        result_mock.stream_events = mock_stream

        with patch("app.services.task_registry.Runner.run_streamed", return_value=result_mock):
            with patch("app.services.task_registry.task_registry") as registry_mock:
                # WHEN running agent
                output = await run_agent_streamed(agent, "test input", "session-1", timeout=1.0)

                # THEN output is returned and registry is cleaned up
                assert output == "test output"
                registry_mock.register.assert_called_once_with("session-1", result_mock)
                registry_mock.unregister.assert_called_once_with("session-1", result_mock)

    @pytest.mark.asyncio
    async def test_timeout_cancels_and_cleans_up(self):
        # GIVEN a mock agent that times out
        agent = MagicMock()
        result_mock = MagicMock()

        async def slow_stream():
            await asyncio.sleep(10)  # Exceed timeout
            yield  # Make it an async generator

        result_mock.stream_events = slow_stream

        with patch("app.services.task_registry.Runner.run_streamed", return_value=result_mock):
            with patch("app.services.task_registry.task_registry") as registry_mock:
                # WHEN running agent with timeout
                # THEN TimeoutError is raised
                with pytest.raises(TimeoutError):
                    await run_agent_streamed(agent, "test input", "session-1", timeout=0.01)

                # AND result is cancelled and unregistered
                result_mock.cancel.assert_called_once_with(mode="immediate")
                registry_mock.unregister.assert_called_once_with("session-1", result_mock)

    @pytest.mark.asyncio
    async def test_exception_during_streaming_cleans_up(self):
        # GIVEN a mock agent that raises during streaming
        agent = MagicMock()
        result_mock = MagicMock()

        async def error_stream():
            raise RuntimeError("Stream error")
            yield  # Make it an async generator

        result_mock.stream_events = error_stream

        with patch("app.services.task_registry.Runner.run_streamed", return_value=result_mock):
            with patch("app.services.task_registry.task_registry") as registry_mock:
                # WHEN running agent that errors
                # THEN exception propagates
                with pytest.raises(RuntimeError, match="Stream error"):
                    await run_agent_streamed(agent, "test input", "session-1", timeout=1.0)

                # AND registry is cleaned up
                registry_mock.unregister.assert_called_once_with("session-1", result_mock)

    @pytest.mark.asyncio
    async def test_returns_none_when_agent_returns_none(self):
        # GIVEN a mock agent that returns None
        agent = MagicMock()
        result_mock = MagicMock()
        result_mock.final_output = None
        result_mock.is_complete = True

        async def mock_stream():
            return
            yield  # Make it an async generator

        result_mock.stream_events = mock_stream

        with patch("app.services.task_registry.Runner.run_streamed", return_value=result_mock):
            with patch("app.services.task_registry.task_registry") as registry_mock:
                # WHEN running agent
                output = await run_agent_streamed(agent, "test input", "session-1", timeout=1.0)

                # THEN None is returned and cleanup happens
                assert output is None
                registry_mock.unregister.assert_called_once_with("session-1", result_mock)

    @pytest.mark.asyncio
    async def test_multiple_concurrent_agents_same_session(self):
        # GIVEN multiple agents running for same session
        agent = MagicMock()

        async def create_result(output_value):
            result_mock = MagicMock()
            result_mock.final_output = output_value
            result_mock.is_complete = True

            async def mock_stream():
                await asyncio.sleep(0.01)  # Simulate work
                return
                yield

            result_mock.stream_events = mock_stream
            return result_mock

        results = [await create_result(f"output-{i}") for i in range(3)]

        with patch(
            "app.services.task_registry.Runner.run_streamed", side_effect=results
        ):
            # WHEN running multiple agents concurrently
            outputs = await asyncio.gather(
                run_agent_streamed(agent, "input-1", "session-1", timeout=1.0),
                run_agent_streamed(agent, "input-2", "session-1", timeout=1.0),
                run_agent_streamed(agent, "input-3", "session-1", timeout=1.0),
            )

            # THEN all outputs are returned correctly
            assert outputs == ["output-0", "output-1", "output-2"]
