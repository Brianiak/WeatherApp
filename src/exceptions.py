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


class EnvNotFoundError(FileNotFoundError):
    """Raised when the project's .env file cannot be found.

    This distinct exception makes it possible to differentiate between a
    missing configuration file and other configuration errors (like a
    missing key inside a present .env).
    """

    def __init__(self, message: str = ".env file not found in project root"):
        super().__init__(message)


class NetworkError(ConnectionError):
    """Raised when a network-level error prevents contacting the API.

    Examples include lack of internet connectivity or DNS resolution
    failures. This inherits from `ConnectionError` for compatibility.
    """

    def __init__(self, message: str = "Network error when contacting API"):
        super().__init__(message)


class ServiceUnavailableError(RuntimeError):
    """Raised when the remote weather service returns a 5xx error."""

    def __init__(self, message: str = "Weather service is unavailable (5xx)"):
        super().__init__(message)


class APITokenExpiredError(RuntimeError):
    """Raised when the API responds with an authentication error (e.g. 401)."""

    def __init__(self, message: str = "API token invalid or expired"):
        super().__init__(message)


class APIRequestError(RuntimeError):
    """Generic error for failed API requests not covered by other exceptions."""

    def __init__(self, message: str = "API request failed"):
        super().__init__(message)
