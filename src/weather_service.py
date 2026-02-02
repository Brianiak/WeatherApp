"""weather_service — fetch weather data using OpenWeatherMap API.

This module reads API configuration from a `.env` file placed at the
project root, constructs the request URL, performs the HTTP GET call,
and pretty-prints the JSON response.

The `.env` file is expected to contain `URL` and `API_KEY` variables.
"""

import os
from pathlib import Path
import requests
import pprint

# Import project-specific exceptions. Use a relative import where possible
try:
    from .exceptions import MissingAPIConfigError
except Exception:
    # Fallback to absolute import to support different execution contexts
    from exceptions import MissingAPIConfigError


def load_dotenv(path=None):
    """Load key=value pairs from a .env file into the process environment.

    If `path` is None, the function looks for a `.env` file in the project
    root (one level above the `src` package). Lines starting with `#` are
    ignored. Values are not interpreted (no quote stripping beyond simple
    split) — they are stored as raw strings.

    Returns a dict of loaded variables.
    """
    if path is None:
        # Find project root (parent of the `src` folder) and look for .env there
        path = Path(__file__).resolve().parents[1] / ".env"
    else:
        path = Path(path)
    if not path.exists():
        # No .env found — return empty mapping but do not crash here.
        return {}
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


# Load environment variables from the project .env file.
load_dotenv()


# Read required configuration from environment variables.
URL = os.getenv("URL")
API_KEY = os.getenv("API_KEY")
if not URL or not API_KEY:
    # Fail fast with an actionable, catchable exception if config is missing.
    raise MissingAPIConfigError("Missing URL or API_KEY in environment or .env")


# Build the full request URL by concatenating the base URL and API key.
request = URL + API_KEY

# Perform the HTTP GET request to the weather API.
res = requests.get(url=request)

# Parse JSON response. This will raise if the response is not JSON.
raw = res.json()


# Pretty-print the returned JSON for debugging / development purposes.
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(raw)
