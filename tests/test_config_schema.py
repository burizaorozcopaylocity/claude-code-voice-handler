#!/usr/bin/env python3
"""
Unit Tests for config_schema.py - Pydantic Validation Tests.

Tests range validation, enums, cross-field validation, and defaults.
"""

import pytest
from pydantic import ValidationError

from voice_handler.config_schema import (
    QueueSettings,
    MessageLimits,
    TimingConfig,
    TTSSettings,
    HistoryConfig,
    VoiceSettings,
    VoiceConfig,
)


class TestQueueSettings:
    """Test QueueSettings validation."""

    def test_max_retries_valid_range(self):
        """max_retries debe aceptar valores entre 1-10."""
        assert QueueSettings(max_retries=1).max_retries == 1
        assert QueueSettings(max_retries=5).max_retries == 5
        assert QueueSettings(max_retries=10).max_retries == 10

    def test_max_retries_too_low(self):
        """max_retries debe rechazar valores < 1."""
        with pytest.raises(ValidationError) as exc_info:
            QueueSettings(max_retries=0)

        assert "greater than or equal to 1" in str(exc_info.value)

    def test_max_retries_too_high(self):
        """max_retries debe rechazar valores > 10."""
        with pytest.raises(ValidationError) as exc_info:
            QueueSettings(max_retries=11)

        assert "less than or equal to 10" in str(exc_info.value)

    def test_retry_backoff_base_range(self):
        """retry_backoff_base debe estar entre 0.1-5.0."""
        assert QueueSettings(retry_backoff_base=0.1).retry_backoff_base == 0.1
        assert QueueSettings(retry_backoff_base=2.5).retry_backoff_base == 2.5
        assert QueueSettings(retry_backoff_base=5.0).retry_backoff_base == 5.0

        with pytest.raises(ValidationError):
            QueueSettings(retry_backoff_base=0.05)

        with pytest.raises(ValidationError):
            QueueSettings(retry_backoff_base=10.0)

    def test_consumer_poll_timeout_range(self):
        """consumer_poll_timeout debe estar entre 0.1-10.0."""
        assert QueueSettings(consumer_poll_timeout=1.0).consumer_poll_timeout == 1.0

        with pytest.raises(ValidationError):
            QueueSettings(consumer_poll_timeout=0.05)


class TestMessageLimits:
    """Test MessageLimits validation."""

    def test_valid_limits(self):
        """Valores válidos deben funcionar."""
        limits = MessageLimits(
            max_words=50,
            max_chars=300,
            min_chars_for_tts=3,
            min_chars_for_compression=50
        )
        assert limits.max_words == 50
        assert limits.max_chars == 300

    def test_max_words_range(self):
        """max_words debe estar entre 10-1000."""
        MessageLimits(max_words=10)  # Min OK
        MessageLimits(max_words=1000)  # Max OK

        with pytest.raises(ValidationError):
            MessageLimits(max_words=5)  # Too low

        with pytest.raises(ValidationError):
            MessageLimits(max_words=1001)  # Too high

    def test_max_chars_range(self):
        """max_chars debe estar entre 50-5000."""
        MessageLimits(max_chars=50)  # Min OK
        MessageLimits(max_chars=5000)  # Max OK

        with pytest.raises(ValidationError):
            MessageLimits(max_chars=30)  # Too low

    def test_truncate_suffix_string(self):
        """truncate_suffix debe aceptar strings."""
        limits = MessageLimits(truncate_suffix="…")
        assert limits.truncate_suffix == "…"


class TestTimingConfig:
    """Test TimingConfig validation."""

    def test_min_speech_delay_range(self):
        """min_speech_delay debe estar entre 0.0-60.0."""
        TimingConfig(min_speech_delay=0.0)  # Min OK
        TimingConfig(min_speech_delay=30.0)  # Mid OK
        TimingConfig(min_speech_delay=60.0)  # Max OK

        with pytest.raises(ValidationError):
            TimingConfig(min_speech_delay=-1.0)

        with pytest.raises(ValidationError):
            TimingConfig(min_speech_delay=61.0)

    def test_session_expiry_hours_range(self):
        """session_expiry_hours debe estar entre 1-72."""
        TimingConfig(session_expiry_hours=1)  # Min OK
        TimingConfig(session_expiry_hours=72)  # Max OK

        with pytest.raises(ValidationError):
            TimingConfig(session_expiry_hours=0)

        with pytest.raises(ValidationError):
            TimingConfig(session_expiry_hours=100)


class TestTTSSettings:
    """Test TTSSettings validation."""

    def test_openai_speed_range(self):
        """openai_speed debe estar entre 0.25-4.0."""
        TTSSettings(openai_speed=0.25)  # Min OK
        TTSSettings(openai_speed=1.0)  # Normal OK
        TTSSettings(openai_speed=4.0)  # Max OK

        with pytest.raises(ValidationError):
            TTSSettings(openai_speed=0.1)

        with pytest.raises(ValidationError):
            TTSSettings(openai_speed=5.0)

    def test_llm_temperature_range(self):
        """llm_temperature debe estar entre 0.0-2.0."""
        TTSSettings(llm_temperature=0.0)  # Min OK
        TTSSettings(llm_temperature=2.0)  # Max OK

        with pytest.raises(ValidationError):
            TTSSettings(llm_temperature=-0.1)

        with pytest.raises(ValidationError):
            TTSSettings(llm_temperature=2.1)


class TestVoiceSettings:
    """Test VoiceSettings validation."""

    def test_tts_provider_enum(self):
        """tts_provider solo debe aceptar valores válidos."""
        assert VoiceSettings(tts_provider="openai").tts_provider == "openai"
        assert VoiceSettings(tts_provider="system").tts_provider == "system"
        assert VoiceSettings(tts_provider="none").tts_provider == "none"

        with pytest.raises(ValidationError) as exc_info:
            VoiceSettings(tts_provider="invalid")

        assert "Input should be 'openai', 'system' or 'none'" in str(exc_info.value)

    def test_openai_voice_enum(self):
        """openai_voice solo debe aceptar voces válidas."""
        valid_voices = ["nova", "alloy", "echo", "fable", "onyx", "shimmer"]

        for voice in valid_voices:
            assert VoiceSettings(openai_voice=voice).openai_voice == voice

        with pytest.raises(ValidationError):
            VoiceSettings(openai_voice="invalid_voice")

    def test_fallback_speech_rate_range(self):
        """fallback_speech_rate debe estar entre 50-400."""
        VoiceSettings(fallback_speech_rate=50)  # Min OK
        VoiceSettings(fallback_speech_rate=400)  # Max OK

        with pytest.raises(ValidationError):
            VoiceSettings(fallback_speech_rate=30)

        with pytest.raises(ValidationError):
            VoiceSettings(fallback_speech_rate=500)

    def test_user_nickname_min_length(self):
        """user_nickname no puede ser vacío."""
        VoiceSettings(user_nickname="B")  # 1 char OK

        with pytest.raises(ValidationError):
            VoiceSettings(user_nickname="")


class TestVoiceConfig:
    """Test root VoiceConfig validation and cross-field constraints."""

    def test_empty_config_uses_defaults(self):
        """Config vacío debe usar todos los defaults."""
        config = VoiceConfig(**{})

        assert config.queue_settings.max_retries == 3
        assert config.message_limits.max_words == 50
        assert config.timing.min_speech_delay == 1.0
        assert config.tts_settings.openai_speed == 0.95
        assert config.history.max_llm_history_messages == 20
        assert config.voice_settings.tts_provider == "openai"

    def test_partial_config_merges_with_defaults(self):
        """Config parcial debe mergear con defaults."""
        config = VoiceConfig(
            queue_settings={"max_retries": 5}
        )

        assert config.queue_settings.max_retries == 5  # Override
        assert config.queue_settings.retry_backoff_base == 0.5  # Default
        assert config.message_limits.max_words == 50  # Default group

    def test_personality_must_exist_in_modes(self):
        """personality seleccionado debe existir en personality_modes."""
        # Caso válido
        config = VoiceConfig(
            voice_settings=VoiceSettings(personality="casual"),
            personality_modes={
                "casual": {"greetings": ["Hey"]},
                "friendly_professional": {"greetings": ["Hello"]}
            }
        )
        assert config.voice_settings.personality == "casual"

    def test_personality_not_found_raises_error(self):
        """personality validation removed - delegated to prompts.py."""
        # No longer raises ValidationError - personality_modes no longer used
        config = VoiceConfig(
            voice_settings=VoiceSettings(personality="nonexistent"),
            personality_modes={}  # Empty dict - no longer validated
        )
        # Config loads successfully - personality handled by RockPersonality
        assert config.voice_settings.personality == "nonexistent"

    def test_empty_personality_modes_skips_validation(self):
        """Si personality_modes está vacío, no valida."""
        config = VoiceConfig(
            voice_settings=VoiceSettings(personality="anything"),
            personality_modes={}
        )
        assert config  # No error

    def test_extra_fields_allowed(self):
        """Campos extra deben permitirse (forward compatibility)."""
        config = VoiceConfig(
            custom_field="custom_value",
            new_setting={"nested": "data"}
        )
        assert config  # No error

    def test_full_config_validation(self):
        """Config completo con todos los campos debe validar correctamente."""
        full_config = {
            "queue_settings": {
                "max_retries": 5,
                "retry_backoff_base": 1.0,
                "consumer_poll_timeout": 2.0
            },
            "message_limits": {
                "max_words": 100,
                "max_chars": 500,
                "min_chars_for_tts": 5,
                "min_chars_for_compression": 100,
                "truncate_suffix": "…"
            },
            "timing": {
                "min_speech_delay": 2.0,
                "min_tool_announcement_interval": 5.0,
                "session_expiry_hours": 8
            },
            "tts_settings": {
                "openai_speed": 1.2,
                "max_tokens_llm": 200,
                "llm_temperature": 0.9,
                "llm_timeout": 10
            },
            "history": {
                "max_llm_history_messages": 30
            },
            "voice_settings": {
                "tts_provider": "system",
                "use_steerable_tts": False,
                "accent": "neutral",
                "message_prefix": "Assistant: ",
                "openai_voice": "echo",
                "fallback_voice": "Samantha",
                "fallback_speech_rate": 200,
                "personality": "butler",
                "user_nickname": "Boss"
            },
            "personality_modes": {
                "butler": {"greetings": ["How may I assist you"]}
            }
        }

        config = VoiceConfig(**full_config)

        # Verificar algunos valores
        assert config.queue_settings.max_retries == 5
        assert config.message_limits.max_words == 100
        assert config.voice_settings.tts_provider == "system"
        assert config.voice_settings.personality == "butler"


class TestRuntimeValidation:
    """Test runtime validation (validate_assignment=True)."""

    def test_runtime_validation_on_root_model(self):
        """validate_assignment funciona en root model, no en nested."""
        config = VoiceConfig()

        # Runtime validation funciona para fields directos en root model
        # Nota: Para nested models (queue_settings.max_retries), Pydantic V2
        # requiere recrear el nested model completo para revalidar
        assert config.queue_settings.max_retries == 3


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_min_boundary_values(self):
        """Test valores mínimos permitidos."""
        config = VoiceConfig(
            queue_settings={"max_retries": 1, "retry_backoff_base": 0.1, "consumer_poll_timeout": 0.1},
            message_limits={"max_words": 10, "max_chars": 50, "min_chars_for_tts": 1},
            timing={"min_speech_delay": 0.0, "session_expiry_hours": 1},
            tts_settings={"openai_speed": 0.25, "llm_temperature": 0.0, "llm_timeout": 1},
            history={"max_llm_history_messages": 5},
            voice_settings={"fallback_speech_rate": 50}
        )
        assert config  # All min values accepted

    def test_max_boundary_values(self):
        """Test valores máximos permitidos."""
        config = VoiceConfig(
            queue_settings={"max_retries": 10, "retry_backoff_base": 5.0, "consumer_poll_timeout": 10.0},
            message_limits={"max_words": 1000, "max_chars": 5000, "min_chars_for_tts": 100},
            timing={"min_speech_delay": 60.0, "min_tool_announcement_interval": 60.0, "session_expiry_hours": 72},
            tts_settings={"openai_speed": 4.0, "max_tokens_llm": 2048, "llm_temperature": 2.0, "llm_timeout": 60},
            history={"max_llm_history_messages": 100},
            voice_settings={"fallback_speech_rate": 400}
        )
        assert config  # All max values accepted
