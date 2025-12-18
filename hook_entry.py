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

# CRITICAL: Remove current directory to avoid voice_handler.py shadowing the package
hook_dir = str(Path(__file__).parent)
while hook_dir in sys.path:
    sys.path.remove(hook_dir)

# Also remove empty string (current dir) and "."
for bad_path in ["", "."]:
    while bad_path in sys.path:
        sys.path.remove(bad_path)

# Add src directory FIRST for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from voice_handler.cli import main

    if __name__ == "__main__":
        main()
except Exception as e:
    # Log error for debugging
    import traceback
    log_path = Path(__file__).parent / "logs" / "hook_errors.log"
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "a") as f:
        from datetime import datetime
        f.write(f"\n[{datetime.now().isoformat()}] Error:\n")
        traceback.print_exc(file=f)
