"""Functions to manage hashed and salted passwords."""
from passlib.context import CryptContext

# CryptContext
pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)


def encrypt_password(password: str) -> str:
    """Return the password hashed and salted."""
    return pwd_context.hash(password)


def check_encrypted_password(password: str, hashed: str) -> bool:
    """Return True if both passwords match."""
    return pwd_context.verify(password, hashed)
