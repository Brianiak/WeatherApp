from pathlib import Path
import json
import time

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform as kivy_platform

try:
    from jnius import autoclass, PythonJavaClass, java_method
except Exception:  # pragma: no cover - desktop/test environments
    autoclass = None
    PythonJavaClass = object

    def java_method(_signature):
        def decorator(func):
            return func

        return decorator

from base_screen import BaseWeatherScreen
from five_days_screen import FiveDaysScreen  # noqa: F401
import services.weather_service as weather_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KV_PATH = Path(__file__).with_name("weather.kv")

for resource_dir in (PROJECT_ROOT, KV_PATH.parent):
    resource_add_path(str(resource_dir))


class ForecastRow(BoxLayout):
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")


class TodayScreen(BaseWeatherScreen):
    location_text = StringProperty("Standort wird ermittelt...")
    temp_text = StringProperty("13\u00b0")
    condition_text = StringProperty("Clouds")
    humidity_text = StringProperty("82%")
    wind_text = StringProperty("6 km/h")


class TomorrowScreen(BaseWeatherScreen):
    location_text = StringProperty("Standort wird ermittelt...")
    condition_text = StringProperty("Clouds")
    minmax_text = StringProperty("Min. Temp / Max. Temp")
    dayparts_text = StringProperty("Morgen / Mittag / Abend / Nacht")


class WeatherRoot(BoxLayout):
    def on_kv_post(self, base_widget):
        self.navigate("today")

    def navigate(self, key: str):
        sm = self.ids.sm
        mapping = {"today": "today", "tomorrow": "tomorrow", "5days": "five_days"}
        target = mapping.get(key)
        if not target:
            return

        sm.current = target
        self._sync_nav_for_current()

    def _sync_nav_for_current(self):
        sm = self.ids.sm
        screen = sm.get_screen(sm.current)

        if "nav" not in screen.ids:
            return

        nav = screen.ids.nav
        if sm.current == "today":
            nav.ids.btn_today.state = "down"
        elif sm.current == "tomorrow":
            nav.ids.btn_tomorrow.state = "down"
        elif sm.current == "five_days":
            nav.ids.btn_5days.state = "down"


class WeatherApp(App):
    kv_file = str(KV_PATH)
    _gps_timeout_event = None
    GPS_TIMEOUT = 45  # seconds
    WEATHER_REFRESH_INTERVAL = 60  # seconds
    SHOW_LOCATION_SOURCE_PREFIX = False
    _last_weather_refresh_ts = 0.0
    current_lat = None
    current_lon = None
    last_gps_lat = None
    last_gps_lon = None
    last_location_label = None
    _has_live_gps_fix = False
    _location_manager = None
    _location_listener = None

    def on_start(self):
        self._load_last_known_location()

        # Use Android LocationManager via pyjnius on Android only.
        if kivy_platform == "android":
            self._start_android_location_flow()
        else:
            print(
                f"Platform '{kivy_platform}' has no Android LocationManager backend; "
                "using fallback coordinates."
            )
            self._use_last_known_location_or_default(
                "platform without Android GPS support"
            )

    def _start_android_location_flow(self):
        try:
            from android.permissions import Permission, check_permission, request_permissions

            required = [Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION]
            if any(check_permission(permission) for permission in required):
                self._start_gps()
                return

            request_permissions(required, self._on_android_permissions_result)
        except Exception as e:
            print("Android permission flow failed:", e)
            self._use_last_known_location_or_default("android permission flow failed")

    def _on_android_permissions_result(self, permissions, grants):
        grants = [bool(grant) for grant in grants]
        if any(grants):
            if not all(grants):
                print(
                    "Location permission partially granted "
                    "(coarse location only). Continuing with available precision."
                )
            self._start_gps()
            return

        print(f"Location permission denied: {list(zip(permissions, grants))}")
        self._use_last_known_location_or_default("location permission denied")

    def _start_gps(self):
        if kivy_platform != "android":
            print(f"GPS via pyjnius is Android-only (platform={kivy_platform}).")
            self._use_last_known_location_or_default("GPS not available on this platform")
            return

        if autoclass is None:
            print("pyjnius import failed; cannot start Android GPS.")
            self._use_last_known_location_or_default("pyjnius unavailable")
            return

        try:
            if self._location_manager is None:
                self._init_android_location_manager()
            self._start_android_location_updates()
            self._gps_timeout_event = Clock.schedule_once(
                self._gps_timeout_fallback, self.GPS_TIMEOUT
            )
        except Exception as e:
            print("Failed to start GPS:", e)
            self._use_last_known_location_or_default("failed to start GPS")

    def _init_android_location_manager(self):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity
        if activity is None:
            raise RuntimeError("PythonActivity.mActivity is None")

        self._location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
        if self._location_manager is None:
            raise RuntimeError("Could not obtain Android LocationManager")

        app_ref = self

        class AndroidLocationListener(PythonJavaClass):
            __javainterfaces__ = ["android/location/LocationListener"]
            __javacontext__ = "app"

            def __init__(self):
                super().__init__()

            @java_method("(Landroid/location/Location;)V")
            def onLocationChanged(self, location):
                if location is None:
                    return
                lat = float(location.getLatitude())
                lon = float(location.getLongitude())
                provider = str(location.getProvider()) if location.getProvider() else "unknown"
                accuracy = None
                try:
                    accuracy = float(location.getAccuracy())
                except Exception:
                    accuracy = None

                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_location(
                        lat=lat,
                        lon=lon,
                        accuracy=accuracy,
                        provider=provider,
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;)V")
            def onProviderDisabled(self, provider):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "provider", f"{provider_name} disabled"
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;)V")
            def onProviderEnabled(self, provider):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "provider", f"{provider_name} enabled"
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
            def onStatusChanged(self, provider, status, extras):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "status", f"{provider_name} status={status}"
                    ),
                    0,
                )

        # Keep strong reference to avoid GC while Java still calls into Python.
        self._location_listener = AndroidLocationListener()

    def _enabled_android_providers(self) -> list[str]:
        LocationManager = autoclass("android.location.LocationManager")
        providers: list[str] = []
        for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
            try:
                if self._location_manager.isProviderEnabled(provider):
                    providers.append(provider)
            except Exception as e:
                print(f"Could not query provider '{provider}': {e}")
        return providers

    def _start_android_location_updates(self):
        Looper = autoclass("android.os.Looper")
        providers = self._enabled_android_providers()
        if not providers:
            raise RuntimeError("No enabled Android location providers (GPS/NETWORK)")

        print(f"Starting Android location updates via providers: {providers}")
        for provider in providers:
            self._location_manager.requestLocationUpdates(
                provider,
                1000,
                0.0,
                self._location_listener,
                Looper.getMainLooper(),
            )

        self._emit_android_last_known_location(providers)

    def _emit_android_last_known_location(self, providers: list[str]):
        for provider in providers:
            try:
                last = self._location_manager.getLastKnownLocation(provider)
            except Exception as e:
                print(f"Could not read last known location for provider '{provider}': {e}")
                continue

            if last is None:
                continue

            try:
                lat = float(last.getLatitude())
                lon = float(last.getLongitude())
            except Exception as e:
                print(f"Invalid last known location from provider '{provider}': {e}")
                continue

            accuracy = None
            try:
                accuracy = float(last.getAccuracy())
            except Exception:
                accuracy = None

            print(
                "Using Android last known location from provider "
                f"'{provider}': lat={lat:.6f}, lon={lon:.6f}, accuracy={accuracy}"
            )
            self.on_gps_location(lat=lat, lon=lon, accuracy=accuracy, provider=provider)
            return

    def _gps_timeout_fallback(self, _dt):
        # If no fix arrives in time, use last successful GPS or default.
        self._gps_timeout_event = None
        if self.current_lat is None or self.current_lon is None:
            print(
                f"GPS timeout after {self.GPS_TIMEOUT}s with no fix. "
                "Falling back to last known location."
            )
            self._use_last_known_location_or_default("GPS timeout")

    def _use_fallback_location(self):
        """Use default coordinates when GPS is unavailable."""
        print("Using default fallback coordinates: lat=51.5074, lon=-0.1278 (London)")
        self._set_location_labels(self._format_location_label("Standort wird geladen...", False))
        self._apply_location(51.5074, -0.1278)

    def _last_location_cache_path(self) -> Path:
        return Path(self.user_data_dir) / "last_location.json"

    def _load_last_known_location(self):
        path = self._last_location_cache_path()
        if not path.exists():
            return

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            lat = float(payload["lat"])
            lon = float(payload["lon"])
            label = payload.get("label")
        except Exception as e:
            print(f"Failed to load last known location cache: {e}")
            return

        self.last_gps_lat = lat
        self.last_gps_lon = lon
        if isinstance(label, str) and label.strip():
            self.last_location_label = label.strip()
            self._set_location_labels(self.last_location_label)

        print(f"Loaded last known location: {lat}, {lon}")

    def _save_last_known_location(self, lat: float, lon: float, label: str | None = None):
        self.last_gps_lat = lat
        self.last_gps_lon = lon
        if label:
            self.last_location_label = label

        payload = {"lat": lat, "lon": lon}
        if self.last_location_label:
            payload["label"] = self.last_location_label

        try:
            path = self._last_location_cache_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload), encoding="utf-8")
        except Exception as e:
            print(f"Failed to store last known location cache: {e}")

    def _use_last_known_location_or_default(self, reason: str):
        if self.last_gps_lat is not None and self.last_gps_lon is not None:
            print(
                f"No live GPS fix ({reason}), using last successful GPS location: "
                f"{self.last_gps_lat}, {self.last_gps_lon}"
            )
            if self.last_location_label:
                self._set_location_labels(self.last_location_label)
            self._apply_location(self.last_gps_lat, self.last_gps_lon)
            return

        print(f"No live GPS fix ({reason}) and no cached GPS location; using default.")
        self._use_fallback_location()

    def on_gps_status(self, stype, status):
        print(f"GPS status: type={stype}, status={status}")
        status_text = str(status).lower()
        degraded = ("disabled", "out of service", "unavailable", "denied")
        if any(marker in status_text for marker in degraded):
            self._use_last_known_location_or_default(f"GPS status: {status}")

    def on_gps_location(self, **kwargs):
        # Cancel timeout once GPS callback responds.
        if self._gps_timeout_event:
            self._gps_timeout_event.cancel()
            self._gps_timeout_event = None

        lat = kwargs.get("lat")
        lon = kwargs.get("lon")
        if lat is None or lon is None:
            print(f"Ignoring GPS update without coordinates: {kwargs}")
            self._use_last_known_location_or_default("GPS update without coordinates")
            return

        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            print(f"Ignoring invalid GPS coordinates: lat={lat}, lon={lon}")
            self._use_last_known_location_or_default("invalid GPS coordinates")
            return

        if not self._coordinates_in_range(lat, lon):
            print(f"Ignoring out-of-range GPS coordinates: lat={lat}, lon={lon}")
            self._use_last_known_location_or_default("out-of-range GPS coordinates")
            return

        accuracy = kwargs.get("accuracy")
        if accuracy is not None:
            print(f"GPS parsed coordinates: lat={lat:.6f}, lon={lon:.6f}, accuracy={accuracy}")
        else:
            print(f"GPS parsed coordinates: lat={lat:.6f}, lon={lon:.6f}")

        print("GPS location:", kwargs)
        is_first_live_fix = not self._has_live_gps_fix
        self._has_live_gps_fix = True
        self._set_location_labels("GPS erkannt, Standort wird geladen...")
        self._apply_location(
            lat,
            lon,
            track_as_gps=True,
            force_refresh=is_first_live_fix,
        )

    def _coordinates_in_range(self, lat: float, lon: float) -> bool:
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    def _format_location_label(self, label: str, is_live_gps: bool) -> str:
        if not self.SHOW_LOCATION_SOURCE_PREFIX:
            return label
        source = "GPS" if is_live_gps else "Fallback"
        return f"{source}: {label}"

    def _should_refresh_weather(self) -> bool:
        now = time.monotonic()
        if now - self._last_weather_refresh_ts < self.WEATHER_REFRESH_INTERVAL:
            return False
        self._last_weather_refresh_ts = now
        return True

    def _apply_location(
        self,
        lat: float,
        lon: float,
        force_refresh: bool = False,
        track_as_gps: bool = False,
    ):
        source = "live GPS" if track_as_gps else "fallback/cached location"
        print(
            f"Applying {source}: lat={lat:.6f}, lon={lon:.6f}, "
            f"force_refresh={force_refresh}"
        )
        self.current_lat = lat
        self.current_lon = lon
        if track_as_gps:
            # Persist successful GPS coordinate acquisition independently from API success.
            self._save_last_known_location(lat, lon)

        if not force_refresh and not self._should_refresh_weather():
            print(
                "Skipping weather refresh due to interval throttle "
                f"({self.WEATHER_REFRESH_INTERVAL}s)."
            )
            return

        try:
            data = weather_service.get_weather(lat=lat, lon=lon)
            self._log_location_roundtrip(lat, lon, data)
            print(json.dumps(data, indent=2))
            location_label = self._update_location_labels_from_weather(
                data,
                track_as_gps=track_as_gps,
            )
            if track_as_gps:
                self._save_last_known_location(lat, lon, label=location_label)
            self._update_weather_display(data)
            self._refresh_forecast_screen()
        except Exception as e:
            print("Error fetching weather with coordinates:", e)
            if self.last_location_label:
                self._set_location_labels(self.last_location_label)
            else:
                self._set_location_labels(self._location_label_from_error(e, track_as_gps))

    def _log_location_roundtrip(self, requested_lat: float, requested_lon: float, weather_data: dict):
        if not isinstance(weather_data, dict):
            return

        city = weather_data.get("city", {})
        if not isinstance(city, dict):
            return

        coord = city.get("coord", {})
        if not isinstance(coord, dict):
            return

        api_lat = coord.get("lat")
        api_lon = coord.get("lon")
        if api_lat is None or api_lon is None:
            return

        try:
            api_lat = float(api_lat)
            api_lon = float(api_lon)
        except (TypeError, ValueError):
            return

        delta_lat = abs(api_lat - requested_lat)
        delta_lon = abs(api_lon - requested_lon)
        city_name = city.get("name")
        country = city.get("country")
        city_label = (
            f"{city_name}, {country}" if city_name and country else city_name or "unknown"
        )

        print(
            "[location-check] requested="
            f"({requested_lat:.6f}, {requested_lon:.6f}), "
            f"api_city={city_label}, "
            f"api_coord=({api_lat:.6f}, {api_lon:.6f}), "
            f"delta=({delta_lat:.4f}, {delta_lon:.4f})"
        )
        if delta_lat > 1.0 or delta_lon > 1.0:
            print(
                "[location-check] Significant difference between requested coordinates "
                "and API city coordinates."
            )

    def _location_label_from_error(self, error: Exception, track_as_gps: bool) -> str:
        # Map frequent backend failures to user-visible hints.
        if isinstance(error, weather_service.EnvNotFoundError):
            return "Standortname nicht verfuegbar (.env fehlt)"
        if isinstance(error, weather_service.MissingAPIConfigError):
            return "Standortname nicht verfuegbar (API Konfig fehlt)"
        if isinstance(error, weather_service.APITokenExpiredError):
            return "Standortname nicht verfuegbar (API Key ungueltig)"
        if isinstance(error, weather_service.NetworkError):
            return "Standortname nicht verfuegbar (kein Internet)"
        if isinstance(error, weather_service.ServiceUnavailableError):
            return "Standortname nicht verfuegbar (Wetterdienst down)"
        if isinstance(error, weather_service.APIRequestError):
            return "Standortname nicht verfuegbar (API Anfragefehler)"
        if track_as_gps:
            return "GPS erkannt, Standortname nicht verfuegbar"
        return "Standort nicht verfuegbar"

    def _set_location_labels(self, label: str):
        if not self.root or "sm" not in self.root.ids:
            return

        sm = self.root.ids.sm
        for screen_name in ("today", "tomorrow"):
            if sm.has_screen(screen_name):
                screen = sm.get_screen(screen_name)
                if hasattr(screen, "location_text"):
                    screen.location_text = label

    def _update_location_labels_from_weather(
        self,
        weather_data: dict,
        track_as_gps: bool = False,
    ) -> str | None:
        label = self._extract_location_label(weather_data)
        if not label:
            fallback_label = self._format_location_label(
                "Standort nicht verfuegbar",
                is_live_gps=track_as_gps,
            )
            self._set_location_labels(fallback_label)
            return None

        display_label = self._format_location_label(label, is_live_gps=track_as_gps)
        self._set_location_labels(display_label)
        return display_label

    def _extract_location_label(self, weather_data: dict) -> str | None:
        city = weather_data.get("city", {}).get("name")
        country = weather_data.get("city", {}).get("country")

        # Fallback for current-weather style payloads (non-forecast).
        if not city:
            city = weather_data.get("name")
            country = weather_data.get("sys", {}).get("country")

        if city and country:
            return f"{city}, {country}"
        if city:
            return city
        return None

    def _refresh_forecast_screen(self):
        if not self.root or "sm" not in self.root.ids:
            return

        sm = self.root.ids.sm
        if not sm.has_screen("five_days"):
            return

        screen = sm.get_screen("five_days")
        if hasattr(screen, "_load_forecast_data"):
            Clock.schedule_once(lambda _dt: screen._load_forecast_data(), 0)

    def _update_weather_display(self, weather_data):
        """Update the UI with weather data from the API response."""
        try:
            if weather_data and "list" in weather_data and len(weather_data["list"]) > 0:
                current_forecast = weather_data["list"][0]

                temp_kelvin = current_forecast.get("main", {}).get("temp")
                if temp_kelvin is not None:
                    temp_celsius = round(temp_kelvin - 273.15)

                    today_screen = self.root.ids.sm.get_screen("today")
                    today_screen.temp_text = f"{temp_celsius}\u00b0C"

                    condition = current_forecast.get("weather", [{}])[0].get(
                        "main", "Unknown"
                    )
                    today_screen.condition_text = condition

                    humidity = current_forecast.get("main", {}).get("humidity")
                    if humidity is not None:
                        today_screen.humidity_text = f"{humidity}%"

                    wind_speed = current_forecast.get("wind", {}).get("speed")
                    if wind_speed is not None:
                        today_screen.wind_text = f"{wind_speed} m/s"

                    print(f"Weather display updated: {temp_celsius}\u00b0C, {condition}")
        except Exception as e:
            print(f"Error updating weather display: {e}")

    def on_stop(self):
        try:
            if kivy_platform == "android" and self._location_manager and self._location_listener:
                self._location_manager.removeUpdates(self._location_listener)
                print("Stopped Android location updates.")
        except Exception:
            pass

    def navigate(self, key: str):
        self.root.navigate(key)


if __name__ == "__main__":
    # Print current weather JSON once when running as a script, then start the app.
    def print_weather_json():
        """Call the weather service and print the returned JSON."""
        try:
            data = weather_service.get_weather()
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("Error fetching weather:", e)

    print_weather_json()
    WeatherApp().run()
