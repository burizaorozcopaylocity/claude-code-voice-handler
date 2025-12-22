#!/usr/bin/env python3
"""
Processor Registry - Strategy Manager.

Maps hook types to their corresponding processor instances.
This is the central registry that VoiceNotificationHandler uses
to delegate hook processing to the appropriate strategy.
"""

from typing import Dict, Optional
from voice_handler.core.processors.base import HookProcessor, ProcessorDependencies


class ProcessorRegistry:
    """
    Registry that manages all hook processors.

    The registry pattern centralizes processor creation and lookup.
    Instead of VoiceNotificationHandler knowing about each processor
    class, it just asks the registry for the right processor.

    This makes it easy to add new processors without modifying the handler:
    1. Create new processor class
    2. Register it here
    3. Done! (Open/Closed Principle)
    """

    def __init__(self, deps: ProcessorDependencies):
        """
        Initialize registry with all processors.

        Args:
            deps: Shared dependencies to inject into each processor
        """
        self.deps = deps
        self._processors: Dict[str, HookProcessor] = {}

        # Register simple processors (Phase 2)
        from voice_handler.core.processors.notification import NotificationProcessor
        from voice_handler.core.processors.session_start import SessionStartProcessor

        self._processors["Notification"] = NotificationProcessor(deps)
        self._processors["SessionStart"] = SessionStartProcessor(deps)

        # Register medium processors (Phase 3)
        from voice_handler.core.processors.user_prompt_submit import UserPromptSubmitProcessor
        from voice_handler.core.processors.stop import StopProcessor

        self._processors["UserPromptSubmit"] = UserPromptSubmitProcessor(deps)
        self._processors["Stop"] = StopProcessor(deps)

        # Register complex processors (Phase 4)
        from voice_handler.core.processors.pre_tool_use import PreToolUseProcessor
        from voice_handler.core.processors.post_tool_use import PostToolUseProcessor

        self._processors["PreToolUse"] = PreToolUseProcessor(deps)
        self._processors["PostToolUse"] = PostToolUseProcessor(deps)

    def get_processor(self, hook_type: str) -> Optional[HookProcessor]:
        """
        Get the processor for a given hook type.

        Args:
            hook_type: Hook type (e.g., "SessionStart", "PreToolUse")

        Returns:
            Processor instance if registered, None otherwise
        """
        return self._processors.get(hook_type)

    def register(self, hook_type: str, processor: HookProcessor) -> None:
        """
        Register a processor for a hook type.

        This allows dynamic registration if needed, though most
        processors are registered in __init__.

        Args:
            hook_type: Hook type to register for
            processor: Processor instance to register
        """
        self._processors[hook_type] = processor

    def list_processors(self) -> Dict[str, str]:
        """
        List all registered processors.

        Useful for debugging and validation.

        Returns:
            Dict mapping hook types to processor class names
        """
        return {
            hook_type: processor.__class__.__name__
            for hook_type, processor in self._processors.items()
        }
