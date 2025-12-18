"""
Queue Tests - Testing the Async Message System.

These tests verify the non-blocking queue system works correctly.
Like a sound check for the PA system!
"""

import pytest
import time
import tempfile
from pathlib import Path


class TestMessageBroker:
    """Tests for the SQLite message broker."""

    def test_broker_enqueue_dequeue(self, temp_dir):
        """Should enqueue and dequeue messages."""
        from voice_handler.queue.broker import MessageBroker, VoiceMessage, MessageType

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        # Enqueue a message
        msg = VoiceMessage(
            message_type=MessageType.SPEAK,
            text="Test message",
            voice="nova",
            priority=5
        )

        assert broker.enqueue(msg) is True
        assert broker.size() == 1

        # Dequeue the message
        received = broker.dequeue(timeout=1.0)

        assert received is not None
        assert received.text == "Test message"
        assert received.voice == "nova"

        # Acknowledge
        broker.ack(received)

    def test_broker_priority_ordering(self, temp_dir):
        """Higher priority messages should be processed first."""
        from voice_handler.queue.broker import MessageBroker, VoiceMessage, MessageType

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        # Enqueue messages with different priorities
        low_priority = VoiceMessage(
            message_type=MessageType.SPEAK,
            text="Low priority",
            priority=1
        )
        high_priority = VoiceMessage(
            message_type=MessageType.SPEAK,
            text="High priority",
            priority=9
        )

        broker.enqueue(low_priority)
        broker.enqueue(high_priority)

        # High priority should come out first
        first = broker.dequeue(timeout=1.0)
        broker.ack(first)

        second = broker.dequeue(timeout=1.0)
        broker.ack(second)

        assert first.text == "High priority"
        assert second.text == "Low priority"

    def test_broker_persistence(self, temp_dir):
        """Queue should persist messages across broker instances."""
        from voice_handler.queue.broker import MessageBroker, VoiceMessage, MessageType

        queue_path = temp_dir / "test_queue.db"

        # First broker - enqueue message
        broker1 = MessageBroker(queue_path=str(queue_path))
        msg = VoiceMessage(
            message_type=MessageType.SPEAK,
            text="Persistent message"
        )
        broker1.enqueue(msg)

        # Second broker - should see the message
        broker2 = MessageBroker(queue_path=str(queue_path))
        received = broker2.dequeue(timeout=1.0)

        assert received is not None
        assert received.text == "Persistent message"

    def test_broker_empty_queue_timeout(self, temp_dir):
        """Dequeue should return None on empty queue after timeout."""
        from voice_handler.queue.broker import MessageBroker

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        start = time.time()
        result = broker.dequeue(timeout=0.5)
        elapsed = time.time() - start

        assert result is None
        assert elapsed >= 0.4  # Should have waited near timeout

    def test_broker_shutdown_message(self, temp_dir):
        """Should be able to send shutdown signal."""
        from voice_handler.queue.broker import MessageBroker, MessageType

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        broker.send_shutdown()

        msg = broker.dequeue(timeout=1.0)
        assert msg is not None
        assert msg.message_type == MessageType.SHUTDOWN


class TestQueueProducer:
    """Tests for the queue producer."""

    def test_producer_speak(self, temp_dir, clean_singletons):
        """Producer should enqueue speak messages."""
        from voice_handler.queue.broker import MessageBroker, get_broker
        from voice_handler.queue.producer import QueueProducer

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))
        producer = QueueProducer(broker=broker)

        result = producer.speak("Test message", voice="onyx")

        assert result is True
        assert broker.size() == 1

    def test_producer_priority_messages(self, temp_dir, clean_singletons):
        """Producer should handle different message priorities."""
        from voice_handler.queue.broker import MessageBroker, MessageType
        from voice_handler.queue.producer import QueueProducer

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))
        producer = QueueProducer(broker=broker)

        producer.speak_greeting("Hello!", voice="nova")
        producer.speak_error("Error occurred!", voice="nova")
        producer.speak_approval("Need approval", voice="nova")

        # Approval (priority 10) should be first
        first = broker.dequeue(timeout=1.0)
        broker.ack(first)

        # Error (priority 9) should be second
        second = broker.dequeue(timeout=1.0)
        broker.ack(second)

        assert first.priority == 10  # Approval
        assert second.priority == 9  # Error

    def test_quick_speak_function(self, temp_dir, clean_singletons):
        """Quick speak function should work."""
        from voice_handler.queue.broker import MessageBroker
        from voice_handler.queue import producer as producer_module

        # Reset singleton and set custom broker
        producer_module._producer_instance = None

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        # Create producer with our broker
        prod = producer_module.QueueProducer(broker=broker)
        producer_module._producer_instance = prod

        # Use quick_speak
        result = producer_module.quick_speak("Quick test")

        assert result is True
        assert broker.size() == 1


class TestQueueConsumer:
    """Tests for the queue consumer."""

    def test_consumer_processes_messages(self, temp_dir, clean_singletons):
        """Consumer should process queued messages."""
        from voice_handler.queue.broker import MessageBroker, VoiceMessage, MessageType
        from voice_handler.queue.consumer import QueueConsumer

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        # Track processed messages
        processed = []

        def mock_speak(text, voice):
            processed.append((text, voice))

        consumer = QueueConsumer(broker=broker, min_speech_delay=0)
        consumer.set_speak_callback(mock_speak)

        # Enqueue a message
        msg = VoiceMessage(
            message_type=MessageType.SPEAK,
            text="Test message",
            voice="nova"
        )
        broker.enqueue(msg)

        # Start consumer
        consumer.start()

        # Wait for processing
        time.sleep(1.0)

        # Stop consumer
        consumer.stop(wait=True)

        assert len(processed) == 1
        assert processed[0][0] == "Test message"
        assert processed[0][1] == "nova"

    def test_consumer_handles_shutdown(self, temp_dir, clean_singletons):
        """Consumer should handle shutdown signal."""
        from voice_handler.queue.broker import MessageBroker
        from voice_handler.queue.consumer import QueueConsumer

        queue_path = temp_dir / "test_queue.db"
        broker = MessageBroker(queue_path=str(queue_path))

        consumer = QueueConsumer(broker=broker)
        consumer.set_speak_callback(lambda t, v: None)

        consumer.start()
        assert consumer.is_running() is True

        consumer.stop(wait=True, timeout=5.0)

        # Give it a moment to fully stop
        time.sleep(0.5)
        assert consumer.is_running() is False
