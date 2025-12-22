#!/usr/bin/env python3
"""
Base Processor Interface - Strategy Pattern Foundation.

Defines the abstract base class for all hook processors and the shared
dependency container that gets injected into each processor.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ProcessorDependencies:
    """
    Dependency container for hook processors.

    Instead of each processor managing its own dependencies, we inject
    all shared components through this container. This makes testing
    easier (can mock the entire container) and keeps processors focused.

    Attributes:
        state_manager: Manages session state and task context
        session_voice_manager: Assigns voices to sessions
        qwen: AI generator for personalized responses
        config: Validated configuration dictionary
        logger: Logging instance
    """
    state_manager: Any  # StateManager
    session_voice_manager: Any  # SessionVoiceManager
    qwen: Any  # QwenContextGenerator
    config: Dict[str, Any]
    logger: Any  # Logger


class HookProcessor(ABC):
    """
    Abstract base class for all hook processors.

    Each hook type (SessionStart, UserPromptSubmit, etc.) gets its own
    processor class that implements this interface. This follows the
    Strategy Pattern: each strategy knows how to handle one specific hook.

    Key Design:
    - process(): Does the actual work and returns a message to speak
    - should_process(): Determines if processing should happen (rate limiting, filters)
    - Shared utilities for common tasks (extract session ID, update state)
    """

    def __init__(self, deps: ProcessorDependencies):
        """
        Initialize processor with dependency injection.

        Args:
            deps: Container with all shared dependencies
        """
        self.deps = deps
        self.logger = deps.logger
        self.state_manager = deps.state_manager
        self.session_voice_manager = deps.session_voice_manager
        self.qwen = deps.qwen
        self.config = deps.config

    @abstractmethod
    def process(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Process the hook and return a message to speak.

        This is the core method that each processor must implement.
        It receives stdin data from the hook and returns a message
        that will be queued for TTS.

        Args:
            stdin_data: Data from stdin (hook payload)

        Returns:
            Message to speak, or None to skip speaking
        """
        pass

    def should_process(self, stdin_data: Optional[Dict[str, Any]]) -> bool:
        """
        Determine if this hook should be processed.

        Default implementation allows all processing. Subclasses can
        override to implement rate limiting, filtering, or other checks.

        Args:
            stdin_data: Data from stdin (hook payload)

        Returns:
            True if should process, False to skip
        """
        return True

    # Shared utility methods for common patterns

    def extract_session_id(self, stdin_data: Optional[Dict[str, Any]]) -> Optional[str]:
        """
        Extract session_id from stdin data.

        Common pattern across multiple processors - centralized here
        to avoid duplication.

        Args:
            stdin_data: Data from stdin

        Returns:
            Session ID if present, None otherwise
        """
        if not stdin_data or not isinstance(stdin_data, dict):
            return None
        return stdin_data.get('session_id')

    def update_session_state(self, session_id: str) -> None:
        """
        Update state manager with current session ID.

        Common pattern: When we get a session ID, save it to state
        so it persists across hook calls.

        Args:
            session_id: Session identifier to store
        """
        if session_id:
            self.state_manager.current_session_id = session_id
            self.state_manager.save_state()
