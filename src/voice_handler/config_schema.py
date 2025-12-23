#!/usr/bin/env python3
"""
Configuration Schema - Pydantic Models for config.json Validation.

Provides type-safe, validated configuration models with range checking,
enum validation, and cross-field validation.
"""

from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Literal, Dict, List, Any


class QueueSettings(BaseModel):
    """Queue retry and polling configuration."""
    max_retries: int = Field(default=3, ge=1, le=10, description="Maximum retry attempts for failed messages")
    retry_backoff_base: float = Field(default=0.5, ge=0.1, le=5.0, description="Base delay for exponential backoff (seconds)")
    consumer_poll_timeout: float = Field(default=1.0, ge=0.1, le=10.0, description="Consumer polling timeout (seconds)")


class MessageLimits(BaseModel):
    """Message truncation and size limits."""
    max_words: int = Field(default=50, ge=10, le=1000, description="Maximum words per message")
    max_chars: int = Field(default=300, ge=50, le=5000, description="Maximum characters per message")
    min_chars_for_tts: int = Field(default=3, ge=1, le=100, description="Minimum characters to trigger TTS")
    min_chars_for_compression: int = Field(default=50, ge=1, description="Minimum characters before LLM compression")
    truncate_suffix: str = Field(default="...", description="Suffix appended to truncated messages")


class TimingConfig(BaseModel):
    """Timing and rate limiting configuration."""
    min_speech_delay: float = Field(default=1.0, ge=0.0, le=60.0, description="Minimum delay between speech outputs (seconds)")
    min_tool_announcement_interval: float = Field(default=3.0, ge=0.0, le=60.0, description="Minimum interval between tool announcements (seconds)")
    session_expiry_hours: int = Field(default=4, ge=1, le=72, description="Session expiry time (hours)")


class TTSSettings(BaseModel):
    """Text-to-Speech provider settings."""
    openai_speed: float = Field(default=0.95, ge=0.25, le=4.0, description="OpenAI TTS playback speed (0.25-4.0)")
    max_tokens_llm: int = Field(default=100, ge=1, le=2048, description="Maximum tokens for LLM compression")
    llm_temperature: float = Field(default=0.8, ge=0.0, le=2.0, description="LLM temperature for message generation")
    llm_timeout: int = Field(default=5, ge=1, le=60, description="LLM request timeout (seconds)")


class HistoryConfig(BaseModel):
    """LLM chat history configuration."""
    max_llm_history_messages: int = Field(default=20, ge=5, le=100, description="Maximum messages in LLM history")


class VoiceSettings(BaseModel):
    """Voice and TTS provider configuration."""
    tts_provider: Literal["openai", "system", "none"] = Field(default="openai", description="TTS provider selection")
    use_steerable_tts: bool = Field(default=True, description="Use OpenAI steerable TTS with accent control")
    accent: str = Field(default="mexicano chilango", description="Accent for steerable TTS")
    message_prefix: str = Field(default="", description="Prefix added to all messages")
    openai_voice: Literal["nova", "alloy", "echo", "fable", "onyx", "shimmer"] = Field(
        default="nova",
        description="OpenAI TTS voice selection"
    )
    openai_voices: Dict[str, str] = Field(
        default_factory=dict,
        description="Available OpenAI voices with descriptions"
    )
    fallback_voice: str = Field(default="Ralph", description="System TTS fallback voice (macOS/Linux)")
    fallback_speech_rate: int = Field(default=180, ge=50, le=400, description="System TTS speech rate (words per minute)")
    personality: str = Field(default="friendly_professional", description="Personality mode selection")
    user_nickname: str = Field(default="Bernard", min_length=1, description="User nickname for personalized messages")


class VoiceConfig(BaseModel):
    """
    Root configuration model with full validation.

    Validates config.json structure, enforces type safety, range checks,
    and cross-field constraints.
    """

    # Core configuration groups (validated)
    queue_settings: QueueSettings = Field(default_factory=QueueSettings, description="Queue retry and polling settings")
    message_limits: MessageLimits = Field(default_factory=MessageLimits, description="Message truncation limits")
    timing: TimingConfig = Field(default_factory=TimingConfig, description="Timing and rate limiting")
    tts_settings: TTSSettings = Field(default_factory=TTSSettings, description="TTS provider settings")
    history: HistoryConfig = Field(default_factory=HistoryConfig, description="LLM history settings")
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings, description="Voice and personality settings")

    # Nested data structures (storage only, no deep validation)
    personality_modes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Personality mode definitions with phrases"
    )
    task_summaries: Dict[str, Any] = Field(
        default_factory=dict,
        description="Task summary templates"
    )
    contextual_phrases: Dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual phrase templates"
    )
    time_aware_greetings: Dict[str, Any] = Field(
        default_factory=dict,
        description="Time-based greeting templates"
    )
    encouragements: List[str] = Field(
        default_factory=list,
        description="Encouragement phrases"
    )
    transition_phrases: List[str] = Field(
        default_factory=list,
        description="Transition phrases for task switching"
    )

    # Validator removed - personality_modes no longer used (delegated to prompts.py)
    # @model_validator(mode='after')
    # def validate_personality_exists(self) -> 'VoiceConfig':
    #     """
    #     Cross-field validator: Ensure selected personality exists in personality_modes.
    #     """
    #     if self.personality_modes and self.voice_settings.personality:
    #         if self.voice_settings.personality not in self.personality_modes:
    #             available = list(self.personality_modes.keys())
    #             raise ValueError(
    #                 f"personality '{self.voice_settings.personality}' not found in personality_modes. "
    #                 f"Available personalities: {available}"
    #             )
    #     return self

    model_config = ConfigDict(
        extra="allow",  # Forward compatibility: allow unknown fields
        validate_assignment=True  # Runtime validation on field updates
    )
