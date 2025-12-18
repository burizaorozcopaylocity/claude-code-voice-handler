"""
Utility Tests - Testing the Roadie Toolkit.

These tests verify the utility modules work correctly.
"""

import pytest
import time
import tempfile
from pathlib import Path


class TestMessageDeduplicator:
    """Tests for the message deduplication system."""

    def test_deduplicator_detects_exact_duplicate(self):
        """Duplicate messages should be detected."""
        from voice_handler.utils.dedup import MessageDeduplicator

        dedup = MessageDeduplicator(cache_duration=5.0)

        # First message should not be duplicate
        assert dedup.is_duplicate("Hello world") is False

        # Same message should be duplicate
        assert dedup.is_duplicate("Hello world") is True

    def test_deduplicator_allows_different_messages(self):
        """Different messages should not be flagged as duplicates."""
        from voice_handler.utils.dedup import MessageDeduplicator

        dedup = MessageDeduplicator(cache_duration=5.0)

        assert dedup.is_duplicate("Message one") is False
        assert dedup.is_duplicate("Message two") is False
        assert dedup.is_duplicate("Message three") is False

    def test_deduplicator_cache_expiry(self):
        """Messages should be allowed again after cache expires."""
        from voice_handler.utils.dedup import MessageDeduplicator

        dedup = MessageDeduplicator(cache_duration=0.1)  # Very short cache

        assert dedup.is_duplicate("Test message") is False
        assert dedup.is_duplicate("Test message") is True

        # Wait for cache to expire
        time.sleep(0.15)

        # Should be allowed again
        assert dedup.is_duplicate("Test message") is False

    def test_deduplicator_clear_cache(self):
        """Cache clearing should allow all messages again."""
        from voice_handler.utils.dedup import MessageDeduplicator

        dedup = MessageDeduplicator()

        dedup.is_duplicate("Test message")
        assert dedup.is_duplicate("Test message") is True

        dedup.clear_cache()

        assert dedup.is_duplicate("Test message") is False

    def test_deduplicator_empty_message(self):
        """Empty messages should not be flagged as duplicates."""
        from voice_handler.utils.dedup import MessageDeduplicator

        dedup = MessageDeduplicator()

        assert dedup.is_duplicate("") is False
        assert dedup.is_duplicate(None) is False


class TestTranscriptReader:
    """Tests for the transcript reader."""

    def test_transcript_reader_extracts_messages(self, mock_transcript):
        """Transcript reader should extract assistant messages."""
        from voice_handler.utils.transcript import TranscriptReader

        reader = TranscriptReader(str(mock_transcript))
        messages = reader.extract_recent_messages(since_position=0)

        assert len(messages) == 2
        assert "test response" in messages[0]['text'].lower()

    def test_transcript_reader_get_last_message(self, mock_transcript):
        """Should get the last message from transcript."""
        from voice_handler.utils.transcript import TranscriptReader

        reader = TranscriptReader(str(mock_transcript))
        last_msg = reader.get_last_message()

        assert last_msg is not None
        assert "completed" in last_msg.lower()

    def test_transcript_reader_clean_message(self):
        """Should clean messages for speech."""
        from voice_handler.utils.transcript import TranscriptReader

        reader = TranscriptReader("/nonexistent/path")

        # Code blocks should be handled
        assert reader.clean_message_for_speech("Text ```code``` more text") == "Text"

        # JSON should return None
        assert reader.clean_message_for_speech('{"key": "value"}') is None

        # Markdown should be cleaned
        cleaned = reader.clean_message_for_speech("**bold** and *italic*")
        assert "**" not in cleaned
        assert "*" not in cleaned

    def test_transcript_reader_detect_approval(self):
        """Should detect approval request patterns."""
        from voice_handler.utils.transcript import TranscriptReader

        reader = TranscriptReader("/nonexistent/path")

        assert reader.detect_approval_request("Would you like me to proceed?") is True
        assert reader.detect_approval_request("I need your approval for this") is True
        assert reader.detect_approval_request("Here is the result") is False


class TestSpeechLock:
    """Tests for the speech lock system."""

    def test_speech_lock_acquires(self, temp_dir):
        """Lock should be acquirable."""
        from voice_handler.utils.lock import SpeechLock

        lock_file = temp_dir / "test.lock"
        lock = SpeechLock(str(lock_file), timeout=5.0)

        with lock.acquire(min_spacing=0):
            # Lock is held - we're inside the context
            pass

        # Lock released - should be able to acquire again
        with lock.acquire(min_spacing=0):
            pass

    def test_speech_lock_enforces_spacing(self, temp_dir):
        """Lock should enforce minimum spacing between speeches."""
        from voice_handler.utils.lock import SpeechLock

        lock_file = temp_dir / "test.lock"
        lock = SpeechLock(str(lock_file), timeout=5.0)

        start_time = time.time()

        with lock.acquire(min_spacing=0.1):
            pass

        with lock.acquire(min_spacing=0.1):
            pass

        elapsed = time.time() - start_time

        # Should have waited at least 0.1 seconds
        assert elapsed >= 0.1


class TestVoiceLogger:
    """Tests for the voice logger."""

    def test_logger_creates_file(self, temp_dir):
        """Logger should create log file."""
        from voice_handler.utils.logger import VoiceLogger

        log_file = temp_dir / "test.log"
        logger = VoiceLogger(log_file=str(log_file))

        logger.log_info("Test message")

        assert log_file.exists()
        content = log_file.read_text()
        assert "Test message" in content

    def test_logger_log_levels(self, temp_dir):
        """Logger should handle different log levels."""
        from voice_handler.utils.logger import VoiceLogger

        log_file = temp_dir / "test.log"
        logger = VoiceLogger(log_file=str(log_file), debug_mode=True)

        logger.log_debug("Debug message")
        logger.log_info("Info message")
        logger.log_warning("Warning message")
        logger.log_error("Error message")

        content = log_file.read_text()
        assert "Debug message" in content
        assert "Info message" in content
        assert "Warning message" in content
        assert "Error message" in content

    def test_logger_context_logging(self, temp_dir):
        """Logger should include context in messages."""
        from voice_handler.utils.logger import VoiceLogger

        log_file = temp_dir / "test.log"
        logger = VoiceLogger(log_file=str(log_file))

        logger.log_info("Test with context", key1="value1", key2="value2")

        content = log_file.read_text()
        assert "key1" in content
        assert "value1" in content
