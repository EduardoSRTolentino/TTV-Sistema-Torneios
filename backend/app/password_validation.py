"""Regras de senha alinhadas ao cadastro (register e POST /users)."""

import re

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128


def validate_password_strength(password: str) -> None:
    """Levanta ValueError com mensagem em português se a senha for inválida."""
    checks: list[tuple[bool, str]] = [
        (len(password) < PASSWORD_MIN_LENGTH, f"A senha deve ter pelo menos {PASSWORD_MIN_LENGTH} caracteres"),
        (len(password) > PASSWORD_MAX_LENGTH, f"A senha deve ter no máximo {PASSWORD_MAX_LENGTH} caracteres"),
        (not re.search(r"[A-Z]", password), "A senha deve conter pelo menos uma letra maiúscula"),
        (not re.search(r"[a-z]", password), "A senha deve conter pelo menos uma letra minúscula"),
        (not re.search(r"\d", password), "A senha deve conter pelo menos um número"),
        (not re.search(r"[^A-Za-z0-9]", password), "A senha deve conter pelo menos um caractere especial"),
    ]

    for failed, message in checks:
        match failed:
            case True:
                raise ValueError(message)
            case False:
                continue
