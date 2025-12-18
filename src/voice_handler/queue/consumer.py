#!/usr/bin/env python3
"""
Queue Consumer - The Background Roadie

Like the tireless roadie working behind the scenes,
the consumer processes voice messages from the queue
and sends them to the TTS provider.

Runs as a daemon thread, continuously processing
messages without blocking the main application.
"""

import time
import threading
from typing import Optional, Callable
from queue import PriorityQueue

from voice_handler.queue.broker import (
    MessageBroker,
    VoiceMessage,
    MessageType,
    get_broker,
)


class QueueConsumer:
    """
    Background consumer that processes voice messages.

    Features:
    - Runs in a daemon thread
    - Priority-based message ordering
    - Automatic retry on failure
    - Graceful shutdown handling
    - Rate limiting to prevent speech overlap
    """

    def __init__(
        self,
        broker: Optional[MessageBroker] = None,
        speak_callback: Optional[Callable[[str, str], None]] = None,
        logger=None,
        min_speech_delay: float = 1.0,
    ):
        """
        Initialize the consumer.

        Args:
            broker: MessageBroker instance
            speak_callback: Function to call for TTS (text, voice) -> None
            logger: Optional logger
            min_speech_delay: Minimum delay between speeches
        """
        self.logger = logger
        self.broker = broker or get_broker(logger=logger)
        self.speak_callback = speak_callback
        self.min_speech_delay = min_speech_delay

        # Thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_speech_time = 0.0

        # Priority queue for ordering messages
        self._priority_queue = PriorityQueue()

    def set_speak_callback(self, callback: Callable[[str, str], None]):
        """Set the TTS callback function."""
        self.speak_callback = callback

    def _process_message(self, message: VoiceMessage) -> bool:
        """
        Process a single message.

        Args:
            message: The message to process

        Returns:
            bool: True if processed successfully
        """
        if not self.speak_callback:
            if self.logger:
                self.logger.log_warning("No speak callback set, skipping message")
            return False

        try:
            # Enforce minimum delay between speeches
            now = time.time()
            time_since_last = now - self._last_speech_time
            if time_since_last < self.min_speech_delay:
                time.sleep(self.min_speech_delay - time_since_last)

            # Call the TTS provider
            self.speak_callback(message.text, message.voice)
            self._last_speech_time = time.time()

            if self.logger:
                self.logger.log_debug(f"Spoke: {message.text[:50]}...")

            return True

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error processing message", exception=e)
            return False

    def _consumer_loop(self):
        """Main consumer loop - runs in daemon thread."""
        if self.logger:
            self.logger.log_info("Consumer loop started - ready to rock!")

        while self._running:
            try:
                # Try to get a message from the broker
                message = self.broker.dequeue(timeout=0.5)

                if message:
                    # Check for shutdown signal
                    if message.message_type == MessageType.SHUTDOWN:
                        if self.logger:
                            self.logger.log_info("Shutdown signal received - B.O.!")
                        self.broker.ack(message)
                        break

                    # Process the message
                    success = self._process_message(message)

                    if success:
                        self.broker.ack(message)
                    else:
                        # Retry failed messages
                        self.broker.nack(message)

            except Exception as e:
                if self.logger:
                    self.logger.log_error("Error in consumer loop", exception=e)
                time.sleep(0.5)  # Avoid tight loop on errors

        if self.logger:
            self.logger.log_info("Consumer loop ended - show's over!")

    def start(self):
        """Start the consumer in a daemon thread."""
        if self._running:
            if self.logger:
                self.logger.log_warning("Consumer already running")
            return

        self._running = True
        self._thread = threading.Thread(
            target=self._consumer_loop,
            name="VoiceConsumer",
            daemon=True,  # Dies when main process exits
        )
        self._thread.start()

        if self.logger:
            self.logger.log_info("Consumer thread started")

    def stop(self, wait: bool = True, timeout: float = 5.0):
        """
        Stop the consumer.

        Args:
            wait: Whether to wait for the thread to finish
            timeout: Maximum wait time
        """
        if not self._running:
            return

        self._running = False

        # Send shutdown signal
        self.broker.send_shutdown()

        if wait and self._thread:
            self._thread.join(timeout=timeout)

        if self.logger:
            self.logger.log_info("Consumer stopped")

    def is_running(self) -> bool:
        """Check if consumer is running."""
        return self._running and self._thread and self._thread.is_alive()


# Singleton consumer instance
_consumer_instance: Optional[QueueConsumer] = None


def get_consumer(logger=None) -> QueueConsumer:
    """Get or create the queue consumer singleton."""
    global _consumer_instance
    if _consumer_instance is None:
        _consumer_instance = QueueConsumer(logger=logger)
    return _consumer_instance
