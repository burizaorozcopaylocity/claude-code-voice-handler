#!/usr/bin/env python3
"""
Message deduplication - The Setlist Manager.

Like a stage manager making sure you don't play the same song twice
in one set, this module prevents repeated voice announcements.
"""

import hashlib
import time
from typing import List, Tuple


class MessageDeduplicator:
    """
    Prevents duplicate announcements within a time window.

    The roadie who keeps track of what songs already played tonight.
    """

    def __init__(self, cache_duration: float = 5.0):
        """
        Initialize the deduplicator.

        Args:
            cache_duration: Seconds to keep announcements in cache
        """
        self.cache_duration = cache_duration
        self.recent_announcements: List[Tuple[str, float]] = []
        self.last_announcement_text: str = ""

    def is_duplicate(self, message: str) -> bool:
        """
        Check if this message is a duplicate of a recent announcement.

        Args:
            message: The message to check

        Returns:
            True if this is a duplicate, False otherwise
        """
        if not message:
            return False

        # Check for exact duplicate of last announcement
        if message == self.last_announcement_text:
            return True

        # Create hash of the message for comparison
        message_hash = hashlib.md5(message.encode()).hexdigest()
        current_time = time.time()

        # Clean up old announcements from cache
        self.recent_announcements = [
            (h, t) for h, t in self.recent_announcements
            if current_time - t < self.cache_duration
        ]

        # Check if this message hash is in recent announcements
        for recent_hash, _ in self.recent_announcements:
            if recent_hash == message_hash:
                return True

        # Not a duplicate - add to cache
        self.recent_announcements.append((message_hash, current_time))
        self.last_announcement_text = message
        return False

    def clear_cache(self):
        """Clear the deduplication cache - new setlist, new show!"""
        self.recent_announcements.clear()
        self.last_announcement_text = ""


# Singleton instance
_deduplicator_instance = None


def get_deduplicator(cache_duration: float = 5.0) -> MessageDeduplicator:
    """Get or create the deduplicator singleton."""
    global _deduplicator_instance
    if _deduplicator_instance is None:
        _deduplicator_instance = MessageDeduplicator(cache_duration)
    return _deduplicator_instance
