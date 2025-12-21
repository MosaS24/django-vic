import secrets
import string

from .models import Session


ALPHABET = string.ascii_uppercase + string.digits  # A-Z, 0-9


def generate_session_code(length: int = 6) -> str:
    """
    Генерирует уникальный код комнаты (например, AB12CD).
    """
    while True:
        code = "".join(secrets.choice(ALPHABET) for _ in range(length))
        if not Session.objects.filter(code=code).exists():
            return code
