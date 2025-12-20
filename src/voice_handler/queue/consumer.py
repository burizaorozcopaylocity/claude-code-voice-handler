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
        max_retries: int = 3,
        retry_backoff_base: float = 0.5,
    ):
        """
        Initialize the consumer.

        Args:
            broker: MessageBroker instance
            speak_callback: Function to call for TTS (text, voice) -> None
            logger: Optional logger
            min_speech_delay: Minimum delay between speeches
            max_retries: Maximum number of retry attempts
            retry_backoff_base: Base delay for exponential backoff
        """
        self.logger = logger
        self.broker = broker or get_broker(logger=logger)
        self.speak_callback = speak_callback
        self.min_speech_delay = min_speech_delay
        self.max_retries = max_retries
        self.retry_backoff_base = retry_backoff_base

        # Thread control
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_speech_time = 0.0

        # Priority queue for ordering messages
        self._priority_queue = PriorityQueue()

    def set_speak_callback(self, callback: Callable[[str, str], None]):
        """Set the TTS callback function."""
        self.speak_callback = callback

    def _process_message(self, message: VoiceMessage) -> tuple:
        """
        Process a single message.

        Args:
            message: The message to process

        Returns:
            tuple[bool, str]: (success, reason)
        """
        if not self.speak_callback:
            if self.logger:
                self.logger.log_warning("No speak callback set, skipping message")
            return False, "no_callback"

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

            return True, "success"

        except Exception as e:
            if self.logger:
                self.logger.log_error("Error processing message", exception=e)
            return False, "exception"

    def _calculate_backoff_delay(self, retry_count: int) -> float:
        """Calculate exponential backoff delay."""
        if retry_count == 0:
            return 0.0
        elif retry_count == 1:
            return 0.5
        elif retry_count == 2:
            return 1.0
        elif retry_count == 3:
            return 2.0
        elif retry_count == 4:
            return 5.0
        else:
            return 10.0

    def _should_retry(self, message: VoiceMessage, reason: str) -> bool:
        """Determine if message should be retried."""
        if reason == "no_callback":
            return False

        retry_count = message.metadata.get('retry_count', 0)
        if retry_count >= self.max_retries:
            if self.logger:
                self.logger.log_warning(
                    f"Message exceeded max retries ({self.max_retries}), dropping: {message.text[:50]}..."
                )
            return False

        return True

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

                    # Get retry metadata
                    retry_count = message.metadata.get('retry_count', 0)
                    last_retry_time = message.metadata.get('last_retry_time')

                    # Apply exponential backoff if this is a retry
                    if retry_count > 0 and last_retry_time:
                        backoff_delay = self._calculate_backoff_delay(retry_count)
                        elapsed = time.time() - last_retry_time
                        if elapsed < backoff_delay:
                            # Too soon to retry, put back in queue
                            self.broker.nack(message)
                            continue

                    # Process the message
                    success, reason = self._process_message(message)

                    if success:
                        # Success - acknowledge and remove from queue
                        self.broker.ack(message)
                    else:
                        # Failure - determine if should retry
                        if self._should_retry(message, reason):
                            # Update retry metadata
                            message.metadata['retry_count'] = retry_count + 1
                            message.metadata['last_retry_time'] = time.time()

                            # Nack to put back in queue for retry
                            self.broker.nack(message)

                            if self.logger:
                                self.logger.log_warning(
                                    f"Message failed (retry #{retry_count + 1}/{self.max_retries}): {message.text[:50]}..."
                                )
                        else:
                            # Don't retry - ack to remove from queue
                            self.broker.ack(message)

                            if self.logger:
                                self.logger.log_error(
                                    f"Message dropped (reason: {reason}): {message.text[:50]}..."
                                )

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
