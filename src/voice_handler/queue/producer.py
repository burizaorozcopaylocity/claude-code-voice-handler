#!/usr/bin/env python3
"""
Queue Producer - The Quick Handoff

Like a roadie quickly handing off equipment, the producer
enqueues voice messages and returns immediately without
waiting for TTS processing.

This is what Claude hooks call - fast and non-blocking.
"""

import time
from typing import Optional, Dict, Any

from voice_handler.queue.broker import (
    MessageBroker,
    VoiceMessage,
    MessageType,
    get_broker,
)


class QueueProducer:
    """
    Fast message producer for Claude hooks.

    The producer's job is to:
    1. Accept voice requests from hooks
    2. Package them into queue messages
    3. Enqueue and return immediately

    This keeps Claude Code responsive while voice
    processing happens in the background.
    """

    def __init__(self, broker: Optional[MessageBroker] = None, logger=None):
        """
        Initialize the producer.

        Args:
            broker: MessageBroker instance (creates one if not provided)
            logger: Optional logger
        """
        self.logger = logger
        self.broker = broker or get_broker(logger=logger)

    def speak(
        self,
        text: str,
        voice: str = "nova",
        session_id: Optional[str] = None,
        message_type: MessageType = MessageType.SPEAK,
        priority: int = 5,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Queue a message for speaking.

        Args:
            text: Text to speak
            voice: OpenAI voice to use
            session_id: Session identifier for voice selection
            message_type: Type of message
            priority: Priority (1-10, higher = more urgent)
            metadata: Additional context

        Returns:
            bool: True if queued successfully
        """
        message = VoiceMessage(
            message_type=message_type,
            text=text,
            voice=voice,
            session_id=session_id,
            priority=priority,
            metadata=metadata or {},
        )

        success = self.broker.enqueue(message)

        if self.logger:
            if success:
                self.logger.log_debug(f"Queued: {text[:50]}...")
            else:
                self.logger.log_warning(f"Failed to queue: {text[:50]}...")

        return success

    def speak_greeting(
        self,
        text: str,
        voice: str = "nova",
        session_id: Optional[str] = None,
    ) -> bool:
        """Queue a greeting message (high priority)."""
        return self.speak(
            text=text,
            voice=voice,
            session_id=session_id,
            message_type=MessageType.GREETING,
            priority=8,
        )

    def speak_completion(
        self,
        text: str,
        voice: str = "nova",
        session_id: Optional[str] = None,
    ) -> bool:
        """Queue a completion message (high priority)."""
        return self.speak(
            text=text,
            voice=voice,
            session_id=session_id,
            message_type=MessageType.COMPLETION,
            priority=7,
        )

    def speak_error(
        self,
        text: str,
        voice: str = "nova",
        session_id: Optional[str] = None,
    ) -> bool:
        """Queue an error message (highest priority)."""
        return self.speak(
            text=text,
            voice=voice,
            session_id=session_id,
            message_type=MessageType.ERROR,
            priority=9,
        )

    def speak_approval(
        self,
        text: str,
        voice: str = "nova",
        session_id: Optional[str] = None,
    ) -> bool:
        """Queue an approval request (highest priority)."""
        return self.speak(
            text=text,
            voice=voice,
            session_id=session_id,
            message_type=MessageType.APPROVAL,
            priority=10,
        )

    def clear_queue(self) -> bool:
        """
        Clear all pending messages from the queue.
        
        Useful when voice is disabled to prevent playing old messages
        when voice is re-enabled.
        
        Returns:
            bool: True if queue was cleared successfully
        """
        try:
            self.broker.clear()
            if self.logger:
                self.logger.log_info("Voice queue cleared")
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_error("Failed to clear queue", exception=e)
            return False

    def queue_size(self) -> int:
        """Get current queue size."""
        return self.broker.size()


# Singleton producer instance
_producer_instance: Optional[QueueProducer] = None


def get_producer(logger=None) -> QueueProducer:
    """Get or create the queue producer singleton."""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = QueueProducer(logger=logger)
    return _producer_instance


def quick_speak(text: str, voice: str = "nova", session_id: str = None) -> bool:
    """
    Convenience function for quick non-blocking speak.

    This is the fastest way to queue a voice message from a hook.

    Example:
        from voice_handler.queue.producer import quick_speak
        quick_speak("Task completed!", voice="onyx")
    """
    producer = get_producer()
    return producer.speak(text, voice=voice, session_id=session_id)
