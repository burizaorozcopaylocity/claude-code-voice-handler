#!/usr/bin/env python3
"""
Qwen AI Integration - The Cosmic Lyricist.

Like having a legendary songwriter who crafts perfect lyrics for every moment,
Qwen generates contextual, rock-infused voice messages.

Cosmic Eddie speaks through Qwen, bringing the spirit of psychedelic rock
to every announcement!
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import random
from voice_handler.ai.prompts import RockPersonality, get_rock_personality


class QwenContextGenerator:
    """
    Generates contextual messages using qwen-code CLI.

    Falls back to simple messages if qwen-code is unavailable.
    Cosmic Eddie's voice comes through here!
    """

    def __init__(self, config: Optional[dict] = None, logger=None):
        """
        Initialize Qwen context generator.

        Args:
            config: Voice configuration
            logger: Logger instance
        """
        self.config = config or {}
        self.logger = logger
        self.qwen_available = self._check_qwen_available()

        # Get user nickname and personality from config
        self.user_nickname = self.config.get("voice_settings", {}).get("user_nickname", "rockstar")
        self.personality_style = self.config.get("voice_settings", {}).get("personality", "rockstar")

        # Initialize rock personality
        self.rock_personality = get_rock_personality()

        if self.logger:
            self.logger.log_info(
                f"Qwen initialized - Cosmic Eddie ready to rock! "
                f"(qwen_available={self.qwen_available})"
            )

    def _check_qwen_available(self) -> bool:
        """Check if qwen-code is available on the system."""
        try:
            if sys.platform == 'win32':
                result = subprocess.run(
                    ["powershell", "-Command", "Get-Command qwen-code -ErrorAction SilentlyContinue"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ["which", "qwen-code"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            return result.returncode == 0
        except Exception:
            return False

    def _call_qwen(self, prompt: str, max_words: int = 30) -> Optional[str]:
        """
        Call qwen-code with a prompt.

        Args:
            prompt: The prompt to send to qwen
            max_words: Maximum words in response

        Returns:
            Qwen's response or None if failed
        """
        if not self.qwen_available:
            return None

        try:
            # Build the full prompt with rock personality system prompt
            system_context = self.rock_personality.get_system_prompt()
            full_prompt = (
                f"{system_context}\n\n"
                f"Usuario: {self.user_nickname}\n"
                f"Tarea: {prompt}\n\n"
                f"Responde en maximo {max_words} palabras."
            )

            if sys.platform == 'win32':
                # Escape quotes for PowerShell
                escaped_prompt = full_prompt.replace("'", "''")
                result = subprocess.run(
                    ["powershell", "-Command", f"qwen-code '{escaped_prompt}'"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    ["qwen-code", full_prompt],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()
                if self.logger:
                    self.logger.log_debug(f"Qwen response: {response}")
                return response
            return None

        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.log_warning("Qwen-code timeout (>10s) - usando fallback rockero")
            return None
        except Exception as e:
            if self.logger:
                self.logger.log_error("Error calling qwen-code", exception=e)
            return None

    def generate_greeting(self, hour: Optional[int] = None) -> str:
        """
        Generate a contextual greeting.

        Args:
            hour: Current hour (0-23)

        Returns:
            Contextual greeting with rock flair
        """
        if hour is None:
            hour = datetime.now().hour

        time_context = (
            "madrugada" if hour < 6 else
            "manana" if hour < 12 else
            "tarde" if hour < 19 else
            "noche"
        )

        prompt = (
            f"Saluda a {self.user_nickname} de forma rockera. "
            f"Es de {time_context}. Usa referencia musical."
        )

        response = self._call_qwen(prompt, max_words=15)
        if response:
            return response
        # Fallback: usar saludo pre-definido de RockPersonality
        return self.rock_personality.get_greeting(time_context, self.user_nickname)

    def generate_acknowledgment(self, task_description: Optional[str] = None) -> str:
        """
        Generate acknowledgment when user submits a prompt.

        This is where Cosmic Eddie previews the upcoming performance!

        Args:
            task_description: Brief description of what was asked

        Returns:
            Contextual acknowledgment
        """
        prompt = self.rock_personality.get_acknowledgment_prompt(
            task_description,
            self.user_nickname
        )

        response = self._call_qwen(prompt, max_words=30)
        if response:
            return response
        # Fallback: usar frase de acknowledgment pre-definida
        return self.rock_personality.get_acknowledgment(self.user_nickname)

    def generate_tool_announcement(
        self,
        tool_name: str,
        file_path: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate announcement for tool usage.

        Args:
            tool_name: Name of the tool being used
            file_path: File being operated on
            context: Additional context

        Returns:
            Contextual tool announcement
        """
        metaphor = self.rock_personality.get_tool_metaphor(tool_name)

        if file_path:
            filename = Path(file_path).name
            prompt = f"Claude va a {metaphor} el archivo {filename}. Anuncia brevemente."
        else:
            prompt = f"Claude va a {metaphor}. Anuncia brevemente."

        response = self._call_qwen(prompt, max_words=15)
        return response or f"{metaphor.capitalize()}..."

    def generate_completion(
        self,
        summary: Optional[str] = None,
        files_modified: int = 0,
        commands_run: int = 0
    ) -> str:
        """
        Generate completion message when task is done.

        The encore announcement!

        Args:
            summary: Summary of what was done
            files_modified: Number of files modified
            commands_run: Number of commands run

        Returns:
            Contextual completion message
        """
        context_parts = []
        if files_modified > 0:
            context_parts.append(f"modifique {files_modified} archivos")
        if commands_run > 0:
            context_parts.append(f"ejecute {commands_run} comandos")

        if summary:
            context = f"Termine la tarea: {summary[:100]}."
        elif context_parts:
            context = f"Termine. {', '.join(context_parts)}."
        else:
            context = "Termine la tarea."

        prompt = (
            f"{context} Anuncialo a {self.user_nickname} "
            f"con una frase de encore rockero."
        )

        response = self._call_qwen(prompt, max_words=25)
        if response:
            return response
        # Fallback: usar frase de completion pre-definida
        return self.rock_personality.get_completion_phrase()

    def generate_approval_request(
        self,
        tool_name: Optional[str] = None,
        action_description: Optional[str] = None
    ) -> str:
        """
        Generate message when Claude needs user approval.

        Like the roadie asking for permission before a pyrotechnics cue!

        Args:
            tool_name: Tool requiring approval
            action_description: What action needs approval

        Returns:
            Contextual approval request
        """
        if tool_name:
            prompt = (
                f"El roadie necesita permiso de {self.user_nickname} "
                f"para usar {tool_name}. Pidelo de forma breve pero urgente."
            )
        elif action_description:
            prompt = (
                f"Necesito permiso de {self.user_nickname} para: {action_description}. "
                f"Pidelo brevemente."
            )
        else:
            prompt = (
                f"Hey {self.user_nickname}, el roadie necesita tu atencion! "
                f"Hay algo que aprobar."
            )

        response = self._call_qwen(prompt, max_words=20)
        if response:
            return response
        # Fallback: usar frase de approval pre-definida
        return self.rock_personality.get_approval_phrase(self.user_nickname)

    def generate_error_message(
        self,
        error_type: Optional[str] = None,
        error_details: Optional[str] = None
    ) -> str:
        """
        Generate message when an error occurs.

        Like announcing feedback in the PA - something's not quite right!

        Args:
            error_type: Type of error
            error_details: Error details

        Returns:
            Contextual error message
        """
        if error_details:
            prompt = (
                f"Hubo feedback en la senal: {error_details[:50]}. "
                f"Informalo a {self.user_nickname} como roadie tranquilo."
            )
        else:
            prompt = (
                f"Un pequeno problema tecnico. "
                f"Informalo a {self.user_nickname} sin alarma."
            )

        response = self._call_qwen(prompt, max_words=20)
        if response:
            return response
        # Fallback: usar frase de error pre-definida
        return self.rock_personality.get_error_phrase()

    def enrich_message(
        self,
        original_message: str,
        context_type: str = "general"
    ) -> str:
        """
        Enrich an existing message with rock context.

        Args:
            original_message: The original message to enrich
            context_type: Type of context

        Returns:
            Enriched message with rock flair
        """
        if not original_message or len(original_message) < 10:
            return original_message

        prompt = (
            f"Reformula este mensaje para {self.user_nickname} "
            f"con personalidad rockera: '{original_message[:150]}'"
        )

        response = self._call_qwen(prompt, max_words=35)
        return response or original_message


# Singleton instance
_qwen_generator: Optional[QwenContextGenerator] = None


def get_qwen_generator(config: Optional[dict] = None, logger=None) -> QwenContextGenerator:
    """Get or create the Qwen context generator singleton."""
    global _qwen_generator
    if _qwen_generator is None:
        _qwen_generator = QwenContextGenerator(config=config, logger=logger)
    return _qwen_generator
