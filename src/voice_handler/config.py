#!/usr/bin/env python3
"""
Configuration Module - The Sound Engineer's Control Board.

Loads configuration from environment variables and .env files.
Like setting up the mixing console before the show!
"""

import os
import threading
import json
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
            load_dotenv(env_path, override=True)
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
    voice_enabled: bool = field(
        default_factory=lambda: os.getenv("VOICE_ENABLED", "true").lower() == "true"
    )
    use_async_queue: bool = field(
        default_factory=lambda: os.getenv("USE_ASYNC_QUEUE", "false").lower() == "true"
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


def is_voice_enabled() -> bool:
    """Check if voice announcements are enabled."""
    return get_config().runtime.voice_enabled


# ============================================================================
# CONFIG.JSON VALIDATION (Pydantic)
# ============================================================================

from voice_handler.config_schema import VoiceConfig
from pydantic import ValidationError

_voice_config_singleton: Optional[VoiceConfig] = None
_voice_config_lock = threading.Lock()


def load_config_json(
    config_path: Optional[Path] = None,
    fail_on_invalid: bool = True,
    logger=None
) -> VoiceConfig:
    """
    Load and validate config.json with Pydantic.

    Args:
        config_path: Path to config.json (auto-detect if None)
        fail_on_invalid: If True, raise on validation error. If False, return defaults.
        logger: Optional logger for error reporting

    Returns:
        Validated VoiceConfig instance

    Raises:
        ValidationError: If fail_on_invalid=True and config is invalid
        Exception: If fail_on_invalid=True and file cannot be read
    """
    # Auto-detect config path
    if config_path is None:
        possible_paths = [
            Path(__file__).parent.parent.parent / "config.json",  # voice_notifications/config.json
            Path.home() / ".claude" / "hooks" / "voice_notifications" / "config.json",
        ]
        for path in possible_paths:
            if path.exists():
                config_path = path
                break

    # Load JSON
    if config_path and config_path.exists():
        try:
            config_data = json.loads(config_path.read_text(encoding='utf-8'))

            # Validate with Pydantic
            validated = VoiceConfig(**config_data)

            if logger:
                logger.log_info(f"Config validated successfully from {config_path}")

            return validated

        except ValidationError as e:
            error_msg = f"Invalid config.json: {e}"

            if logger:
                logger.log_error(error_msg, exception=e)

            if fail_on_invalid:
                raise
            else:
                # Graceful fallback
                if logger:
                    logger.log_warning("Using default config due to validation errors")
                return VoiceConfig()

        except Exception as e:
            error_msg = f"Failed to load config.json: {e}"

            if logger:
                logger.log_error(error_msg, exception=e)

            if fail_on_invalid:
                raise
            else:
                return VoiceConfig()
    else:
        # No config.json found
        if logger:
            logger.log_warning("config.json not found, using defaults")
        return VoiceConfig()


def get_voice_config(reload: bool = False) -> VoiceConfig:
    """
    Get singleton VoiceConfig instance.

    Args:
        reload: Force reload from disk

    Returns:
        Cached or freshly loaded VoiceConfig
    """
    global _voice_config_singleton

    if _voice_config_singleton is None or reload:
        with _voice_config_lock:
            if _voice_config_singleton is None or reload:
                _voice_config_singleton = load_config_json(fail_on_invalid=False)

    return _voice_config_singleton


def reload_voice_config() -> VoiceConfig:
    """Force reload of config.json (useful after API updates)."""
    return get_voice_config(reload=True)
