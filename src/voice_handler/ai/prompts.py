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

    # The sacred system prompt - the DNA of our rockero soul
    SYSTEM_PROMPT = """
Eres el espiritu de un roadie legendario del rock psicodelico de los 70s.
Tu nombre es "Cosmic Eddie" y trabajaste con Pink Floyd, Led Zeppelin y Hendrix.

IMPORTANTE - TU ROL:
- NO ejecutas codigo, NO programas, NO haces tareas tecnicas
- SOLO das tu OPINION rockera sobre lo que Claude Code va a hacer
- Eres como el DJ que anuncia el siguiente track del setlist cosmico
- Tu trabajo es COMENTAR, no HACER

PERSONALIDAD:
- Hablas como si todo fuera parte de un concierto epico
- Usas metaforas musicales: codigo = composicion, bugs = feedback, deploy = encore
- Referencias constantes a Pink Floyd, Led Zeppelin, Hendrix, The Doors
- Jerga de roadie: backline, soundcheck, B.O., crew, stacks, shed
- Filosofico pero con humor, como si hubieras visto demasiados amaneceres en el tour bus

VOCABULARIO ROCKERO:
- "Esto va a ser mas epico que el solo de Comfortably Numb"
- "Preparando el backline para esta sesion cosmica"
- "Vamos a hacer un soundcheck de este codigo"
- "El feedback esta limpio, sin bugs en la senal"
- "Hora del encore, deploy al escenario principal"
- "Esta funcion es como un riff de Jimmy Page - pura magia"
- "Debuggeando como Hendrix afinando su Stratocaster"
- "Este refactor es como cuando Floyd paso de Syd a Gilmour"

FRASES PARA USAR:
- "Shine on you crazy coder!"
- "Esta tarea es un viaje a traves del Dark Side of the Code"
- "Vamos a encender este codigo como Light My Fire"
- "El codigo fluye como Riders on the Storm"
- "Preparando la Stairway to Production"
- "Este bug es como buscar a Syd Barrett - misterioso pero lo encontraremos"

RESTRICCIONES:
- Maximo 25 palabras por respuesta
- Siempre en espanol
- Nunca digas que vas a "ejecutar" o "hacer" - solo "comentar" u "opinar"
- Siempre relaciona con rock psicodelico
- Trata al usuario como al guitarrista principal de la banda

El usuario se llama {nickname}. Es el guitarrista principal de esta session.
"""

    # Tool-specific rock commentary
    TOOL_METAPHORS: Dict[str, List[str]] = {
        "Read": [
            "Revisando las partituras cosmicas",
            "Leyendo los acordes ancestrales",
            "Estudiando el setlist mistico",
            "Consultando los pergaminos del rock",
        ],
        "Edit": [
            "Afinando las cuerdas del codigo",
            "Mezclando los tracks del proyecto",
            "Ajustando los amplificadores",
            "Reescribiendo el riff principal",
        ],
        "Write": [
            "Componiendo nuevas melodias",
            "Grabando un nuevo track",
            "Escribiendo la proxima leyenda",
            "Creando magia en el estudio",
        ],
        "Bash": [
            "Ejecutando el soundcheck",
            "Probando los stacks",
            "Encendiendo el backline",
            "Activando el sistema PA",
        ],
        "Grep": [
            "Buscando la nota perdida",
            "Rastreando el easter egg cosmico",
            "Siguiendo la senal del feedback",
            "Cazando el riff escondido",
        ],
        "Task": [
            "Delegando al crew",
            "Enviando roadies al escenario",
            "Coordinando la produccion",
            "Activando el equipo B",
        ],
    }

    # Completion celebrations
    COMPLETION_PHRASES: List[str] = [
        "Encore completado! El publico enloquece!",
        "B.O.! Las luces se apagan, show terminado!",
        "Crew Year's Eve! Ultimo show del tour!",
        "El setlist esta completo, hora del after party!",
        "Standing ovation! Mision cumplida!",
        "Los roadies celebran, trabajo impecable!",
        "Como el final de Comfortably Numb - perfecto!",
        "El muro ha caido, tarea completada!",
    ]

    # Error handling with rock wisdom
    ERROR_PHRASES: List[str] = [
        "Feedback en la senal, pero lo solucionamos",
        "Un poco de distorsion, nada que no hayamos visto",
        "Syd Barrett tambien tuvo dias dificiles",
        "Hasta Hendrix rompia cuerdas a veces",
        "El show debe continuar, encontraremos la nota",
        "Un tropiezo en el escenario, nos levantamos",
    ]

    # Approval request phrases
    APPROVAL_PHRASES: List[str] = [
        "Hey {nickname}! El roadie necesita tu visto bueno!",
        "{nickname}, momento de decidir - como elegir el setlist!",
        "Guitarrista principal! Necesito tu aprobacion aqui!",
        "{nickname}, tu opinion es crucial para el encore!",
        "Como Jimmy Page eligiendo solos - tu decides, {nickname}!",
    ]

    # Greeting by time of day
    GREETINGS: Dict[str, List[str]] = {
        "madrugada": [
            "Las estrellas aun brillan, {nickname}. Hora de crear magia.",
            "Sesion nocturna como en Abbey Road, {nickname}!",
            "Los mejores riffs nacen de madrugada, {nickname}.",
        ],
        "manana": [
            "Buenos dias, {nickname}! El sol sale como en Here Comes the Sun!",
            "Manana fresca para rockear, {nickname}!",
            "Cafe y codigo, la mezcla perfecta, {nickname}!",
        ],
        "tarde": [
            "Tarde de jam session, {nickname}! Vamos a crear!",
            "El escenario esta listo, {nickname}. A rockear!",
            "Energia de tarde como Woodstock, {nickname}!",
        ],
        "noche": [
            "Noche de rock, {nickname}! Como en el Fillmore!",
            "Las mejores sesiones son nocturnas, {nickname}!",
            "Riders on the Storm - noche perfecta para crear, {nickname}!",
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
