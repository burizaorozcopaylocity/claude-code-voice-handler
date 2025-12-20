#!/usr/bin/env python3
"""
Rock Personality Prompts - The Spirit of Psychedelic Rock

This module contains the soul of our voice handler - a legendary roadie
from the golden age of psychedelic rock who comments on code like
announcing the next epic number in a cosmic setlist.

References:
- Pink Floyd: The Wall, Dark Side of the Moon, Wish You Were Here
- Led Zeppelin: Stairway to Heaven, Kashmir, Whole Lotta Love
- Jimi Hendrix: Purple Haze, Voodoo Child, All Along the Watchtower
- The Doors: Light My Fire, Riders on the Storm, The End
- Cream: Sunshine of Your Love, White Room, Crossroads
"""

from typing import Dict, List, Optional, ClassVar
import random


class RockPersonality:
    """
    The legendary roadie personality that brings psychedelic wisdom
    to code commentary. Like the spirit guide of a cosmic jam session.
    """

    # The system prompt - Professional technical assistant
    SYSTEM_PROMPT = """
Eres un asistente técnico profesional altamente capacitado.
Tu nombre es "Tech Advisor" y proporcionas resúmenes concisos de operaciones de desarrollo.

IMPORTANTE - TU ROL:
- NO ejecutas código, NO programas, NO realizas tareas técnicas
- SOLO informas sobre lo que Claude Code va a realizar
- Eres un observador técnico que proporciona contexto claro y profesional
- Tu trabajo es NOTIFICAR, no EJECUTAR

PERSONALIDAD:
- Tono profesional, corporativo y técnico
- Lenguaje preciso y directo
- Sin jerga innecesaria o metáforas elaboradas
- Enfoque en eficiencia y claridad

TERMINOLOGÍA PROFESIONAL:
- "Entendido" en vez de expresiones coloquiales
- "Procesando" para indicar operaciones en curso
- "Completado" o "Finalizado" para tareas terminadas
- "Requiere aprobación" para permisos necesarios
- "En ejecución" para operaciones activas
- Usa términos técnicos estándar: refactorización, deployment, debugging, testing

RESTRICCIONES:
- Máximo 20 palabras técnicas por respuesta
- Tono serio y profesional
- Nunca digas que vas a "ejecutar" - usa "Claude ejecutará" o "Se procederá a"
- Evita expresiones casuales o emocionales
- Mantén un registro formal y corporativo

El usuario es {nickname}. Dirígete a él de forma profesional.
"""

    # Tool-specific professional terminology
    TOOL_METAPHORS: Dict[str, List[str]] = {
        "Read": [
            "Revisando archivo",
            "Leyendo contenido",
            "Consultando documento",
            "Analizando código",
        ],
        "Edit": [
            "Modificando código",
            "Actualizando archivo",
            "Refactorizando componente",
            "Ajustando configuración",
        ],
        "Write": [
            "Creando archivo",
            "Generando código",
            "Escribiendo documento",
            "Implementando funcionalidad",
        ],
        "Bash": [
            "Ejecutando comando",
            "Procesando operación",
            "Iniciando ejecución",
            "Corriendo script",
        ],
        "Grep": [
            "Buscando patrón",
            "Localizando referencia",
            "Rastreando ocurrencia",
            "Identificando coincidencia",
        ],
        "Task": [
            "Delegando tarea",
            "Asignando proceso",
            "Coordinando operación",
            "Distribuyendo trabajo",
        ],
    }

    # Completion messages
    COMPLETION_PHRASES: List[str] = [
        "Tarea completada exitosamente.",
        "Operación finalizada.",
        "Proceso ejecutado correctamente.",
        "Implementación completada.",
        "Ejecución finalizada sin errores.",
        "Tarea procesada satisfactoriamente.",
        "Operación concluida.",
        "Proceso terminado correctamente.",
    ]

    # Error handling messages
    ERROR_PHRASES: List[str] = [
        "Error detectado. Procesando solución.",
        "Inconveniente identificado. Ajustando.",
        "Problema encontrado. Corrigiendo.",
        "Error capturado. Implementando fix.",
        "Fallo detectado. Aplicando corrección.",
        "Excepción manejada. Continuando operación.",
    ]

    # Approval request phrases
    APPROVAL_PHRASES: List[str] = [
        "Requiere aprobación de {nickname}.",
        "{nickname}, se necesita autorización.",
        "Solicitud de aprobación pendiente, {nickname}.",
        "{nickname}, confirmación requerida.",
        "Esperando validación de {nickname}.",
    ]

    # Acknowledgment phrases (when user submits a task)
    ACKNOWLEDGMENT_PHRASES: List[str] = [
        "Entendido, {nickname}. Procesando solicitud.",
        "Confirmado, {nickname}. Iniciando operación.",
        "Recibido, {nickname}. Claude procederá.",
        "Registrado, {nickname}. En ejecución.",
        "Aceptado, {nickname}. Tarea en proceso.",
        "Comprendido, {nickname}. Comenzando.",
    ]

    # Greeting by time of day
    GREETINGS: Dict[str, List[str]] = {
        "madrugada": [
            "Sesión activa, {nickname}. Sistema operativo.",
            "Entorno de desarrollo listo, {nickname}.",
            "Plataforma iniciada, {nickname}.",
        ],
        "manana": [
            "Buenos días, {nickname}. Sistema disponible.",
            "Entorno activo, {nickname}. Listo para desarrollo.",
            "Sesión matinal iniciada, {nickname}.",
        ],
        "tarde": [
            "Buenas tardes, {nickname}. Ambiente preparado.",
            "Sistema operativo, {nickname}. Procesando solicitudes.",
            "Entorno configurado, {nickname}.",
        ],
        "noche": [
            "Buenas noches, {nickname}. Plataforma activa.",
            "Sesión nocturna lista, {nickname}.",
            "Sistema disponible, {nickname}. En operación.",
        ],
    }

    @classmethod
    def get_system_prompt(cls, nickname: str = "rockstar") -> str:
        """Get the system prompt with the user's nickname."""
        return cls.SYSTEM_PROMPT.format(nickname=nickname)

    @classmethod
    def get_tool_metaphor(cls, tool_name: str) -> str:
        """Get a random rock metaphor for a tool action."""
        metaphors = cls.TOOL_METAPHORS.get(tool_name, ["Preparando el backline"])
        return random.choice(metaphors)

    @classmethod
    def get_completion_phrase(cls) -> str:
        """Get a random completion celebration."""
        return random.choice(cls.COMPLETION_PHRASES)

    @classmethod
    def get_error_phrase(cls) -> str:
        """Get a random error handling phrase."""
        return random.choice(cls.ERROR_PHRASES)

    @classmethod
    def get_approval_phrase(cls, nickname: str = "rockstar") -> str:
        """Get a random approval request phrase."""
        phrase = random.choice(cls.APPROVAL_PHRASES)
        return phrase.format(nickname=nickname)

    @classmethod
    def get_greeting(cls, time_of_day: str, nickname: str = "rockstar") -> str:
        """Get a time-appropriate greeting."""
        greetings = cls.GREETINGS.get(time_of_day, cls.GREETINGS["tarde"])
        greeting = random.choice(greetings)
        return greeting.format(nickname=nickname)

    @classmethod
    def get_acknowledgment(cls, nickname: str = "rockstar") -> str:
        """Get a random acknowledgment phrase."""
        phrase = random.choice(cls.ACKNOWLEDGMENT_PHRASES)
        return phrase.format(nickname=nickname)

    @classmethod
    def get_acknowledgment_prompt(cls, task: str, nickname: str = "rockstar") -> str:
        """
        Generate a prompt for Qwen to acknowledge a task.

        IMPORTANT: This prompt makes it clear that Qwen should only
        COMMENT on what Claude will do, not execute anything.
        """
        return f"""
{nickname} le pidio a Claude Code: "{task[:150]}"

Tu trabajo es SOLO dar una opinion rockera de 15-20 palabras sobre esta tarea.
NO ejecutes nada, solo COMENTA como un roadie anunciando el siguiente track.
Usa referencias al rock psicodelico de los 70s.
Menciona lo que Claude VA A HACER (no lo que TU haras).

Ejemplo: "Shine on! Claude va a refactorizar ese modulo como Gilmour afinando para Comfortably Numb!"
"""


# Iconic album references for special occasions
ALBUM_REFERENCES = {
    "dark_side": {
        "name": "The Dark Side of the Moon",
        "band": "Pink Floyd",
        "use_for": "complex debugging, deep analysis",
        "quote": "There is no dark side of the moon really. Matter of fact it's all dark.",
    },
    "the_wall": {
        "name": "The Wall",
        "band": "Pink Floyd",
        "use_for": "breaking down barriers, refactoring",
        "quote": "All in all you're just another brick in the wall.",
    },
    "led_zeppelin_iv": {
        "name": "Led Zeppelin IV",
        "band": "Led Zeppelin",
        "use_for": "building something epic, new features",
        "quote": "And she's buying a stairway to heaven.",
    },
    "electric_ladyland": {
        "name": "Electric Ladyland",
        "band": "Jimi Hendrix",
        "use_for": "creative solutions, innovative code",
        "quote": "Excuse me while I kiss the sky.",
    },
    "la_woman": {
        "name": "L.A. Woman",
        "band": "The Doors",
        "use_for": "long sessions, persistence",
        "quote": "Riders on the storm.",
    },
}


def get_album_reference(context: str) -> Optional[Dict]:
    """Get a relevant album reference based on context."""
    context_lower = context.lower()

    if any(word in context_lower for word in ["debug", "error", "fix", "bug"]):
        return ALBUM_REFERENCES["dark_side"]
    elif any(word in context_lower for word in ["refactor", "restructure", "clean"]):
        return ALBUM_REFERENCES["the_wall"]
    elif any(word in context_lower for word in ["new", "create", "feature", "build"]):
        return ALBUM_REFERENCES["led_zeppelin_iv"]
    elif any(word in context_lower for word in ["creative", "solution", "innovative"]):
        return ALBUM_REFERENCES["electric_ladyland"]
    elif any(word in context_lower for word in ["long", "session", "marathon"]):
        return ALBUM_REFERENCES["la_woman"]

    return None


# Singleton pattern for rock personality
_rock_personality: Optional[RockPersonality] = None


def get_rock_personality() -> RockPersonality:
    """Get the singleton RockPersonality instance."""
    global _rock_personality
    if _rock_personality is None:
        _rock_personality = RockPersonality()
    return _rock_personality

