"""Validation functions."""


def validate_username(username: str) -> bool:
    """Validate username.

    Requisites: Min length = 5."""
    return len(username) >= 5


def validate_name(name: str) -> bool:
    """Validate full name.

    Requisites: Min words = 2."""
    return len(name.split()) >= 2


def validate_pwd(password: str) -> bool:
    """Validate password strenght.

    Requisites: Min length = 8."""
    return len(password) >= 8
