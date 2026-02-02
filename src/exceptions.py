"""Custom exception types for the WeatherApp project.

This module defines exceptions used across the `src` package so callers
can catch specific error conditions (e.g., missing configuration).
"""


class MissingAPIConfigError(RuntimeError):
    """Raised when required API configuration is missing.

    This exception is intended to signal that `URL` and/or `API_KEY`
    were not found in the environment or the project's `.env` file.
    """

    def __init__(self, message: str = "Missing URL or API_KEY in environment or .env"):
        super().__init__(message)
