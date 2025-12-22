#!/usr/bin/env python3
"""
Transcript Reader - The Tour Historian.

Like the chronicler who records every legendary show,
this module extracts Claude's messages from the conversation log.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class TranscriptReader:
    """
    Reads and extracts messages from Claude Code transcript files.

    The archivist who keeps track of every riff and lyric.
    """

    def __init__(self, transcript_path: str, session_id: Optional[str] = None):
        """
        Initialize the transcript reader.

        Args:
            transcript_path: Path to the transcript file
            session_id: Optional session identifier
        """
        self.transcript_path = Path(transcript_path)
        self.session_id = session_id

        # Get state file path from centralized paths module
        from voice_handler.utils.paths import get_paths
        self.state_file = get_paths().state_storage

        self.state = self._load_state()
        self.last_positions = self.state.get('transcript_positions', {})

        # Reset positions for new session
        if session_id and self.state.get('current_session_id') != session_id:
            self.last_positions = {}

    def _load_state(self) -> Dict[str, Any]:
        """Load combined state from temp storage."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            'transcript_positions': {},
            'task_context': {
                "files_created": [],
                "files_modified": [],
                "files_deleted": [],
                "commands_run": [],
                "searches_performed": [],
                "start_time": datetime.now().isoformat(),
                "operations_count": 0
            }
        }

    def _save_last_position(self, position: int):
        """Save the last read position for this transcript."""
        self.last_positions[str(self.transcript_path)] = position
        self.state['transcript_positions'] = self.last_positions
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except IOError:
            pass  # Non-critical failure

    def extract_recent_messages(
        self,
        hook_type: Optional[str] = None,
        since_position: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract recent Claude messages from the transcript.

        Args:
            hook_type: Optional hook type filter
            since_position: Position to start reading from

        Returns:
            List of message dictionaries
        """
        if not self.transcript_path.exists():
            return []

        messages = []
        start_position = since_position if since_position is not None else \
            self.last_positions.get(str(self.transcript_path), 0)
        current_position = start_position

        try:
            with open(self.transcript_path, 'r', encoding='utf-8') as f:
                if start_position > 0:
                    f.seek(start_position)

                lines = f.readlines()

                for line in lines:
                    current_position += len(line.encode('utf-8'))

                    try:
                        entry = json.loads(line.strip())

                        if entry.get('type') == 'assistant' and 'message' in entry:
                            msg = entry['message']
                            if msg.get('role') == 'assistant' and 'content' in msg:
                                content_list = msg['content']

                                for content_item in content_list:
                                    if content_item.get('type') == 'text':
                                        text = content_item.get('text', '').strip()
                                        if text:
                                            messages.append({
                                                'text': text,
                                                'timestamp': entry.get('timestamp'),
                                                'uuid': entry.get('uuid'),
                                                'position': current_position
                                            })
                    except json.JSONDecodeError:
                        continue

        except Exception:
            pass

        if current_position > start_position:
            self._save_last_position(current_position)

        return messages

    def get_last_message(
        self,
        max_length: int = 350,
        min_length: int = 50
    ) -> Optional[str]:
        """
        Get the most recent Claude message with intelligent extraction.

        Args:
            max_length: Maximum character length for the message
            min_length: Minimum character length to consider

        Returns:
            Extracted message or None
        """
        messages = self.extract_recent_messages()

        if not messages:
            return None

        last_msg = messages[-1]['text']
        last_msg = self.clean_message_for_speech(last_msg)

        if not last_msg:
            return None

        if len(last_msg) <= max_length:
            return last_msg

        return self.extract_meaningful_summary(last_msg, max_length, min_length)

    def extract_meaningful_summary(
        self,
        text: str,
        max_length: int = 350,
        min_length: int = 50
    ) -> str:
        """
        Extract a meaningful summary from text.

        Args:
            text: The full text to summarize
            max_length: Maximum character length
            min_length: Minimum character length

        Returns:
            Summarized text
        """
        # Handle numbered or bulleted lists specially
        list_pattern = r'\n\s*(\d+\.|\*|\-)\s+'
        if re.search(list_pattern, text):
            return self._extract_list_summary(text, max_length)

        # Split into sentences
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])\s*\n'
        sentences = re.split(sentence_pattern, text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return text[:max_length - 3] + '...' if len(text) > max_length else text

        summary = ""
        target_length = int(max_length * 0.9)

        for i, sentence in enumerate(sentences):
            if sentence and sentence[-1] not in '.!?':
                sentence += '.'

            potential_summary = summary + (" " if summary else "") + sentence

            if len(potential_summary) <= target_length:
                summary = potential_summary
                if len(summary) >= min_length and len(summary) >= int(target_length * 0.6):
                    if i + 1 < len(sentences):
                        next_sentence = sentences[i + 1]
                        if next_sentence[-1] not in '.!?':
                            next_sentence += '.'
                        next_potential = summary + " " + next_sentence
                        if len(next_potential) <= max_length:
                            summary = next_potential
                    break
            else:
                if not summary:
                    break_points = ['. ', ', ', ' - ', ': ']
                    for bp in break_points:
                        if bp in sentence[:target_length]:
                            pos = sentence[:target_length].rfind(bp)
                            summary = sentence[:pos + 1]
                            break
                    else:
                        summary = sentence[:max_length - 3] + '...'
                break

        return summary if summary else text[:max_length - 3] + '...'

    def _extract_list_summary(self, text: str, max_length: int) -> str:
        """Extract summary from numbered or bulleted lists."""
        intro = ""
        list_start_pattern = r'\n\s*(\d+\.|\*|\-)\s+'
        match = re.search(list_start_pattern, text)

        if match:
            intro = text[:match.start()].strip()
            list_text = text[match.start():]
        else:
            list_text = text

        if '\n' in list_text:
            list_items = re.split(r'\n\s*(?:\d+\.|\*|\-)\s+', list_text)
        else:
            list_items = re.split(r'\s*\d+\.\s+', list_text)

        list_items = [item.strip() for item in list_items if item.strip()]

        if intro:
            summary = intro
            if not summary.endswith(':'):
                summary += ":"
        else:
            summary = ""

        items_text = []
        for item in list_items[:2]:
            item = re.sub(r'^(\d+\.|\*|\-)\s+', '', item)
            item = item.rstrip('.')
            if item:
                items_text.append(item)

        if items_text:
            if len(items_text) == 1:
                summary += f" {items_text[0]}"
            else:
                summary += f" {items_text[0]}, {items_text[1].lower()}"

            remaining = len(list_items) - len(items_text)
            if remaining > 0:
                more_text = f" and {remaining} more"
                if len(summary + more_text) <= max_length:
                    summary += more_text

        if summary and summary[-1] not in '.!?':
            summary += '.'

        return summary if summary else "Completed tasks"

    def clean_message_for_speech(self, text: str) -> Optional[str]:
        """Clean up message for speech synthesis."""
        if '```' in text:
            parts = text.split('```')
            return parts[0].strip()

        if text.strip().startswith('{') and text.strip().endswith('}'):
            return None

        if text.count('/') > 5 or text.count('\\') > 5:
            return None

        text = ' '.join(text.split())
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`(.*?)`', r'\1', text)

        return text.strip()

    def get_messages_since_last_check(self) -> List[str]:
        """Get all messages since the last check."""
        messages = self.extract_recent_messages()
        cleaned_messages = []

        for msg in messages:
            cleaned_text = self.clean_message_for_speech(msg['text'])
            if cleaned_text:
                cleaned_messages.append(cleaned_text)

        return cleaned_messages

    def detect_approval_request(self, text: str) -> bool:
        """
        Detect if a message contains an approval/confirmation request.

        Args:
            text: Message text to check

        Returns:
            True if approval request detected
        """
        if not text:
            return False

        text_lower = text.lower()

        approval_patterns = [
            "would you like", "should i proceed", "shall i continue",
            "do you want", "is this okay", "confirm", "approve",
            "permission to", "may i", "can i proceed", "before i continue",
            "do you approve", "is it okay to", "should i go ahead",
            "ready to proceed", "waiting for your", "need your approval",
            "requires your approval", "please confirm", "yes or no",
            "y/n", "(y/n)", "[y/n]", "proceed with", "continue with",
            "allow me to", "i'll need to", "i need to", "about to",
            "going to make", "will make the following", "before making",
            "requires permission", "awaiting confirmation", "please respond",
            "your response", "let me know if", "if you'd like me to"
        ]

        return any(pattern in text_lower for pattern in approval_patterns)
