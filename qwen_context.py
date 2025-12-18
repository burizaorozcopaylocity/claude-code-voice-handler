#!/usr/bin/env python3
"""
Qwen-Code integration for generating contextual voice messages.
Uses local Qwen model to create dynamic, context-aware announcements.
"""

import subprocess
import sys
import os


class QwenContextGenerator:
    """
    Generates contextual messages using qwen-code CLI.
    Falls back to simple messages if qwen-code is unavailable.
    """

    def __init__(self, config=None, logger=None):
        """
        Initialize Qwen context generator.

        Args:
            config (dict): Voice configuration
            logger: Logger instance
        """
        self.config = config or {}
        self.logger = logger
        self.qwen_available = self._check_qwen_available()

        # Get user nickname and personality from config
        self.user_nickname = self.config.get("voice_settings", {}).get("user_nickname", "friend")
        self.personality = self.config.get("voice_settings", {}).get("personality", "rockstar")

    def _check_qwen_available(self):
        """Check if qwen-code is available on the system."""
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-Command qwen-code -ErrorAction SilentlyContinue"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _call_qwen(self, prompt, max_words=30):
        """
        Call qwen-code with a prompt.

        Args:
            prompt (str): The prompt to send to qwen
            max_words (int): Maximum words in response

        Returns:
            str: Qwen's response or None if failed
        """
        if not self.qwen_available:
            return None

        try:
            # Build the full prompt with constraints
            full_prompt = f"{prompt} Responde en maximo {max_words} palabras, en espanol, tono {self.personality}."

            result = subprocess.run(
                ["powershell", "-Command", f"qwen-code '{full_prompt}'"],
                capture_output=True,
                text=True,
                timeout=15  # 15 second timeout
            )

            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()
                if self.logger:
                    self.logger.log_debug(f"Qwen response: {response}")
                return response
            return None

        except subprocess.TimeoutExpired:
            if self.logger:
                self.logger.log_warning("Qwen-code timed out")
            return None
        except Exception as e:
            if self.logger:
                self.logger.log_error("Error calling qwen-code", exception=e)
            return None

    def generate_greeting(self, hour=None):
        """
        Generate a contextual greeting.

        Args:
            hour (int): Current hour (0-23)

        Returns:
            str: Contextual greeting
        """
        from datetime import datetime
        if hour is None:
            hour = datetime.now().hour

        time_context = "madrugada" if hour < 6 else "manana" if hour < 12 else "tarde" if hour < 19 else "noche"

        prompt = f"Saluda a {self.user_nickname} de forma breve y rockera, es de {time_context}."

        response = self._call_qwen(prompt, max_words=15)
        return response or f"Hey {self.user_nickname}, let's rock!"

    def generate_acknowledgment(self, task_description=None):
        """
        Generate acknowledgment when user submits a prompt.

        Args:
            task_description (str): Brief description of what was asked

        Returns:
            str: Contextual acknowledgment
        """
        if task_description:
            # Truncate but keep meaningful part of task
            task_short = task_description[:150].strip()
            prompt = f"{self.user_nickname} me pidio: '{task_short}'. Responde confirmando la tarea especifica de forma rockera, menciona que vas a hacer."
        else:
            prompt = f"{self.user_nickname} me dio una tarea. Confirma de forma breve y rockera."

        response = self._call_qwen(prompt, max_words=25)
        return response or f"On it, {self.user_nickname}!"

    def generate_tool_announcement(self, tool_name, file_path=None, context=None):
        """
        Generate announcement for tool usage.

        Args:
            tool_name (str): Name of the tool being used
            file_path (str): File being operated on
            context (str): Additional context

        Returns:
            str: Contextual tool announcement
        """
        tool_actions = {
            "Read": "leyendo",
            "Edit": "editando",
            "Write": "escribiendo",
            "Grep": "buscando en el codigo",
            "Glob": "buscando archivos",
            "Bash": "ejecutando comando",
            "Task": "iniciando subtarea"
        }

        action = tool_actions.get(tool_name, f"usando {tool_name}")

        if file_path:
            from pathlib import Path
            filename = Path(file_path).name
            prompt = f"Estoy {action} el archivo {filename}. Anuncia esto de forma breve y rockera."
        else:
            prompt = f"Estoy {action}. Anuncia de forma breve."

        response = self._call_qwen(prompt, max_words=15)
        return response or f"{action.capitalize()}..."

    def generate_completion(self, summary=None, files_modified=0, commands_run=0):
        """
        Generate completion message when task is done.

        Args:
            summary (str): Summary of what was done
            files_modified (int): Number of files modified
            commands_run (int): Number of commands run

        Returns:
            str: Contextual completion message
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

        prompt = f"{context} Anuncialo a {self.user_nickname} de forma rockera y satisfecha."

        response = self._call_qwen(prompt, max_words=25)
        return response or f"Done, {self.user_nickname}! Another brick in the wall."

    def generate_approval_request(self, tool_name=None, action_description=None):
        """
        Generate message when Claude needs user approval.

        Args:
            tool_name (str): Tool requiring approval
            action_description (str): What action needs approval

        Returns:
            str: Contextual approval request
        """
        if tool_name:
            prompt = f"Necesito permiso de {self.user_nickname} para usar {tool_name}. Pidelo de forma breve pero clara."
        elif action_description:
            prompt = f"Necesito permiso de {self.user_nickname} para: {action_description}. Pidelo brevemente."
        else:
            prompt = f"Necesito la atencion de {self.user_nickname}, hay algo que aprobar. Pidelo de forma breve."

        response = self._call_qwen(prompt, max_words=20)
        return response or f"Hey {self.user_nickname}, I need your approval here!"

    def generate_error_message(self, error_type=None, error_details=None):
        """
        Generate message when an error occurs.

        Args:
            error_type (str): Type of error
            error_details (str): Error details

        Returns:
            str: Contextual error message
        """
        if error_details:
            prompt = f"Hubo un problema: {error_details[:50]}. Informalo a {self.user_nickname} de forma breve pero no alarmante."
        else:
            prompt = f"Hubo un pequeño problema. Informalo a {self.user_nickname} de forma tranquila."

        response = self._call_qwen(prompt, max_words=20)
        return response or f"Hit a snag, {self.user_nickname}. Let me check this out."

    def enrich_message(self, original_message, context_type="general"):
        """
        Enrich an existing message with more context.

        Args:
            original_message (str): The original message to enrich
            context_type (str): Type of context (greeting, completion, error, etc.)

        Returns:
            str: Enriched message
        """
        if not original_message or len(original_message) < 10:
            return original_message

        prompt = f"Reformula este mensaje para {self.user_nickname} de forma mas natural y rockera: '{original_message[:150]}'"

        response = self._call_qwen(prompt, max_words=35)
        return response or original_message


# Singleton instance for easy access
_qwen_generator = None

def get_qwen_generator(config=None, logger=None):
    """Get or create the Qwen context generator singleton."""
    global _qwen_generator
    if _qwen_generator is None:
        _qwen_generator = QwenContextGenerator(config=config, logger=logger)
    return _qwen_generator
