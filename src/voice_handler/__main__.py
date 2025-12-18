#!/usr/bin/env python3
"""
Voice Handler Package Entry Point.

This allows running the voice handler as a module:
    python -m voice_handler --hook UserPromptSubmit

Like the backstage door that leads directly to the main stage!
"""

from voice_handler.cli import main

if __name__ == "__main__":
    main()
