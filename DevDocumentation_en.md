# WeatherApp Development Documentation

## Table of Contents
1. [Overview](#overview)
2. [Main Application](#main-application)
3. [Base Classes](#base-classes)
4. [Mixins](#mixins)
5. [Screens](#screens)
6. [UI Components](#ui-components)
7. [Services](#services)
8. [Exception Handling](#exception-handling)

---

## Overview

WeatherApp is a Kivy-based mobile weather application that displays current weather information and 5-day forecasts using the OpenWeatherMap API. The app features GPS-based location tracking on Android devices with fallback caching mechanisms.

### Architecture
- **Kivy Framework**: Cross-platform UI framework for desktop and mobile
- **Mixin Pattern**: GPS location, caching, and weather sync separated into reusable mixins
- **Screen Manager**: Navigation between three main screens (Today, Tomorrow, 5-day forecast)
- **OpenWeatherMap API**: Weather data backend

---

## Main Application

### `src/main.py`

#### Class: `WeatherApp`
Main application class combining GPS location and weather data features.

**Parent Classes:**
- `AndroidLocationMixin`: Android GPS handling
- `LocationCacheMixin`: Location caching functionality
- `WeatherSyncMixin`: Weather data synchronization
- `App`: Kivy application base class

**Attributes:**
- `kv_file` (str): Path to the KV layout file
- `GPS_TIMEOUT` (int): GPS acquisition timeout in seconds (45)
- `WEATHER_REFRESH_INTERVAL` (int): Weather API refresh throttle interval (60 seconds)
- `current_lat`, `current_lon` (float): Current location coordinates
- `last_gps_lat`, `last_gps_lon` (float): Last successful GPS coordinates
- `_weather_from_cache` (bool): Flag indicating if weather data is from cache
- `_has_live_gps_fix` (bool): Flag indicating if live GPS fix was obtained

**Methods:**

##### `on_start()`
Initialize the application on startup.

Loads the last cached location and initiates the location flow. On Android devices, starts the GPS permission request and location tracking. On other platforms, uses fallback coordinates (London).

**Parameters:** None

**Returns:** None

**Example:**
```python
# Called automatically by Kivy on app start
app.on_start()  # Loads cached location and starts GPS on Android
```

---

##### `navigate(key: str)`
Navigate to a different screen in the application.

**Parameters:**
- `key` (str): Screen identifier. Valid values are:
  - `'today'`: Today's weather screen
  - `'tomorrow'`: Tomorrow's weather screen
  - `'5days'`: 5-day forecast screen

**Returns:** None

**Example:**
```python
app.navigate('5days')  # Navigate to 5-day forecast screen
```

---

## Base Classes

### `src/base_screen.py`

#### Class: `BaseWeatherScreen`
Base class for all weather screens providing responsive layout support.

Handles automatic resize detection and responsive layout updates when window size changes. All weather screens inherit from this class to ensure consistent responsive behavior.

**Properties:**
- `card_width` (NumericProperty): Width of weather card (350dp)

**Methods:**

##### `on_kv_post(base_widget)`
Called after KV file is processed for this widget.

Sets up window resize event binding to trigger responsive layout updates whenever the window is resized.

**Parameters:**
- `base_widget`: The root widget from the KV file

**Returns:** None

---

##### `_on_window_resize(_window, size)`
Handle window resize events.

Internal callback triggered by window size changes. Triggers the `on_responsive_update()` method to allow subclasses to respond to size changes.

**Parameters:**
- `_window`: The window object (unused)
- `size` (tuple): Tuple of (width, height) in pixels

**Returns:** None

---

##### `on_responsive_update()`
Called when responsive layout update is needed.

Override this method in subclasses to implement custom responsive behavior such as recalculating RecycleView heights or adjusting widget dimensions based on available space.

**Parameters:** None

**Returns:** None

---

## Mixins

### `src/app_mixins/weather_sync.py`

#### Class: `WeatherSyncMixin`
Mixin providing weather data fetching and display synchronization.

Handles fetching weather data from the OpenWeatherMap API, managing location coordinates, updating all weather UI screens with current and forecast data, and handling API errors with fallback to cached data.

**Attributes:**
- `_weather_from_cache` (bool): Flag tracking if current weather data came from cache

**Methods:**

##### `_should_refresh_weather() -> bool`
Check if enough time has elapsed to refresh weather data.

Uses the `WEATHER_REFRESH_INTERVAL` class attribute to throttle API calls and avoid excessive requests to the weather service.

**Parameters:** None

**Returns:**
- `bool`: True if refresh interval elapsed, False otherwise

**Example:**
```python
if app._should_refresh_weather():
    data = weather_service.get_weather(lat, lon)
```

---

##### `_apply_location(lat, lon, force_refresh=False, track_as_gps=False)`
Apply location coordinates and fetch weather data.

Stores the provided coordinates, optionally saves them to cache, and fetches weather data from the API. Updates all weather UI screens with the fetched data. Falls back to cached data if the API call fails.

**Parameters:**
- `lat` (float): Latitude coordinate (-90 to 90)
- `lon` (float): Longitude coordinate (-180 to 180)
- `force_refresh` (bool): Force API refresh even if interval throttle active (default: False)
- `track_as_gps` (bool): Mark as live GPS fix and save to location cache (default: False)

**Returns:** None

**Example:**
```python
# Apply GPS location with forced refresh (first GPS fix)
app._apply_location(52.5200, 13.4050, force_refresh=True, track_as_gps=True)
```

---

##### `_log_location_roundtrip(requested_lat, requested_lon, weather_data)`
Log the difference between requested and API-returned coordinates.

Extracts the city location from the weather API response and compares it with the requested coordinates to verify location accuracy. Alerts if the coordinates differ significantly (>1 degree).

**Parameters:**
- `requested_lat` (float): The latitude that was requested
- `requested_lon` (float): The longitude that was requested
- `weather_data` (dict): Weather API response with city coordinate info

**Returns:** None

---

##### `_location_label_from_error(error, track_as_gps) -> str`
Generate a user-friendly location label based on error type.

Maps specific exception types to appropriate German error messages for display in the UI. Returns different messages based on the error type and whether GPS tracking was active.

**Parameters:**
- `error` (Exception): The exception that was raised
- `track_as_gps` (bool): Whether this was a GPS tracking attempt

**Returns:**
- `str`: German error message for display in the UI

**Error Mapping:**
- `EnvNotFoundError` → "Standortname nicht verfuegbar (.env fehlt)"
- `MissingAPIConfigError` → "Standortname nicht verfuegbar (API Konfig fehlt)"
- `APITokenExpiredError` → "Standortname nicht verfuegbar (API Key ungueltig)"
- `NetworkError` → "Standortname nicht verfuegbar (kein Internet)"
- `ServiceUnavailableError` → "Standortname nicht verfuegbar (Wetterdienst down)"
- `APIRequestError` → "Standortname nicht verfuegbar (API Anfragefehler)"

---

##### `_update_location_labels_from_weather(weather_data, track_as_gps=False) -> str | None`
Extract location label from weather data and update UI screens.

Parses the city name and country from the weather API response and updates location text displayed on Today and Tomorrow screens.

**Parameters:**
- `weather_data` (dict): Weather API response containing city info
- `track_as_gps` (bool): Whether this location came from live GPS (default: False)

**Returns:**
- `str | None`: The formatted location label, or None on extraction failure

---

##### `_extract_location_label(weather_data) -> str | None`
Extract city and country name from weather API response.

Parses the 'city' object from the API response to get location information. Returns formatted string "City, Country" or just "City" if country is unavailable.

**Parameters:**
- `weather_data` (dict): Weather API response containing city info

**Returns:**
- `str | None`: Location label like "Berlin, DE" or None if not found

---

##### `_refresh_forecast_screen()`
Trigger data refresh on the 5-day forecast screen.

Schedules an asynchronous reload of forecast data on the FiveDaysScreen to display the latest weather forecast for the current coordinates.

**Parameters:** None

**Returns:** None

---

##### `_update_weather_display(weather_data)`
Update all weather screens with current and forecast data.

Parses the weather API response and updates:
- Today screen: current temperature, weather condition, hourly forecast
- Tomorrow screen: min/max temperature, hourly forecast, weather icon
- Five days screen: forecast data refresh

Uses cache indicator icons and sets location labels. Updates are applied asynchronously to the UI screens.

**Parameters:**
- `weather_data` (dict): Weather API response with forecast entries

**Returns:** None

---

### `src/app_mixins/android_location.py`

#### Class: `AndroidLocationMixin`
Mixin providing Android GPS location tracking and permission handling.

Manages Android location permissions, initializes GPS tracking via the Android LocationManager service, handles location updates with provider fallback, and implements timeout fallback to cached locations when GPS acquisition fails or is not available.

**Attributes:**
- `_location_manager`: Android LocationManager instance
- `_location_listener`: Custom LocationListener instance
- `_gps_timeout_event`: Kivy Clock event for GPS timeout

**Methods:**

##### `_start_android_location_flow()`
Start the Android GPS location acquisition flow.

Requests necessary location permissions (coarse and fine location). If permissions are already granted, immediately starts GPS tracking. If permissions are denied, falls back to cached location.

**Parameters:** None

**Returns:** None

---

##### `_on_android_permissions_result(permissions, grants)`
Handle the result of Android permission requests.

Called when the user responds to permission requests. If any location permission is granted, starts GPS. If all permissions are denied, falls back to cached or default location.

**Parameters:**
- `permissions`: List of requested permission identifiers
- `grants`: List of booleans indicating if each permission was granted

**Returns:** None

---

##### `_start_gps()`
Start GPS location updates on Android.

Initializes the Android LocationManager and begins requesting location updates from available providers (GPS and/or Network). Sets up a timeout fallback (`GPS_TIMEOUT` seconds) to use cached location if GPS acquisition fails.

On non-Android platforms, falls back to cached or default location.

**Parameters:** None

**Returns:** None

---

##### `_init_android_location_manager()`
Initialize Android LocationManager and custom LocationListener.

Sets up the Android system LocationManager service and creates a custom LocationListener that bridges Android location callbacks to Kivy Clock for proper UI thread scheduling.

**Parameters:** None

**Returns:** None

---

##### `_enabled_android_providers() -> list[str]`
Get list of currently enabled Android location providers.

Queries the Android LocationManager for available location providers (GPS_PROVIDER and NETWORK_PROVIDER) and returns only those that are currently enabled.

**Parameters:** None

**Returns:**
- `list[str]`: List of enabled provider names (may be empty)

---

##### `_start_android_location_updates()`
Start requesting location updates from Android providers.

Registers the custom LocationListener with the Android LocationManager for all enabled providers. Also emits the last known location for each provider to immediately provide a location fix if available.

**Parameters:** None

**Returns:** None

**Raises:**
- `RuntimeError`: If no location providers are enabled

---

##### `_emit_android_last_known_location(providers)`
Emit the last known location for each provider.

Retrieves and emits the last known location cached by Android's LocationManager for each enabled provider. This provides an immediate location fix without waiting for fresh GPS fixes.

**Parameters:**
- `providers` (list[str]): List of location provider names to query

**Returns:** None

---

##### `_gps_timeout_fallback(_dt)`
Fallback handler called when GPS acquisition times out.

Called when `GPS_TIMEOUT` seconds elapse without getting a GPS fix. Falls back to the last cached location or default coordinates.

**Parameters:**
- `_dt`: Delta time (used by Kivy Clock, unused)

**Returns:** None

---

##### `on_gps_status(stype, status)`
Handle GPS status change events from Android LocationListener.

Called when GPS provider status changes (enabled, disabled, etc.). Falls back to cached location if status indicates GPS is degraded.

**Parameters:**
- `stype` (str): Type of status change ('provider' or 'status')
- `status` (str): Description of the status change

**Returns:** None

---

##### `on_gps_location(**kwargs)`
Handle new GPS location update from Android LocationListener.

Validates the received coordinates, cancels any pending timeout, and applies the location for weather data fetching. Calls `_apply_location()` with `force_refresh=True` on first GPS fix.

**Parameters:**
- `**kwargs`: Must contain 'lat' and 'lon' as floats, optional 'accuracy'

**Returns:** None

---

##### `on_stop()`
Cleanup GPS resources on application stop.

Unregisters the LocationListener from the Android LocationManager to stop receiving GPS updates. Called automatically when the app exits.

**Parameters:** None

**Returns:** None

---

### `src/app_mixins/location_cache.py`

#### Class: `LocationCacheMixin`
Mixin providing location caching and fallback location functionality.

Handles saving and loading the last known GPS location to disk cache, providing fallback coordinates when GPS is unavailable, and formatting location labels for UI display.

**Attributes:**
- `last_gps_lat`, `last_gps_lon` (float): Last cached GPS coordinates
- `last_location_label` (str): Last cached location label

**Methods:**

##### `_use_fallback_location()`
Use hardcoded fallback coordinates and apply them.

Uses London coordinates (51.5074, -0.1278) as a fallback when no GPS fix is available and no cached location exists.

**Parameters:** None

**Returns:** None

---

##### `_last_location_cache_path() -> Path`
Get the filesystem path to the location cache file.

**Parameters:** None

**Returns:**
- `Path`: Path to last_location.json in the user data directory

---

##### `_load_last_known_location()`
Load the last known location from disk cache.

Reads the cached location JSON file and restores the coordinates and location label. If loading fails, silently returns without error.

**Parameters:** None

**Returns:** None

---

##### `_save_last_known_location(lat, lon, label=None)`
Save the current location to disk cache.

Saves coordinates and optional location label to a JSON file in the user data directory for persistence across app sessions.

**Parameters:**
- `lat` (float): Latitude coordinate to save
- `lon` (float): Longitude coordinate to save
- `label` (str | None): Optional location label (city, country)

**Returns:** None

---

##### `_use_last_known_location_or_default(reason)`
Apply last cached location or fallback to default coordinates.

Attempts to use the previously saved GPS location. If no cached location exists, falls back to hardcoded default coordinates.

**Parameters:**
- `reason` (str): The reason why this fallback was triggered

**Returns:** None

---

##### `_coordinates_in_range(lat, lon) -> bool`
Validate that coordinates are within valid geographic ranges.

**Parameters:**
- `lat` (float): Latitude to validate (-90 to 90)
- `lon` (float): Longitude to validate (-180 to 180)

**Returns:**
- `bool`: True if coordinates are valid, False otherwise

---

##### `_format_location_label(label, is_live_gps) -> str`
Format a location label for display, optionally with source prefix.

Optionally prepends "GPS:" or "Fallback:" prefix based on the location source. Controlled by the `SHOW_LOCATION_SOURCE_PREFIX` class attribute.

**Parameters:**
- `label` (str): The base location label
- `is_live_gps` (bool): Whether this is from live GPS or fallback

**Returns:**
- `str`: The formatted location label for display

---

##### `_set_location_labels(label)`
Update location text on all weather screens.

Sets the `location_text` property on Today and Tomorrow screens to display the provided location label.

**Parameters:**
- `label` (str): The location label to display

**Returns:** None

---

## Screens

### `src/screens/today_screen.py`

#### Class: `HourForecast`
Hour forecast tile widget with time, icon, temperature, and description.

**Properties:**
- `time_text` (StringProperty): Time in HH:MM format
- `icon_source` (StringProperty): Path to weather icon
- `temp_text` (StringProperty): Temperature with degree symbol
- `desc_text` (StringProperty): Weather description

---

#### Class: `TodayScreen`
Screen model for the 'Today' view.

Provides properties used by the KV layout and a helper to populate the horizontal hourly forecast area with items built from the API 3-hourly forecast entries.

**Properties:**
- `location_text` (StringProperty): Current location label
- `location_icon_source` (StringProperty): Location icon (GPS or cached)
- `temp_text` (StringProperty): Current temperature
- `condition_text` (StringProperty): Current weather condition
- `weather_icon` (StringProperty): Current weather icon path
- `hourly_items` (ListProperty): List of hourly forecast entries

**Methods:**

##### `set_hourly_data(entries)`
Populate the hourly horizontal forecast from a list of API entries.

Extract time, icon, temperature, and description from each entry and create HourForecast widgets. UI definition is in weather.kv. Shows up to 8 3-hourly entries.

**Parameters:**
- `entries` (list): List of API forecast dictionaries

**Returns:** None

---

### `src/screens/tomorrow_screen.py`

#### Class: `TomorrowScreen`
Display tomorrow's weather forecast with detailed hourly information.

Shows tomorrow's weather conditions including min/max temperatures, hourly forecast by time of day, and an hourly breakdown for the entire day.

**Properties:**
- `location_text` (StringProperty): Tomorrow's location label
- `location_icon_source` (StringProperty): Location icon
- `condition_text` (StringProperty): Tomorrow's weather condition
- `minmax_text` (StringProperty): Min/Max temperature range
- `dayparts_text` (StringProperty): Temps by time of day
- `weather_icon` (StringProperty): Tomorrow's weather icon
- `hourly_items` (ListProperty): Tomorrow's hourly forecast

**Methods:**

##### `set_hourly_data(entries)`
Populate the hourly forecast for tomorrow.

Extracts hourly weather data and creates HourForecast widgets for each entry throughout tomorrow, displaying the full day's hourly forecast.

**Parameters:**
- `entries` (list): List of API forecast entries for tomorrow

**Returns:** None

---

### `src/screens/five_days_screen.py`

#### Class: `FiveDaysScreen`
Screen displaying a 5-day weather forecast with temperature and condition details.

This screen shows a scrollable list of 5 consecutive days with daily information: date, weather icon, min/max temperature, and temperature breakdown by time of day (morning, midday, evening, night).

**Properties:**
- `forecast_items` (ListProperty): List of 5-day forecast dictionaries
- `card_width` (NumericProperty): Width of weather card

**Key Methods:**

##### `on_kv_post(base_widget)`
Initialize screen after KV file is processed.

Fetches weather forecast data from the API and populates the forecast_items list with 5 days of weather data. Calculates the optimal RecycleView height based on available space.

**Parameters:**
- `base_widget`: The base widget passed by Kivy during initialization

**Returns:** None

---

##### `_load_forecast_data()`
Fetch and process 5-day forecast data from the weather API.

Makes an API call to get forecast data, processes it into daily summaries with min/max temperatures and time-of-day breakdowns, then updates the forecast_items list.

Falls back to hardcoded data if API call fails.

**Parameters:** None

**Returns:** None

---

##### `_process_forecast_data(data) -> list`
Process API forecast data into daily summaries.

Extracts 5 days of weather information from the 3-hour interval API response, calculating min/max temperatures and extracting temperatures for different times of day.

**Parameters:**
- `data` (dict): API response containing forecast list with 3-hour intervals

**Returns:**
- `list`: List of dictionaries with forecast information for 5 days

---

##### `_load_fallback_data()`
Load hardcoded fallback data for testing when API call fails.

Provides static 5-day forecast data with predefined dates, temperatures, and weather icons for testing and development purposes.

**Parameters:** None

**Returns:** None

---

##### `on_responsive_update()`
Handle responsive layout updates when window size changes.

Called whenever the window is resized. Recalculates and updates the RecycleView height to fit the new available space.

**Parameters:** None

**Returns:** None

---

##### `_update_rv_height()`
Calculate and update the RecycleView height based on available space.

Determines the optimal height for the RecycleView by:
1. Calculating total content height (number of items × row height)
2. Subtracting navigation and padding heights from card height
3. Applying minimum (140dp) and maximum constraints
4. Using the smaller of calculated or maximum height

The RecycleView height is set to ensure all forecast items are visible while respecting screen space constraints.

**Parameters:** None

**Returns:** None

---

## UI Components

### `src/ui/weather_root.py`

#### Class: `WeatherRoot`
Root widget managing screen navigation and transitions.

Controls the screen manager, handles navigation between weather screens (Today, Tomorrow, 5-day forecast) with animated slide transitions, and keeps the navigation bar synchronized with the current screen.

**Methods:**

##### `on_kv_post(base_widget)`
Called after KV file is processed.

Initializes the root widget by navigating to the 'today' screen.

**Parameters:**
- `base_widget`: The root widget from the KV file

**Returns:** None

---

##### `navigate(key)`
Navigate to a different screen with animated transition.

Attempts to navigate to the specified screen with a slide transition effect. Determines transition direction based on current and target screen positions.

**Parameters:**
- `key` (str): Screen identifier ('today', 'tomorrow', or '5days')

**Returns:** None

---

##### `_sync_nav_for_current()`
Update navigation buttons to highlight the current screen.

Sets the appropriate navigation button to 'down' state to visually indicate which screen is currently displayed.

**Parameters:** None

**Returns:** None

---

### `src/ui/forecast_row.py`

#### Class: `ForecastRow`
Forecast row widget displaying daily forecast information.

Displays a single row in the 5-day forecast list with date, weather icon, min/max temperatures, and hourly temperature breakdown (morning, midday, evening, night).

**Properties:**
- `date_text` (StringProperty): Date in format "Mo, 22.01."
- `icon_source` (StringProperty): Path to weather icon image
- `minmax_text` (StringProperty): Min/Max temperature display
- `dayparts_text` (StringProperty): Space-separated temps for morning, midday, evening, night

---

## Services

### `src/services/weather_service.py`

This module handles all weather data fetching from the OpenWeatherMap API with comprehensive error handling and caching mechanisms.

**Key Functions:**

#### `load_dotenv(path=None)`
Load key=value pairs from a .env file into the process environment.

Searches for a .env file in multiple locations (project root, Android assets, current directory). Values are stored as raw strings without quote stripping.

**Parameters:**
- `path` (str | None): Explicit path to .env file, or None to search default locations

**Returns:**
- `dict`: Dictionary of loaded variables

**Raises:**
- `EnvNotFoundError`: If no .env file found in any location

---

#### `_get_config()`
Return (URL, API_KEY) from environment or raise MissingAPIConfigError.

Configuration is validated when the service is actually used (via `get_weather()`), which avoids side-effects at import time.

**Resolution order:**
1. Environment variables (URL, API_KEY)
2. .env file (filesystem or Android assets)
3. config.py fallback (always bundled as a .py file in the APK)

**Parameters:** None

**Returns:**
- `tuple`: (url, api_key) strings

**Raises:**
- `MissingAPIConfigError`: If neither environment nor .env nor fallback config found

---

#### `build_request_url(url, api_key, lat=None, lon=None) -> str`
Build a request URL from a base URL, ensuring appid, lat, lon are set.

- Parses the provided URL and updates query parameters
- Ensures appid is set to api_key
- If lat/lon are provided, sets/overwrites them in the query

**Parameters:**
- `url` (str): Base API URL
- `api_key` (str): OpenWeatherMap API key
- `lat` (str | float | None): Optional latitude for location-based query
- `lon` (str | float | None): Optional longitude for location-based query

**Returns:**
- `str`: Full URL string ready for requests.get()

---

#### `fetch_json(request_url, timeout=10) -> dict`
Perform HTTP GET against request_url and return parsed JSON.

Handles various error conditions with specific exception types for proper error handling upstream.

**Parameters:**
- `request_url` (str): Complete URL to fetch
- `timeout` (int): Request timeout in seconds (default: 10)

**Returns:**
- `dict`: Parsed JSON response

**Raises:**
- `NetworkError`: Network connectivity problems
- `APITokenExpiredError`: API returns 401 Unauthorized
- `ServiceUnavailableError`: API returns 5xx status
- `APIRequestError`: Other non-successful responses or invalid JSON

---

#### `get_weather(lat=None, lon=None) -> dict`
High-level API: return weather JSON from configured provider.

Optional lat/lon may be provided (floats or strings) and will be inserted into the request URL query parameters. If omitted, the coordinates present in the configured base URL (or none) will be used.

If the API call fails, attempts to return cached weather data from the last successful request. The response will have a '__cached__' flag set to True when data comes from cache.

**Parameters:**
- `lat` (str | float | None): Optional latitude
- `lon` (str | float | None): Optional longitude

**Returns:**
- `dict`: Weather data from API or cache with possible '__cached__' flag

**Raises:**
- `APIRequestError`: If both API call and cache retrieval fail

---

## Exception Handling

### `src/utils/exceptions.py`

All custom exceptions inherit from standard Python exceptions for compatibility.

#### `MissingAPIConfigError`
Raised when required API configuration is missing.

This exception signals that URL and/or API_KEY were not found in the environment or the project's .env file.

---

#### `EnvNotFoundError`
Raised when the project's .env file cannot be found.

This distinct exception makes it possible to differentiate between a missing configuration file and other configuration errors (like a missing key inside a present .env).

---

#### `NetworkError`
Raised when a network-level error prevents contacting the API.

Examples include lack of internet connectivity or DNS resolution failures.

---

#### `ServiceUnavailableError`
Raised when the remote weather service returns a 5xx error.

---

#### `APITokenExpiredError`
Raised when the API responds with an authentication error (e.g. 401).

---

#### `APIRequestError`
Generic error for failed API requests not covered by other exceptions.

---

## Development Guidelines

### Adding New Functions
1. Always add comprehensive docstrings following the format in this guide
2. Include parameter types and return types
3. Document any exceptions that may be raised
4. Provide usage examples for complex functions
5. Update this document with new function documentation

### Error Handling
- Use specific exception types from `utils/exceptions.py`
- Catch exceptions at the appropriate level (API layer, UI layer, etc.)
- Provide user-friendly German error messages in the UI
- Log errors with context for debugging

### Location and Weather Data
- Always validate coordinates before use
- Handle API responses gracefully with fallback to cache
- Update location labels on all relevant screens
- Respect WEATHER_REFRESH_INTERVAL to avoid excessive API calls

---

**Last Updated:** February 2026
**Documentation Version:** 1.0
