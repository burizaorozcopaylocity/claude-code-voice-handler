#!/usr/bin/env python3
"""
Quick CLI to check voice queue status.

Usage:
    python queue_status.py           # Show queue status
    python queue_status.py --clear   # Clear all pending messages
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from voice_handler.queue.broker import get_broker
from voice_handler.utils.logger import VoiceLogger


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Voice Queue Status")
    parser.add_argument("--clear", action="store_true", help="Clear all pending messages")
    args = parser.parse_args()

    logger = VoiceLogger()
    broker = get_broker(logger=logger)

    if args.clear:
        queue_size = broker.size()
        broker.clear()
        print(f"🧹 Cleared {queue_size} pending messages from queue")
    else:
        queue_size = broker.size()
        print("🎵 Voice Queue Status")
        print("=" * 40)
        print(f"Pending messages: {queue_size}")

        if queue_size > 0:
            print(f"\n💡 Tip: Use --clear to clear the queue if needed")
            print(f"   Example: python {Path(__file__).name} --clear")


if __name__ == "__main__":
    main()
