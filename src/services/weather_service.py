"""weather_service — fetch weather data using OpenWeatherMap API.

This module reads API configuration from a `.env` file placed at the
project root, constructs the request URL, performs the HTTP GET call,
and pretty-prints the JSON response.

The `.env` file is expected to contain `URL` and `API_KEY` variables.
"""

import os
from pathlib import Path
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Import project-specific exceptions. Try relative import first (when the
# package is imported as a package), then absolute import, and as a final
# fallback load the module from the file system. This makes imports robust
# when running tests or executing modules directly.
try:
    # Prefer package-relative import (works when `src` is a package)
    from ..utils.exceptions import (
        MissingAPIConfigError,
        EnvNotFoundError,
        NetworkError,
        ServiceUnavailableError,
        APITokenExpiredError,
        APIRequestError,
    )
except Exception:
    try:
        # Try absolute import if the package root is on sys.path
        from utils.exceptions import (
            MissingAPIConfigError,
            EnvNotFoundError,
            NetworkError,
            ServiceUnavailableError,
            APITokenExpiredError,
            APIRequestError,
        )
    except Exception:
        # Last-resort: load exceptions.py directly from the src/utils folder
        import importlib.util

        exceptions_path = Path(__file__).resolve().parents[1] / "utils" / "exceptions.py"
        spec = importlib.util.spec_from_file_location("weather_exceptions", str(exceptions_path))
        exceptions_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(exceptions_mod)

        MissingAPIConfigError = exceptions_mod.MissingAPIConfigError
        EnvNotFoundError = exceptions_mod.EnvNotFoundError
        NetworkError = exceptions_mod.NetworkError
        ServiceUnavailableError = exceptions_mod.ServiceUnavailableError
        APITokenExpiredError = exceptions_mod.APITokenExpiredError
        APIRequestError = exceptions_mod.APIRequestError


def _default_env_paths() -> list[Path]:
    """Return candidate .env paths for desktop and packaged Android runs."""
    module_path = Path(__file__).resolve()
    candidates: list[Path] = [
        module_path.parents[2] / ".env",  # repo-root layout (local dev/tests)
        module_path.parents[1] / ".env",  # packaged app root (.../app/.env)
        module_path.parent / ".env",      # same directory as service module
        Path.cwd() / ".env",              # current working directory
    ]

    # python-for-android environment hints
    for env_key in ("ANDROID_ARGUMENT", "ANDROID_PRIVATE"):
        raw = os.getenv(env_key)
        if not raw:
            continue
        base = Path(raw)
        candidates.append(base / ".env")
        candidates.append(base / "app" / ".env")

    # De-duplicate while preserving order.
    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def _parse_env_lines(lines) -> dict:
    env = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def _load_dotenv_from_android_assets(asset_name: str = ".env") -> dict | None:
    """Best-effort read for .env embedded via buildozer android.add_assets."""
    try:
        from jnius import autoclass
    except Exception:
        return None

    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        assets = PythonActivity.mActivity.getAssets()
        stream = assets.open(asset_name)
    except Exception:
        return None

    try:
        raw = bytearray()
        while True:
            value = stream.read()
            if value == -1:
                break
            raw.append(value & 0xFF)
    finally:
        try:
            stream.close()
        except Exception:
            pass

    if not raw:
        return {}
    return _parse_env_lines(raw.decode("utf-8", errors="replace").splitlines())


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
    if path is not None:
        candidates = [Path(path)]
    else:
        candidates = _default_env_paths()

    for candidate in candidates:
        if not candidate.exists():
            continue

        env = {}
        with candidate.open(encoding="utf-8") as f:
            env = _parse_env_lines(f)

        # Inject loaded variables into os.environ so other parts of the app can use them
        os.environ.update(env)
        return env

    if path is None:
        env = _load_dotenv_from_android_assets(".env")
        if env is not None:
            os.environ.update(env)
            return env

    searched = ", ".join(str(candidate) for candidate in candidates)
    raise EnvNotFoundError(
        f".env file not found. Looked in: {searched} and Android assets (.env)"
    )

# NOTE: Do not load the .env file at import time. Loading is deferred until
# the service is actually used (via `_get_config()` / `get_weather()`), so
# importing the module does not raise on missing files and leaves the
# `get_weather` symbol available for callers and tests.

def _get_config():
    """Return (URL, API_KEY) from environment or raise MissingAPIConfigError.

    Configuration is validated when the service is actually used (via
    `get_weather()`), which avoids side-effects at import time.
    """
    url = os.getenv("URL")
    api_key = os.getenv("API_KEY")
    if url and api_key:
        return url, api_key

    # If values are not in process env, try loading from .env.
    load_dotenv()
    url = os.getenv("URL")
    api_key = os.getenv("API_KEY")
    if not url or not api_key:
        raise MissingAPIConfigError("Missing URL or API_KEY in environment or .env")
    return url, api_key

# TODO: Insert lat and lon parameters into the URL based on user location as soon as that feature is available.
def build_request_url(url: str, api_key: str, lat: str | float | None = None, lon: str | float | None = None) -> str:
    """Build a request URL from a base URL, ensuring `appid`, `lat`, `lon` are set.

    - Parses the provided `url` and updates query parameters.
    - Ensures `appid` is set to `api_key`.
    - If `lat`/`lon` are provided, sets/overwrites them in the query.

    Returns the full URL string ready for requests.get().
    """
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # Ensure API key param is present under 'appid'
    qs["appid"] = [api_key]

    # Optionally override coordinates
    if lat is not None:
        qs["lat"] = [str(lat)]
    if lon is not None:
        qs["lon"] = [str(lon)]

    new_query = urlencode({k: v[0] for k, v in qs.items()})
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)

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

def get_weather(lat: str | float | None = None, lon: str | float | None = None) -> dict:
    """High-level API: return weather JSON from configured provider.

    Optional `lat` and `lon` may be provided (floats or strings) and will
    be inserted into the request URL query parameters. If omitted, the
    coordinates present in the configured base URL (or none) will be used.
    """
    url, api_key = _get_config()
    request_url = build_request_url(url, api_key, lat=lat, lon=lon)
    return fetch_json(request_url)


__all__ = ["get_weather", "build_request_url", "fetch_json"]
