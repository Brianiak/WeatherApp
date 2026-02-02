
from pathlib import Path
from plyer import gps # python -m pip install plyer requests

from kivy.app import App
from kivy.properties import StringProperty
from kivy.resources import resource_add_path
from kivy.uix.boxlayout import BoxLayout
from kivy.utils import platform as kivy_platform

import json

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
    location_text = StringProperty("Houston, US")
    temp_text = StringProperty("13°")
    condition_text = StringProperty("Clouds")
    humidity_text = StringProperty("82%")
    wind_text = StringProperty("6 km/h")


class TomorrowScreen(BaseWeatherScreen):
    location_text = StringProperty("Houston, US")
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

    def on_start(self):
        # Only attempt to use the native GPS implementation on mobile.
        # Plyer's GPS is not implemented on desktop platforms (raises
        # ModuleNotFoundError / NotImplementedError). For desktop/testing
        # fall back to simulated coordinates.
        if kivy_platform in ("android", "ios"):
            try:
                gps.configure(on_location=self.on_gps_location)
                gps.start()
            except NotImplementedError:
                print("Plyer GPS not implemented on this platform.")
            except Exception as e:
                print("Failed to start GPS:", e)
        else:
            print(f"Platform '{kivy_platform}' has no Plyer GPS; using simulated coordinates.")
            # Call the GPS handler with a reasonable default location (for testing).
            # You can replace these with any coordinates you want to test with.
            self.on_gps_location(lat=48.48, lon=7.93)
    
    def on_gps_location(self, **kwargs):
        # Extract coordinates provided by Plyer GPS and request weather.
        lat = kwargs.get("lat")
        lon = kwargs.get("lon")
        print("GPS location:", kwargs)

        # Call weather service with the received coordinates and print JSON.
        try:
            data = weather_service.get_weather(lat=lat, lon=lon)
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("Error fetching weather with GPS coordinates:", e)

    def navigate(self, key: str):
        self.root.navigate(key)


if __name__ == "__main__":
    # Print current weather JSON once when running as a script, then start the app.
    def print_weather_json():
        """Call the weather service and print the returned JSON.

        Uses the public `get_weather()` function from `weather_service`.
        Errors are caught and printed so they don't prevent the GUI from starting.
        """
        try:
            # Prefer direct import; fall back to package-style if needed.
            data = weather_service.get_weather()
            print(json.dumps(data, indent=2))
        except Exception as e:
            print("Error fetching weather:", e)

    print_weather_json()
    WeatherApp().run()
