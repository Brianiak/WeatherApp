from pathlib import Path
import json
import time

from plyer import gps  # python -m pip install plyer requests

from kivy.app import App
from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform as kivy_platform

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
    _last_weather_refresh_ts = 0.0
    current_lat = None
    current_lon = None
    last_gps_lat = None
    last_gps_lon = None
    last_location_label = None

    def on_start(self):
        self._load_last_known_location()

        # Use native GPS only on mobile devices.
        if kivy_platform == "android":
            self._start_android_location_flow()
        elif kivy_platform == "ios":
            self._start_gps()
        else:
            print(
                f"Platform '{kivy_platform}' has no Plyer GPS; using simulated coordinates."
            )
            self._use_last_known_location_or_default(
                "platform without native GPS support"
            )

    def _start_android_location_flow(self):
        try:
            from android.permissions import Permission, check_permission, request_permissions

            required = [Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION]
            if all(check_permission(permission) for permission in required):
                self._start_gps()
                return

            request_permissions(required, self._on_android_permissions_result)
        except Exception as e:
            print("Android permission flow failed:", e)
            self._use_last_known_location_or_default("android permission flow failed")

    def _on_android_permissions_result(self, permissions, grants):
        if all(grants):
            self._start_gps()
            return

        print(f"Location permission denied: {list(zip(permissions, grants))}")
        self._use_last_known_location_or_default("location permission denied")

    def _start_gps(self):
        try:
            gps.configure(on_location=self.on_gps_location, on_status=self.on_gps_status)
            # Request frequent updates to move away from stale last-known data quickly.
            gps.start(minTime=1000, minDistance=0)
            self._gps_timeout_event = Clock.schedule_once(
                self._gps_timeout_fallback, self.GPS_TIMEOUT
            )
        except NotImplementedError:
            print("Plyer GPS not implemented on this platform.")
            self._use_last_known_location_or_default("plyer GPS not implemented")
        except Exception as e:
            print("Failed to start GPS:", e)
            self._use_last_known_location_or_default("failed to start GPS")

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

        print("GPS location:", kwargs)
        self._set_location_labels("GPS erkannt, Standort wird geladen...")
        self._apply_location(lat, lon, track_as_gps=True)

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
        self.current_lat = lat
        self.current_lon = lon
        if track_as_gps:
            # Persist successful GPS coordinate acquisition independently from API success.
            self._save_last_known_location(lat, lon)

        if not force_refresh and not self._should_refresh_weather():
            return

        try:
            data = weather_service.get_weather(lat=lat, lon=lon)
            print(json.dumps(data, indent=2))
            location_label = self._update_location_labels_from_weather(data)
            if track_as_gps:
                self._save_last_known_location(lat, lon, label=location_label)
            self._update_weather_display(data)
            self._refresh_forecast_screen()
        except Exception as e:
            print("Error fetching weather with coordinates:", e)
            if self.last_location_label:
                self._set_location_labels(self.last_location_label)
            elif track_as_gps:
                self._set_location_labels("GPS erkannt, Standortname nicht verfuegbar")
            else:
                self._set_location_labels("Standort nicht verfuegbar")

    def _set_location_labels(self, label: str):
        if not self.root or "sm" not in self.root.ids:
            return

        sm = self.root.ids.sm
        for screen_name in ("today", "tomorrow"):
            if sm.has_screen(screen_name):
                screen = sm.get_screen(screen_name)
                if hasattr(screen, "location_text"):
                    screen.location_text = label

    def _update_location_labels_from_weather(self, weather_data: dict) -> str | None:
        label = self._extract_location_label(weather_data)
        if not label:
            label = "Standort nicht verfuegbar"
            self._set_location_labels(label)
            return None

        self._set_location_labels(label)
        return label

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
            if kivy_platform in ("android", "ios"):
                gps.stop()
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
