from pathlib import Path
import json

from kivy.app import App
from kivy.resources import resource_add_path
from kivy.utils import platform as kivy_platform

import services.weather_service as weather_service
from app_mixins.android_location import AndroidLocationMixin
from app_mixins.location_cache import LocationCacheMixin
from app_mixins.weather_sync import WeatherSyncMixin
from screens.five_days_screen import FiveDaysScreen  # noqa: F401
from screens.today_screen import TodayScreen  # noqa: F401
from screens.tomorrow_screen import TomorrowScreen  # noqa: F401
from ui.forecast_row import ForecastRow  # noqa: F401
from ui.weather_root import WeatherRoot  # noqa: F401

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KV_PATH = Path(__file__).with_name("weather.kv")

for resource_dir in (PROJECT_ROOT, KV_PATH.parent):
    resource_add_path(str(resource_dir))


class WeatherApp(AndroidLocationMixin, LocationCacheMixin, WeatherSyncMixin, App):
    """Main application class combining GPS location and weather data features.
    
    Integrates Android GPS location handling, location caching, and weather
    synchronization to provide a comprehensive weather application with the
    OpenWeatherMap API backend.
    """
    
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
        """Initialize the application on startup.
        
        Loads the last cached location and initiates the location flow.
        On Android devices, starts the GPS permission request and location tracking.
        On other platforms, uses fallback coordinates (London).
        """
        self._load_last_known_location()

        if kivy_platform == "android":
            self._start_android_location_flow()
            return

        print(
            f"Platform '{kivy_platform}' has no Android LocationManager backend; "
            "using fallback coordinates."
        )
        self._use_last_known_location_or_default(
            "platform without Android GPS support"
        )

    def navigate(self, key: str):
        """Navigate to a different screen in the application.
        
        Args:
            key (str): Screen identifier. Valid values are:
                - 'today': Today's weather screen
                - 'tomorrow': Tomorrow's weather screen  
                - '5days': 5-day forecast screen
        """
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
