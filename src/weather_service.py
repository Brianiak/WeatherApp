"""weather_service — fetch weather data using OpenWeatherMap API.

This module reads API configuration from a `.env` file placed at the
project root, constructs the request URL, performs the HTTP GET call,
and pretty-prints the JSON response.

The `.env` file is expected to contain `URL` and `API_KEY` variables.
"""

import os
from pathlib import Path
import requests

# Import project-specific exceptions. Use a relative import where possible
try:
    from .exceptions import (
        MissingAPIConfigError,
        EnvNotFoundError,
        NetworkError,
        ServiceUnavailableError,
        APITokenExpiredError,
        APIRequestError,
    )
except Exception:
    # Fallback to absolute import to support different execution contexts
    from exceptions import (
        MissingAPIConfigError,
        EnvNotFoundError,
        NetworkError,
        ServiceUnavailableError,
        APITokenExpiredError,
        APIRequestError,
    )


def load_dotenv(path=None):
    """Load key=value pairs from a .env file into the process environment.

    If `path` is None, the function looks for a `.env` file in the project
    root (one level above the `src` package). Lines starting with `#` are
    ignored. Values are not interpreted (no quote stripping beyond simple
    split) — they are stored as raw strings.

    Raises:
        EnvNotFoundError: if the .env file does not exist at the expected path.

    Returns a dict of loaded variables.
    """
    if path is None:
        # Find project root (parent of the `src` folder) and look for .env there
        path = Path(__file__).resolve().parents[1] / ".env"
    else:
        path = Path(path)
    if not path.exists():
        raise EnvNotFoundError(f".env file not found at: {path}")
    env = {}
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    # Inject loaded variables into os.environ so other parts of the app can use them
    os.environ.update(env)
    return env

# NOTE: Do not load the .env file at import time. Loading is deferred until
# the service is actually used (via `_get_config()` / `get_weather()`), so
# importing the module does not raise on missing files and leaves the
# `get_weather` symbol available for callers and tests.

def _get_config():
    """Return (URL, API_KEY) from environment or raise MissingAPIConfigError.

    Configuration is validated when the service is actually used (via
    `get_weather()`), which avoids side-effects at import time.
    """
    # Ensure environment variables are loaded from the project's .env file
    # prior to reading them. This will raise EnvNotFoundError if the .env
    # file does not exist, which callers can catch if they wish.
    load_dotenv()
    url = os.getenv("URL")
    api_key = os.getenv("API_KEY")
    if not url or not api_key:
        raise MissingAPIConfigError("Missing URL or API_KEY in environment or .env")
    return url, api_key

# TODO: Insert lat and lon parameters into the URL based on user location as soon as that feature is available.
def build_request_url(url: str, api_key: str) -> str:
    """Return the full request URL by concatenating base URL and API key."""
    return url + api_key

# TODO: Consider creating fallback logic f.ex. caching the last successful response to use when network errors occur.
def fetch_json(request_url: str, timeout: int = 10) -> dict:
    """Perform HTTP GET against `request_url` and return parsed JSON.

    Raises:
        NetworkError: when there are network connectivity problems.
        APITokenExpiredError: when API returns 401 Unauthorized.
        ServiceUnavailableError: when API returns a 5xx status.
        APIRequestError: for other non-successful responses or invalid JSON.
    """
    try:
        res = requests.get(url=request_url, timeout=timeout)
    except (requests.ConnectionError, requests.Timeout) as exc:
        # Connection problems (no internet, DNS failure, timeouts)
        raise NetworkError("Network error contacting weather API") from exc

    # Handle authentication / token errors explicitly
    if res.status_code == 401:
        raise APITokenExpiredError("API token invalid or expired")

    # Service-side errors
    if 500 <= res.status_code < 600:
        raise ServiceUnavailableError(f"Weather service returned {res.status_code}")

    # Any other non-OK response is treated as a generic API request error
    if not res.ok:
        raise APIRequestError(f"API request failed: HTTP {res.status_code}: {res.text}")

    try:
        return res.json()
    except ValueError as exc:
        raise APIRequestError("Invalid JSON response from weather API") from exc

def get_weather() -> dict:
    """High-level API: return weather JSON from configured provider.

    This function reads configuration, builds the request URL, performs
    the HTTP request and returns the parsed JSON. It raises
    `MissingAPIConfigError` when configuration is missing and propagates
    network-related exceptions from `requests`.
    """
    url, api_key = _get_config()
    request_url = build_request_url(url, api_key)
    return fetch_json(request_url)


__all__ = ["get_weather", "build_request_url", "fetch_json"]
