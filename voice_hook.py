#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#   "openai>=1.0.0",
#   "sounddevice>=0.4.6",
#   "soundfile>=0.12.1",
#   "numpy>=1.24.0",
#   "persist-queue>=0.8.0",
# ]
# ///
"""
Voice Handler Wrapper - The Stage Manager's Quick Entrance.

This wrapper delegates to the new modular package structure
while maintaining backward compatibility with existing hooks.

🎸 Rock on with async TTS! 🎸
"""
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from voice_handler.cli import main

    if __name__ == "__main__":
        main()
except Exception:
    # Silent failure for hooks - don't block Claude operations
    pass
