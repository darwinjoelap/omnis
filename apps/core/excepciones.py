"""Excepciones de dominio: el usuario ve el mensaje, nunca un traceback."""


class ErrorDeNegocio(Exception):
    """Regla de negocio incumplida. El texto se muestra tal cual al usuario."""
