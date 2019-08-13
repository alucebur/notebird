"""User-defined exceptions."""
from typing import Tuple


class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class UsernameExistsError(Error):
    """Exception raised when the given username already exists in the database.

    Attributes:
        username -- conflicting username that produced the error.
        message -- explanation of the error."""

    def __init__(self, username: str, message: str):
        self.username = username
        self.message = message


class DatabaseError(Error):
    """Exception raised by errors related to the database operation.

    Attributes:
        message -- explanation of the error."""

    def __init__(self, message: str):
        self.message = message


class ValidationError(Error):
    """Exception raised by errors in input validations.

    Attributes:
        columns -- columns that failed validation.
        message -- explanation of the error."""

    def __init__(self, columns: Tuple[str, ...], message: str):
        self.columns = columns
        self.message = message


class LoginError(Error):
    """Exception raised when the provided username-password combination
    is not valid.

    Attributes:
        username -- username that produced the error.
        message -- explanation of the error."""

    def __init__(self, username: str, message: str):
        self.username = username
        self.message = message
