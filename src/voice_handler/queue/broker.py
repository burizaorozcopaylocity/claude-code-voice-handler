#!/usr/bin/env python3
"""
Message Broker - The Backstage Communication Hub

Like the production manager coordinating roadies, this broker
manages the flow of voice messages between Claude hooks and
the TTS worker.

Uses persist-queue with SQLite for reliable, crash-resistant
message passing that survives process restarts.
"""

import os
import sys
import json
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Any, Dict
from enum import Enum

# Import persist-queue for SQLite-backed queue
try:
    from persistqueue import SQLiteAckQueue
    PERSIST_QUEUE_AVAILABLE = True
except ImportError:
    PERSIST_QUEUE_AVAILABLE = False


class MessageType(Enum):
    """Types of voice messages in the queue."""
    SPEAK = "speak"           # Regular TTS message
    GREETING = "greeting"     # Session greeting
    COMPLETION = "completion" # Task completion
    ERROR = "error"           # Error notification
    APPROVAL = "approval"     # Approval request
    SHUTDOWN = "shutdown"     # Shutdown signal


@dataclass
class VoiceMessage:
    """
    A message in the voice queue - like a setlist item.

    Attributes:
        message_type: Type of voice message
        text: The text to speak
        voice: OpenAI voice to use
        session_id: Claude Code session identifier
        priority: Message priority (higher = more urgent)
        timestamp: When the message was created
        metadata: Additional context
    """
    message_type: MessageType
    text: str
    voice: str = "nova"
    session_id: Optional[str] = None
    priority: int = 5
    timestamp: float = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for queue storage."""
        return {
            "message_type": self.message_type.value,
            "text": self.text,
            "voice": self.voice,
            "session_id": self.session_id,
            "priority": self.priority,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceMessage":
        """Create from dictionary retrieved from queue."""
        return cls(
            message_type=MessageType(data["message_type"]),
            text=data["text"],
            voice=data.get("voice", "nova"),
            session_id=data.get("session_id"),
            priority=data.get("priority", 5),
            timestamp=data.get("timestamp", time.time()),
            metadata=data.get("metadata", {}),
        )


class MessageBroker:
    """
    The message broker - like the production desk at a concert.

    Manages a persistent SQLite queue that:
    - Survives process crashes and restarts
    - Supports acknowledgment-based processing
    - Allows retry of failed messages
    - Handles multiple producers (hooks) and one consumer (TTS worker)
    """

    DEFAULT_QUEUE_PATH = None  # Set based on OS

    def __init__(self, queue_path: Optional[str] = None, logger=None):
        """
        Initialize the message broker.

        Args:
            queue_path: Path to the SQLite queue database
            logger: Optional logger instance
        """
        self.logger = logger

        # Determine queue path based on OS
        if queue_path is None:
            if sys.platform == 'win32':
                temp_dir = os.environ.get('TEMP', 'C:\\Temp')
                queue_path = os.path.join(temp_dir, 'claude_voice_queue')
            else:
                queue_path = '/tmp/claude_voice_queue'

        self.queue_path = Path(queue_path)
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize the queue
        self.queue = None
        if PERSIST_QUEUE_AVAILABLE:
            try:
                self.queue = SQLiteAckQueue(
                    str(self.queue_path),
                    multithreading=True,
                    auto_commit=True,
                )
                if self.logger:
                    self.logger.log_info(f"Message broker initialized at {self.queue_path}")
            except Exception as e:
                if self.logger:
                    self.logger.log_error("Failed to initialize queue", exception=e)
        else:
            if self.logger:
                self.logger.log_warning("persist-queue not available, using in-memory fallback")

    def enqueue(self, message: VoiceMessage) -> bool:
        """
        Add a message to the queue.

        Args:
            message: The VoiceMessage to enqueue

        Returns:
            bool: True if successful
        """
        if not self.queue:
            if self.logger:
                self.logger.log_warning("Queue not available, message dropped")
            return False

        try:
            self.queue.put(message.to_dict())
            if self.logger:
                self.logger.log_debug(f"Enqueued message: {message.message_type.value}")
            return True
        except Exception as e:
            if self.logger:
                self.logger.log_error("Failed to enqueue message", exception=e)
            return False

    def dequeue(self, timeout: float = 1.0) -> Optional[VoiceMessage]:
        """
        Get the next message from the queue.

        Args:
            timeout: How long to wait for a message

        Returns:
            VoiceMessage or None if queue is empty
        """
        if not self.queue:
            return None

        try:
            # Non-blocking get with timeout
            data = self.queue.get(timeout=timeout)
            if data:
                return VoiceMessage.from_dict(data)
            return None
        except Exception:
            # Queue is empty or timeout
            return None

    def ack(self, message: VoiceMessage):
        """
        Acknowledge successful processing of a message.

        Args:
            message: The message that was processed
        """
        if self.queue:
            try:
                self.queue.ack(message.to_dict())
            except Exception:
                pass  # Already acked or not in queue

    def nack(self, message: VoiceMessage):
        """
        Negative acknowledge - mark for retry.

        Args:
            message: The message to retry
        """
        if self.queue:
            try:
                self.queue.nack(message.to_dict())
            except Exception:
                pass

    def size(self) -> int:
        """Get the current queue size."""
        if self.queue:
            try:
                return self.queue.size
            except Exception:
                return 0
        return 0

    def clear(self):
        """Clear all messages from the queue."""
        if self.queue:
            try:
                while self.queue.size > 0:
                    item = self.queue.get(timeout=0.1)
                    if item:
                        self.queue.ack(item)
            except Exception:
                pass

    def send_shutdown(self):
        """Send a shutdown signal to the consumer."""
        shutdown_msg = VoiceMessage(
            message_type=MessageType.SHUTDOWN,
            text="",
            priority=10,  # Highest priority
        )
        self.enqueue(shutdown_msg)


# Singleton broker instance
_broker_instance: Optional[MessageBroker] = None


def get_broker(logger=None) -> MessageBroker:
    """Get or create the message broker singleton."""
    global _broker_instance
    if _broker_instance is None:
        _broker_instance = MessageBroker(logger=logger)
    return _broker_instance
