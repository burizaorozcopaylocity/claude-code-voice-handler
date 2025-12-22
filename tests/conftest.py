"""
Pytest Configuration - The Stage Setup.

Like setting up the stage before the show, this module
configures fixtures and shared test utilities.
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add src to path for imports FIRST, before the parent directory
# This ensures the package is found before the wrapper script
_src_path = str(Path(__file__).parent.parent / "src")
_parent_path = str(Path(__file__).parent.parent)

# Remove parent directory if present (to avoid voice_handler.py shadowing)
if _parent_path in sys.path:
    sys.path.remove(_parent_path)

# Insert src at the beginning
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config():
    """Provide a mock configuration for testing (Pydantic-validated)."""
    from voice_handler.config_schema import VoiceConfig

    # Create config with defaults + test overrides
    config = VoiceConfig(
        voice_settings={
            "tts_provider": "system",
            "openai_voice": "nova",
            "user_nickname": "TestRockstar",
            "personality": "rockstar"
        }
    )

    # Return as dict for handler compatibility
    return config.model_dump()


@pytest.fixture
def mock_transcript(temp_dir):
    """Create a mock transcript file for testing."""
    transcript_path = temp_dir / "test_transcript.jsonl"

    # Create sample transcript entries
    entries = [
        {
            "type": "user",
            "message": {"role": "user", "content": "Test prompt"}
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "This is a test response from Claude."}]
            },
            "timestamp": "2024-01-01T00:00:00Z",
            "uuid": "test-uuid-1"
        },
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Task completed successfully!"}]
            },
            "timestamp": "2024-01-01T00:00:01Z",
            "uuid": "test-uuid-2"
        }
    ]

    with open(transcript_path, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    yield transcript_path


@pytest.fixture
def mock_stdin_data():
    """Provide mock stdin data for hook processing."""
    return {
        "session_id": "test-session-12345",
        "transcript_path": "/tmp/test_transcript.jsonl",
        "prompt": "Please help me write a test",
        "tool_name": "Read",
        "tool_input": {
            "file_path": "/path/to/test.py"
        }
    }


@pytest.fixture
def clean_singletons():
    """Clean up singleton instances between tests."""
    # Import singletons
    from voice_handler.utils import logger as logger_module
    from voice_handler.core import state as state_module
    from voice_handler.core import session as session_module
    from voice_handler.queue import broker as broker_module
    from voice_handler.queue import producer as producer_module
    from voice_handler.queue import consumer as consumer_module
    from voice_handler.ai import qwen as qwen_module

    yield

    # Reset singletons after test
    logger_module._logger_instance = None
    state_module._state_manager_instance = None
    session_module._session_voice_manager = None
    broker_module._broker_instance = None
    producer_module._producer_instance = None
    consumer_module._consumer_instance = None
    qwen_module._qwen_generator = None


# Skip TTS tests if OpenAI not configured
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "requires_openai: marks tests requiring OpenAI API"
    )
    config.addinivalue_line(
        "markers", "requires_qwen: marks tests requiring qwen-code CLI"
    )
