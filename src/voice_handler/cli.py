#!/usr/bin/env python3
"""
CLI Entry Point - The Box Office.

Like the box office that handles all ticket requests,
this module processes command line arguments and routes
voice handler requests to the right place.
"""

import argparse
import sys
import json
from typing import Optional, Tuple, Dict, Any

from voice_handler.utils.logger import get_logger
from voice_handler.core.handler import get_handler


def read_stdin_data() -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Read and parse stdin data from Claude Code.

    Returns:
        Tuple of (parsed JSON dict or None, raw text or None)
    """
    logger = get_logger()
    stdin_data = None
    stdin_text = None

    if not sys.stdin.isatty():
        try:
            stdin_input = sys.stdin.read()
            if stdin_input:
                logger.log_debug(
                    f"Raw stdin received",
                    length=len(stdin_input),
                    first_chars=stdin_input[:200]
                )
                try:
                    stdin_data = json.loads(stdin_input)
                    logger.log_stdin_data(stdin_data)
                except json.JSONDecodeError:
                    stdin_text = stdin_input.strip()
                    logger.log_stdin_data(stdin_text)
        except Exception as e:
            logger.log_error("Error reading stdin", exception=e)
    else:
        logger.log_debug("No stdin data (terminal mode)")

    return stdin_data, stdin_text


def main():
    """
    Main entry point for voice handler CLI.

    The main stage door - all requests come through here!
    """
    parser = argparse.ArgumentParser(
        description="Claude Code Voice Handler - Natural TTS for hook events 🎸",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  voice-handler --hook UserPromptSubmit
  voice-handler --hook PreToolUse --tool Read
  voice-handler --hook Stop
  voice-handler --message "Testing, one two three!"

Hooks:
  UserPromptSubmit  - When user submits a prompt
  PreToolUse        - Before a tool is executed
  PostToolUse       - After a tool completes
  Stop              - When Claude stops processing
  Notification      - Permission/notification events
        """
    )

    parser.add_argument(
        "--voice",
        help="Voice to use (overrides session voice)"
    )
    parser.add_argument(
        "--message",
        help="Message to speak (overrides automatic generation)"
    )
    parser.add_argument(
        "--hook",
        help="Hook type (UserPromptSubmit, PreToolUse, PostToolUse, Stop, Notification)"
    )
    parser.add_argument(
        "--tool",
        help="Tool name (for PreToolUse hooks)"
    )
    parser.add_argument(
        "--file",
        help="File path (for file operations)"
    )
    parser.add_argument(
        "--command",
        help="Command being run (for Bash tool)"
    )
    parser.add_argument(
        "--query",
        help="Search query (for search operations)"
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Use synchronous mode (no background daemon)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )

    args = parser.parse_args()

    # Initialize logger and handler
    logger = get_logger()

    logger.log_info(
        "Voice handler invoked - The show begins!",
        hook=args.hook,
        tool=args.tool,
        file=args.file,
        command=args.command,
        query=args.query,
        has_message=bool(args.message)
    )

    # Initialize handler - use sync mode by default for reliability
    # Async mode with daemon can be enabled with --async flag later
    handler = get_handler(use_async=False)

    # Read stdin data
    stdin_data, stdin_text = read_stdin_data()

    # Log the hook event
    logger.log_hook_event(
        args.hook,
        tool=args.tool,
        stdin_data=stdin_data or stdin_text,
        file=args.file,
        command=args.command,
        query=args.query
    )

    # Determine tool name and session ID
    tool_name = args.tool
    if stdin_data and isinstance(stdin_data, dict):
        tool_name = stdin_data.get('tool_name') or tool_name
        session_id = stdin_data.get('session_id')
        if session_id:
            handler.current_session_id = session_id
            logger.log_debug(f"Session ID captured: {session_id[:8]}...")

    # Check if this hook should trigger voice announcements
    if not handler.should_announce(args.hook, tool_name):
        logger.log_info(f"Hook {args.hook} logged only (no voice announcement)")
        sys.exit(0)

    # Update context for voice-enabled hooks
    if args.hook:
        handler.state_manager.update_context(
            args.hook,
            tool_name=tool_name,
            file_path=args.file,
            command=args.command,
            query=args.query
        )

    # Process hook-specific logic
    message = None

    if args.hook == "UserPromptSubmit":
        message = handler.process_user_prompt_submit(stdin_data)

    elif args.hook == "PreToolUse":
        message = handler.process_pre_tool_use(stdin_data, tool_name)
        if not message:
            sys.exit(0)

    elif args.hook == "PostToolUse":
        message = handler.process_post_tool_use(stdin_data)
        if not message:
            sys.exit(0)

    elif args.hook == "Stop":
        message = handler.process_stop(stdin_data)

    elif args.hook == "Notification":
        message = handler.process_notification(stdin_data)

    # Fall back to command line argument
    if not message and args.message:
        message = args.message

    # Default messages for specific hooks
    if not message:
        if args.hook == "Stop":
            message = "Listo"
        elif args.hook in ["PostToolUse", "PreToolUse"]:
            sys.exit(0)

    # Speak the message if we have one
    if message:
        logger.log_message_flow("Speaking", message)
        handler.speak(message, voice=args.voice)


if __name__ == "__main__":
    main()
