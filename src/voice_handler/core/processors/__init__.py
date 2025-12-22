#!/usr/bin/env python3
"""
Hook Processors - Strategy Pattern Implementation.

Exports all processors and base classes for the VoiceNotificationHandler.
"""

from voice_handler.core.processors.base import (
    ProcessorDependencies,
    HookProcessor
)
from voice_handler.core.processors.registry import ProcessorRegistry
from voice_handler.core.processors.notification import NotificationProcessor
from voice_handler.core.processors.session_start import SessionStartProcessor
from voice_handler.core.processors.user_prompt_submit import UserPromptSubmitProcessor
from voice_handler.core.processors.stop import StopProcessor
from voice_handler.core.processors.pre_tool_use import PreToolUseProcessor
from voice_handler.core.processors.post_tool_use import PostToolUseProcessor

__all__ = [
    'ProcessorDependencies',
    'HookProcessor',
    'ProcessorRegistry',
    'NotificationProcessor',
    'SessionStartProcessor',
    'UserPromptSubmitProcessor',
    'StopProcessor',
    'PreToolUseProcessor',
    'PostToolUseProcessor',
]
