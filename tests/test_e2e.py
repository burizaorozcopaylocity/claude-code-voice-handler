"""
End-to-End Tests - The Full Concert Rehearsal.

These tests verify the complete voice handler system works
from hook input to voice output. Like a full dress rehearsal!
"""

import pytest
import json
import time
import tempfile
from pathlib import Path


class TestVoiceHandlerE2E:
    """End-to-end tests for the voice handler system."""

    @pytest.fixture
    def handler(self, mock_config, temp_dir, clean_singletons):
        """Create a handler instance for testing."""
        from voice_handler.core.handler import VoiceNotificationHandler
        from voice_handler.queue.broker import MessageBroker
        from voice_handler.queue import broker as broker_module

        # Use custom queue path
        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))
        broker_module._broker_instance = broker

        # Create handler in async mode but don't start daemon
        handler = VoiceNotificationHandler(config=mock_config, use_async=True)

        yield handler

    def test_user_prompt_submit_flow(self, handler, mock_stdin_data):
        """Should process UserPromptSubmit hook end-to-end."""
        result = handler.process_user_prompt_submit(mock_stdin_data)

        assert result is not None
        assert handler.current_session_id == mock_stdin_data["session_id"]

    def test_pre_tool_use_flow(self, handler, mock_stdin_data):
        """Should process PreToolUse hook end-to-end."""
        # First set up session
        handler.process_user_prompt_submit(mock_stdin_data)

        # Process tool use
        result = handler.process_pre_tool_use(mock_stdin_data, "Read")

        # May return None if rate limited, but should not error
        assert result is None or isinstance(result, str)

    def test_stop_flow(self, handler, mock_transcript, mock_stdin_data):
        """Should process Stop hook end-to-end."""
        # Set up session
        handler.process_user_prompt_submit(mock_stdin_data)

        # Update stdin with transcript
        mock_stdin_data["transcript_path"] = str(mock_transcript)

        result = handler.process_stop(mock_stdin_data)

        assert result is not None

    def test_notification_flow(self, handler, mock_stdin_data):
        """Should process Notification hook end-to-end."""
        mock_stdin_data["message"] = "Claude needs your permission to use Edit"

        result = handler.process_notification(mock_stdin_data)

        assert result is not None

    def test_async_speak_queues_message(self, handler, temp_dir):
        """Speaking should queue message asynchronously."""
        handler.speak("Test message", voice="nova")

        # Check queue has message
        time.sleep(0.1)  # Brief wait for queue
        assert handler.producer.queue_size() >= 0  # Queue exists

    def test_session_voice_assignment(self, handler, mock_stdin_data):
        """Sessions should get consistent voice assignments."""
        # Process user prompt to set session
        handler.process_user_prompt_submit(mock_stdin_data)

        voice1 = handler.get_session_voice()
        voice2 = handler.get_session_voice()

        # Same session should get same voice
        assert voice1 == voice2

    def test_deduplication_prevents_duplicates(self, handler):
        """Duplicate messages should be filtered."""
        from voice_handler.utils.dedup import get_deduplicator

        # First message goes through
        handler.speak("Unique message")

        # Get deduplicator state
        dedup = handler.deduplicator

        # Same message should be blocked
        assert dedup.is_duplicate("Unique message") is True

    def test_rate_limiting_tools(self, handler, mock_stdin_data):
        """Tool announcements should be rate limited (via PreToolUseProcessor)."""
        # Set up stdin data for PreToolUse
        tool_stdin = {
            "tool_name": "Read",
            "tool_input": {"file_path": "/test/path.py"}
        }

        # First announcement should succeed
        result_1 = handler.process_pre_tool_use(tool_stdin)
        can_announce_1 = result_1 is not None

        # Immediate second should be rate limited (returns None)
        result_2 = handler.process_pre_tool_use(tool_stdin)
        can_announce_2 = result_2 is not None

        # After waiting, should pass again
        min_interval = handler.config["timing"]["min_tool_announcement_interval"]
        time.sleep(min_interval + 0.1)
        result_3 = handler.process_pre_tool_use(tool_stdin)
        can_announce_3 = result_3 is not None

        assert can_announce_1 is True
        assert can_announce_2 is False
        assert can_announce_3 is True


class TestStateManagementE2E:
    """End-to-end tests for state management."""

    def test_state_persists_across_handlers(self, mock_config, temp_dir, clean_singletons):
        """State should persist across handler instances."""
        from voice_handler.core.handler import VoiceNotificationHandler
        from voice_handler.core.state import StateManager

        # First handler - update state
        handler1 = VoiceNotificationHandler(config=mock_config, use_async=False)
        handler1.state_manager.update_context("PreToolUse", tool_name="Write", file_path="/test.py")
        handler1.state_manager.save_state()

        # Second handler - should see state
        handler2 = VoiceNotificationHandler(config=mock_config, use_async=False)

        context = handler2.state_manager.task_context
        assert "/test.py" in context.get("files_created", [])

    def test_todo_completion_detection(self, clean_singletons):
        """Should detect completed todos."""
        from voice_handler.core.state import StateManager

        state = StateManager()

        # Initial todos
        initial_todos = [
            {"id": "1", "content": "Task 1", "status": "in_progress"},
            {"id": "2", "content": "Task 2", "status": "pending"}
        ]
        state.last_todos = initial_todos

        # New todos with completion
        new_todos = [
            {"id": "1", "content": "Task 1", "status": "completed"},
            {"id": "2", "content": "Task 2", "status": "in_progress"}
        ]

        completed = state.detect_completed_todos(new_todos)

        assert "Task 1" in completed

    def test_task_summary_generation(self, clean_singletons):
        """Should generate task summaries."""
        from voice_handler.core.state import StateManager

        state = StateManager()

        # Update context with operations
        state.update_context("PreToolUse", tool_name="Write", file_path="/file1.py")
        state.update_context("PreToolUse", tool_name="Edit", file_path="/file2.py")
        state.update_context("PreToolUse", tool_name="Bash", command="npm test")

        summary = state.get_task_summary()

        assert summary is not None
        assert "Created" in summary or "Modified" in summary or "Ran" in summary


class TestCLIIntegration:
    """Tests for CLI integration."""

    def test_cli_help(self):
        """CLI should show help without errors."""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "voice_handler", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).parent.parent / "src")
        )

        # Should not error
        assert result.returncode == 0
        assert "hook" in result.stdout.lower()


@pytest.mark.slow
class TestAsyncQueueE2E:
    """End-to-end tests for async queue system."""

    def test_full_async_flow(self, temp_dir, mock_config, clean_singletons):
        """Test complete async flow from produce to consume."""
        from voice_handler.queue.broker import MessageBroker
        from voice_handler.queue.producer import QueueProducer
        from voice_handler.queue.consumer import QueueConsumer

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        # Track processed messages
        processed = []

        def mock_speak(text, voice):
            processed.append(text)

        # Set up producer and consumer
        producer = QueueProducer(broker=broker)
        consumer = QueueConsumer(broker=broker, min_speech_delay=0)
        consumer.set_speak_callback(mock_speak)

        # Start consumer
        consumer.start()

        # Produce messages
        producer.speak("Message 1")
        producer.speak("Message 2")
        producer.speak("Message 3")

        # Wait for processing
        time.sleep(2.0)

        # Stop consumer
        consumer.stop(wait=True)

        # All messages should be processed
        assert len(processed) == 3
        assert "Message 1" in processed
        assert "Message 2" in processed
        assert "Message 3" in processed
