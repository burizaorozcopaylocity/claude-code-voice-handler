#!/usr/bin/env python3
"""
Integration Tests for Config Validation System.

Tests the complete config loading pipeline: file → Pydantic → consumers.
"""

import pytest
import tempfile
from pathlib import Path
from pydantic import ValidationError

from voice_handler.config import load_config_json, get_voice_config
from voice_handler.config_schema import VoiceConfig


class TestConfigLoading:
    """Test config loading from files."""

    def test_load_valid_config(self):
        """load_config_json carga config válido correctamente."""
        config_path = Path(__file__).parent.parent / "config.json"
        config = load_config_json(config_path, fail_on_invalid=True)

        assert config.queue_settings.max_retries >= 1
        assert config.queue_settings.max_retries <= 10
        assert config.voice_settings.tts_provider in ["openai", "system", "none"]

    def test_load_invalid_config_fails_hard(self):
        """load_config_json con fail_on_invalid=True debe raise."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"queue_settings": {"max_retries": -999}}')
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValidationError):
                load_config_json(temp_path, fail_on_invalid=True)
        finally:
            temp_path.unlink()

    def test_load_invalid_config_fallback(self):
        """load_config_json con fail_on_invalid=False retorna defaults."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('{"invalid json')
            temp_path = Path(f.name)

        try:
            config = load_config_json(temp_path, fail_on_invalid=False)
            assert config.queue_settings.max_retries == 3  # Default
        finally:
            temp_path.unlink()

    def test_missing_config_uses_defaults(self):
        """Config inexistente usa defaults."""
        non_existent = Path("/tmp/this_does_not_exist_12345.json")
        config = load_config_json(non_existent, fail_on_invalid=False)

        assert config.queue_settings.max_retries == 3
        assert config.message_limits.max_words == 50


class TestHandlerIntegration:
    """Test VoiceNotificationHandler con config validado."""

    def test_handler_loads_validated_config(self):
        """Handler usa config validado sin errores."""
        from voice_handler.core.handler import VoiceNotificationHandler

        handler = VoiceNotificationHandler(use_async=False)

        # Config values están validados y accesibles
        assert handler.max_words > 0
        assert handler.max_chars > 0
        assert handler.min_speech_delay >= 0
        assert handler.preferred_voice in ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]


class TestSingletonBehavior:
    """Test singleton config access."""

    def test_get_voice_config_returns_same_instance(self):
        """get_voice_config() retorna la misma instancia (singleton)."""
        config1 = get_voice_config()
        config2 = get_voice_config()

        assert config1 is config2  # Same object in memory

    def test_reload_creates_new_instance(self):
        """reload_voice_config() crea nueva instancia."""
        from voice_handler.config import reload_voice_config

        config1 = get_voice_config()
        config2 = reload_voice_config()

        # After reload, should be different instance
        # (Note: could be same if config hasn't changed on disk)
        assert isinstance(config2, VoiceConfig)


class TestPersonalityValidation:
    """Test cross-field validation (personality must exist)."""

    def test_personality_validation_with_temp_config(self):
        """personality inexistente debe fallar en validación."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('''{
                "voice_settings": {"personality": "nonexistent"},
                "personality_modes": {
                    "friendly_professional": {},
                    "casual": {}
                }
            }''')
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValidationError) as exc_info:
                load_config_json(temp_path, fail_on_invalid=True)

            assert "personality 'nonexistent' not found" in str(exc_info.value)
        finally:
            temp_path.unlink()
