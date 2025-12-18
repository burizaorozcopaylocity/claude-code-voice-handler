#!/usr/bin/env python3
"""
Configuration Module - The Sound Engineer's Control Board.

Loads configuration from environment variables and .env files.
Like setting up the mixing console before the show!
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

# Load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    # Find .env file (check multiple locations)
    env_locations = [
        Path(__file__).parent.parent.parent / ".env",  # voice_notifications/.env
        Path.home() / ".claude" / "hooks" / "voice_notifications" / ".env",
        Path.cwd() / ".env",
    ]

    for env_path in env_locations:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # python-dotenv not installed, use environment variables only


@dataclass
class UserConfig:
    """User-specific settings."""
    nickname: str = field(default_factory=lambda: os.getenv("USER_NICKNAME", "rockstar"))
    language: str = field(default_factory=lambda: os.getenv("LANGUAGE", "es"))


@dataclass
class LLMConfig:
    """LLM provider settings."""
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "qwen"))

    # Ollama settings
    ollama_model: str = field(default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b"))
    ollama_host: str = field(default_factory=lambda: os.getenv("OLLAMA_HOST", "http://localhost:11434"))

    # Qwen settings
    qwen_max_tokens: int = field(default_factory=lambda: int(os.getenv("QWEN_MAX_TOKENS", "50")))


@dataclass
class TTSConfig:
    """Text-to-Speech settings."""
    provider: str = field(default_factory=lambda: os.getenv("TTS_PROVIDER", "openai"))
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_voice: str = field(default_factory=lambda: os.getenv("OPENAI_VOICE", "nova"))


@dataclass
class PersonalityConfig:
    """Personality settings for the AI roadie."""
    style: str = field(default_factory=lambda: os.getenv("PERSONALITY_STYLE", "rockstar"))


@dataclass
class RuntimeConfig:
    """Runtime behavior settings."""
    use_async_queue: bool = field(
        default_factory=lambda: os.getenv("USE_ASYNC_QUEUE", "true").lower() == "true"
    )
    debug_mode: bool = field(
        default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true"
    )
    min_speech_delay: float = field(
        default_factory=lambda: float(os.getenv("MIN_SPEECH_DELAY", "1.0"))
    )
    tool_announcement_interval: float = field(
        default_factory=lambda: float(os.getenv("TOOL_ANNOUNCEMENT_INTERVAL", "3.0"))
    )


@dataclass
class VoiceHandlerConfig:
    """Main configuration container."""
    user: UserConfig = field(default_factory=UserConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    tts: TTSConfig = field(default_factory=TTSConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    def to_dict(self) -> dict:
        """Convert config to dictionary format (for backward compatibility)."""
        return {
            "voice_settings": {
                "tts_provider": self.tts.provider,
                "openai_voice": self.tts.openai_voice,
                "user_nickname": self.user.nickname,
                "personality": self.personality.style,
            },
            "llm_settings": {
                "provider": self.llm.provider,
                "ollama_model": self.llm.ollama_model,
                "ollama_host": self.llm.ollama_host,
            },
            "runtime": {
                "use_async": self.runtime.use_async_queue,
                "debug": self.runtime.debug_mode,
            }
        }


# Singleton instance
_config: Optional[VoiceHandlerConfig] = None


def get_config() -> VoiceHandlerConfig:
    """Get the singleton configuration instance."""
    global _config
    if _config is None:
        _config = VoiceHandlerConfig()
    return _config


def reload_config() -> VoiceHandlerConfig:
    """Force reload of configuration (useful for testing)."""
    global _config
    _config = VoiceHandlerConfig()
    return _config


# Convenience functions
def get_user_nickname() -> str:
    """Get the user's nickname."""
    return get_config().user.nickname


def get_llm_provider() -> str:
    """Get the LLM provider name."""
    return get_config().llm.provider


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return get_config().runtime.debug_mode
