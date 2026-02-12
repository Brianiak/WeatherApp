# WeatherApp

Kivy-based weather app for desktop and Android.

The app displays weather data from OpenWeatherMap in three views:
- `Heute` (today)
- `Morgen` (tomorrow)
- `5 Tage` (5-day forecast)

It supports live Android GPS, cached last-known location, and a default fallback location when GPS is unavailable.

## Features

- Current weather display (temperature, condition, humidity, wind)
- Tomorrow overview (condition, min/max, day parts)
- 5-day forecast list with weather icons and day-part temperatures
- Responsive card layout for desktop and mobile-like screens
- Android location flow with runtime permissions
- Location fallback chain: live GPS -> cached location -> default coordinates
- Error handling for API/network/config problems

## Tech Stack

- Python
- Kivy (`kivy>=2.3.1`)
- Requests (`requests==2.32.5`)
- Pyjnius for Android bridge (`pyjnius==1.6.1`, non-Windows)
- Ruff + Pytest/Unittest for quality checks

## Project Structure

```text
src/
  main.py
  weather.kv
  base_screen.py
  five_days_screen.py
  app_mixins/
    android_location.py
    location_cache.py
    weather_sync.py
  screens/
    today_screen.py
    tomorrow_screen.py
  services/
    weather_service.py
    config.py
  ui/
    weather_root.py
    forecast_row.py
tests/
  test_weather_service.py
  test_five_days_screen.py
buildozer.spec
requirements.txt
pytest.ini
```

## Configuration

Create a `.env` file in the repository root:

```env
URL=https://api.openweathermap.org/data/2.5/forecast
API_KEY=your_openweathermap_api_key
```

Config resolution order in `src/services/weather_service.py`:
1. Environment variables (`URL`, `API_KEY`)
2. `.env` files (multiple candidate paths, including project root)
3. `src/services/config.py` fallback

Notes:
- Keep real keys out of version control.
- CI/APK workflows expect `src/.env` to exist and copy it to root during build.

## Local Setup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Run the App

From repo root:

```powershell
python src/main.py
```

`src/main.py` prints one weather JSON response at startup and then launches the Kivy UI.

## Tests and Lint

Run unit tests (unittest):

```powershell
python -m unittest discover -s tests
```

Run tests with pytest:

```powershell
python -m pytest -q -p no:cacheprovider
```

Run lint:

```powershell
python -m ruff check .
```

## Android Build

The repository includes `buildozer.spec` and GitHub Actions workflows for APK builds.

Typical local build command (Linux/WSL environment):

```bash
buildozer -v android debug
```

Important Android settings already present:
- Permissions: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_COARSE_LOCATION`, `ACCESS_FINE_LOCATION`, `WAKE_LOCK`
- API levels: `android.minapi = 21`, `android.api = 33`
- Arch: `arm64-v8a`

## CI Workflows

- `.github/workflows/main_caching.yml`: lint + tests + Android build for `main`
- `.github/workflows/lint-test-branches.yml`: branch/PR lint + tests + Android test build
- `.github/workflows/build-apk.yml`: manual APK build (`workflow_dispatch`)

## Known Behavior and Fallbacks

- Desktop platforms without Android `LocationManager` use cached/default coordinates.
- If weather refresh fails, the app keeps working with fallback screen data where implemented.
- Weather refresh is throttled via `WEATHER_REFRESH_INTERVAL` in `src/main.py`.
