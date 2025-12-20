"""
Text utilities for voice handler.

Provides functions for message truncation and text processing.
"""

from typing import Optional


def truncate_message(
    message: str,
    max_words: Optional[int] = None,
    max_chars: Optional[int] = None,
    suffix: str = "..."
) -> str:
    """
    Trunca mensaje inteligentemente sin cortar mid-palabra.

    Aplica truncamiento por palabras primero, luego por caracteres.
    Busca el último espacio antes del límite para no cortar palabras.

    Args:
        message: Mensaje original a truncar
        max_words: Límite máximo de palabras (None = sin límite)
        max_chars: Límite máximo de caracteres (None = sin límite)
        suffix: Sufijo a agregar cuando se trunca (default: "...")

    Returns:
        Mensaje truncado con sufijo si fue necesario truncar

    Examples:
        >>> truncate_message("Hola mundo esto es un test", max_words=3)
        'Hola mundo esto...'

        >>> truncate_message("A" * 400, max_chars=300)
        'AAA...AAA...'  # Truncado a ~300 chars
    """
    if not message:
        return message

    original_message = message
    truncated = False

    # 1. Truncar por palabras primero (si se especificó)
    if max_words is not None and max_words > 0:
        words = message.split()
        if len(words) > max_words:
            message = ' '.join(words[:max_words])
            truncated = True

    # 2. Luego truncar por caracteres (si se especificó)
    if max_chars is not None and max_chars > 0:
        if len(message) > max_chars:
            # Buscar último espacio antes del límite para no cortar palabras
            truncate_pos = message[:max_chars].rfind(' ')

            if truncate_pos > 0:
                # Encontramos un espacio, truncar ahí
                message = message[:truncate_pos]
            else:
                # No hay espacios (palabra muy larga), truncar hard
                message = message[:max_chars]

            truncated = True

    # Agregar sufijo solo si se truncó
    if truncated:
        message = message.rstrip() + suffix

    return message


def count_words(text: str) -> int:
    """
    Cuenta palabras en un texto.

    Args:
        text: Texto a analizar

    Returns:
        Número de palabras
    """
    return len(text.split())


def should_truncate(text: str, max_words: int, max_chars: int) -> bool:
    """
    Determina si un texto necesita ser truncado.

    Args:
        text: Texto a verificar
        max_words: Límite de palabras
        max_chars: Límite de caracteres

    Returns:
        True si el texto excede algún límite
    """
    if max_words and count_words(text) > max_words:
        return True

    if max_chars and len(text) > max_chars:
        return True

    return False
