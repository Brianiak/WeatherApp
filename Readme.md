# WeatherApp

Kivy-basierte Wetter-App fuer Desktop und Android (Buildozer-Appname: `Weatherly`).

Die App nutzt OpenWeatherMap-Forecastdaten (`/data/2.5/forecast`) und zeigt drei Ansichten:
- `Heute`
- `Morgen`
- `5 Tage`

## Features (aktueller Stand)

- Aktuelles Wetter mit Temperatur, Bedingung und Standortlabel.
- Stundenvorschau fuer `Heute` (max. 8 Eintraege, horizontal).
- Stundenvorschau fuer `Morgen` (alle verfuegbaren Eintraege, horizontal).
- 5-Tage-Ansicht mit:
  - Min/Max pro Tag
  - Tagesabschnitte `Morgen / Mittag / Abend / Nacht`
- Android-Standortfluss mit Runtime-Permissions (`COARSE`/`FINE`) und `LocationManager`.
- Fallback-Kette fuer Standort:
  - Live-GPS
  - Letzter erfolgreicher GPS-Standort (`user_data_dir/last_location.json`)
  - Default-Koordinaten London (`51.5074, -0.1278`)
- Wetter-Cache in `src/json/last_weather.json` bei erfolgreicher API-Antwort.
- API-Fallback auf Wetter-Cache bei Request-Fehlern.
- Kennzeichnung von Cache-Daten ueber `__cached__` Flag in `weather_service.get_weather()`.
- Spezifische Fehlerklassen fuer API/Netzwerk/Config (`src/utils/exceptions.py`).

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
  conftest.py
  test_android_location_mixin.py
  test_base_and_ui.py
  test_location_cache_mixin.py
  test_screens_today_tomorrow.py
  test_weather_sync_mixin.py
  test_weather_service.py
  test_five_days_screen.py
.github/workflows/
  build-apk.yml
  lint-test-branches.yml
  protect-main.yml
buildozer.spec
requirements.txt
pytest.ini
```

## Konfiguration

### 1) `.env` anlegen

Beispiel fuer `src/.env`:

```env
URL=https://api.openweathermap.org/data/2.5/forecast
API_KEY=your_openweathermap_api_key
```

Hinweis:
- Die Build-Workflows erwarten aktuell `src/.env` und kopieren sie nach `.env` im Repo-Root.
- Lokal kannst du alternativ auch `.env` im Repo-Root verwenden.

### 2) Aufloesungsreihenfolge fuer URL/API_KEY

`src/services/weather_service.py` loest Konfiguration in dieser Reihenfolge auf:
1. Bereits gesetzte Umgebungsvariablen (`URL`, `API_KEY`)
2. `.env` von Dateisystem-Kandidaten (u. a. Repo-Root, `src/`, CWD)
3. Android-Assets (`.env`, falls im APK-Bundle vorhanden)
4. Fallback aus `src/services/config.py`

Wenn nichts verfuegbar ist, wird `MissingAPIConfigError` geworfen.

### 3) Sicherheit

`src/services/config.py` enthaelt derzeit einen hardcodierten Fallback-Key.
Empfehlung:
- Echte Keys nicht committen.
- Keys ueber `.env` oder GitHub Secrets bereitstellen.
- Bereits veroeffentlichte Keys im OpenWeatherMap-Konto rotieren.

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

Beim direkten Start als Skript wird einmal die rohe Wetter-JSON ausgegeben, danach startet die UI.

## Tests und Lint

```powershell
python -m unittest discover -s tests
python -m pytest tests/ -q -p no:cacheprovider
python -m ruff check .
```

Zusatz:
- `pytest.ini` hat Coverage-Optionen inkl. `--cov-fail-under=70`.
- CI nutzt fuer Kivy-Tests `xvfb-run`.

## Android Build (lokal, Linux/WSL empfohlen)

```bash
buildozer -v android debug
```

Wichtige `buildozer.spec`-Punkte:
- `android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_COARSE_LOCATION,ACCESS_FINE_LOCATION,WAKE_LOCK`
- `android.api = 33`
- `android.minapi = 21`
- `android.ndk = 25b`
- `android.archs = arm64-v8a`
- `source.include_exts` enthaelt `env` (fuer `.env` Packaging)

## CI/CD Workflows (aktueller Stand)

- `lint-test-branches.yml`
  - Trigger: `pull_request` und `push` auf allen Branches ausser `main/master`
  - Jobs: `lint-test` und danach `build-android-apk-testing`
  - Hinweis: Der Test-Step im Job `lint-test` hat `continue-on-error: true`
- `build-apk.yml`
  - Trigger: `push` auf `main` und manuell (`workflow_dispatch`)
  - Jobs: `lint`, `test`, `build-android`
  - Hinweis: `build-android` hat aktuell kein aktives `needs` auf `lint`/`test`
- `protect-main.yml`
  - Trigger: `push` auf `main`
  - Blockiert Commits ohne PR-Verknuepfung

Hinweis:
Alle Android-Build-Workflows brechen ab, wenn `src/.env` fehlt.

## Laufzeitdetails

- Desktop ohne Android `LocationManager` nutzt automatisch Fallback-Koordinaten oder letzten Standort-Cache.
- GPS-Timeout ist in `WeatherApp.GPS_TIMEOUT = 45`.
- Wetter-Refresh ist in `WeatherApp.WEATHER_REFRESH_INTERVAL = 60` Sekunden gedrosselt.
- Bei gecachten Wetterdaten wird in der UI das Icon `icons/no_location.png` statt `icons/location.png` gesetzt.
