# WeatherApp

Kivy-basierte Wetter-App fuer Desktop und Android.

Die App zeigt OpenWeatherMap-Daten in drei Ansichten:
- `Heute`
- `Morgen`
- `5 Tage`

## Features

- Aktuelles Wetter (Temperatur, Zustand, Ort)
- Horizontale Stundenvorschau fuer `Heute`
- Horizontale Stundenvorschau fuer `Morgen`
- 5-Tage-Liste mit Min/Max und Tagesabschnitten (Morgen/Mittag/Abend/Nacht)
- Android-GPS mit Runtime-Permissions
- Standort-Fallback-Kette:
  - Live GPS
  - Letzter erfolgreicher Standort aus Cache
  - Default-Koordinaten (London: `51.5074, -0.1278`)
- Robuste API-Fehlerbehandlung (`NetworkError`, `ServiceUnavailableError`, `APITokenExpiredError`, ...)

## Tech Stack

- Python 3.11
- Kivy (`kivy>=2.3.1`)
- Requests (`requests==2.32.5`)
- Pyjnius (`pyjnius==1.6.1`, nur non-Windows)
- Tests: `unittest` + `pytest`
- Lint: `ruff`

## Projektstruktur

```text
src/
  main.py
  weather.kv
  base_screen.py
  .env
  app_mixins/
    android_location.py
    location_cache.py
    weather_sync.py
  screens/
    today_screen.py
    tomorrow_screen.py
    five_days_screen.py
  services/
    weather_service.py
    config.py
  ui/
    weather_root.py
    forecast_row.py
  utils/
    exceptions.py
  icons/
  json/
    last_weather.json

tests/
  test_weather_service.py
  test_five_days_screen.py

.github/workflows/
  build-apk.yml
  lint-test-branches.yml
  main_caching.yml
  protect-main.yml

buildozer.spec
requirements.txt
pytest.ini
```

## Konfiguration

### 1) Umgebungsvariablen (`URL`, `API_KEY`)

Beispiel fuer `.env`:

```env
URL=https://api.openweathermap.org/data/2.5/forecast
API_KEY=your_openweathermap_api_key
```

### 2) Welche `.env` wird genutzt?

Die App sucht die Konfiguration in dieser Reihenfolge:
1. Bereits gesetzte Umgebungsvariablen (`URL`, `API_KEY`)
2. `.env`-Dateien (mehrere Kandidaten, inkl. Repo-Root und Laufzeitpfade)
3. Android-Assets (`.env`)
4. Fallback aus `src/services/config.py`

### 3) Wichtig fuer CI/Android Build

Die GitHub-Workflows erwarten `src/.env` und kopieren sie beim Build nach `.env` im Repo-Root.

## Sicherheitshinweis

`src/services/config.py` enthaelt aktuell einen Fallback-API-Key.

Empfehlung:
- Keine echten Keys in `config.py` committen.
- Key nur ueber `.env`/Secrets bereitstellen.
- Bereits geleakte Keys im OpenWeatherMap-Account rotieren.

## Lokales Setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## App starten

```powershell
python src/main.py
```

Hinweis: Beim Start wird einmal die rohe Wetter-JSON auf der Konsole ausgegeben, danach startet die UI.

## Tests und Lint

```powershell
python -m unittest discover -s tests
python -m pytest -q -p no:cacheprovider
python -m ruff check .
```

## Android Build (Linux/WSL empfohlen)

```bash
buildozer -v android debug
```

Relevante Einstellungen in `buildozer.spec`:
- Permissions: `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_COARSE_LOCATION`, `ACCESS_FINE_LOCATION`, `WAKE_LOCK`
- `android.minapi = 21`
- `android.api = 33`
- Architektur: `arm64-v8a`

## CI Workflows

- `main_caching.yml`: Build-Job (manual trigger)
- `lint-test-branches.yml`: Lint, Tests, Android-Testbuild fuer Branches/PRs
- `build-apk.yml`: Lint, Tests, Android-Build auf `main` + manuell
- `protect-main.yml`: blockt direkte Pushes auf `main` ohne PR-Bezug

## Bekannte Laufzeit-Details

- Auf Desktop gibt es keinen Android `LocationManager`; dann greift der Fallback-Flow.
- Wetter-Refresh ist in `src/main.py` ueber `WEATHER_REFRESH_INTERVAL` gedrosselt.
- Letzter erfolgreicher Standort wird als `last_location.json` im `user_data_dir` gecacht.
