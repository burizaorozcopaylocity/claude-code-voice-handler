"""
Async Message Queue - The Backstage Crew That Keeps the Show Running.

The async message queue system that ensures Claude never waits for TTS.
Non-blocking, persistent, and rock solid!
"""

from voice_handler.queue.broker import MessageBroker, VoiceMessage, MessageType, get_broker
from voice_handler.queue.producer import QueueProducer, get_producer, quick_speak
from voice_handler.queue.consumer import QueueConsumer, get_consumer
from voice_handler.queue.daemon import VoiceDaemon

__all__ = [
    "MessageBroker",
    "VoiceMessage",
    "MessageType",
    "get_broker",
    "QueueProducer",
    "get_producer",
    "quick_speak",
    "QueueConsumer",
    "get_consumer",
    "VoiceDaemon",
]
