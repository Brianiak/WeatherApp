from types import SimpleNamespace
from unittest.mock import patch

import services.weather_service as weather_service
from app_mixins.weather_sync import WeatherSyncMixin


class AttrDict(dict):
    __getattr__ = dict.__getitem__


class DummyTodayScreen:
    def __init__(self):
        self.temp_text = ""
        self.condition_text = ""
        self.weather_icon = ""
        self.location_icon_source = ""
        self.hourly_calls = []

    def set_hourly_data(self, entries):
        self.hourly_calls.append(entries)


class DummyTomorrowScreen:
    def __init__(self):
        self.condition_text = ""
        self.minmax_text = ""
        self.dayparts_text = ""
        self.weather_icon = ""
        self.location_icon_source = ""
        self.hourly_calls = []

    def set_hourly_data(self, entries):
        self.hourly_calls.append(entries)


class DummyFiveDaysScreen:
    def __init__(self):
        self.load_calls = 0

    def _load_forecast_data(self):
        self.load_calls += 1


class DummyScreenManager:
    def __init__(self):
        self._screens = {
            "today": DummyTodayScreen(),
            "tomorrow": DummyTomorrowScreen(),
            "five_days": DummyFiveDaysScreen(),
        }

    def has_screen(self, name):
        return name in self._screens

    def get_screen(self, name):
        return self._screens[name]


class DummyWeatherSyncApp(WeatherSyncMixin):
    WEATHER_REFRESH_INTERVAL = 60

    def __init__(self):
        self._last_weather_refresh_ts = 0.0
        self.current_lat = None
        self.current_lon = None
        self.last_location_label = None
        self._weather_from_cache = False
        self.saved_locations = []
        self.labels = []
        self.root = SimpleNamespace(ids=AttrDict(sm=DummyScreenManager()))

    def _save_last_known_location(self, lat, lon, label=None):
        self.saved_locations.append((lat, lon, label))
        if label:
            self.last_location_label = label

    def _set_location_labels(self, label):
        self.labels.append(label)

    def _format_location_label(self, label, is_live_gps):
        return f"GPS: {label}" if is_live_gps else label


def _sample_weather_payload():
    return {
        "city": {
            "name": "Berlin",
            "country": "DE",
            "coord": {"lat": 52.52, "lon": 13.40},
        },
        "list": [
            {
                "dt_txt": "2026-02-10 09:00:00",
                "main": {"temp": 280},
                "weather": [{"main": "Clouds", "icon": "02d"}],
            },
            {
                "dt_txt": "2026-02-10 12:00:00",
                "main": {"temp": 281},
                "weather": [{"main": "Clouds", "icon": "02d"}],
            },
            {
                "dt_txt": "2026-02-11 06:00:00",
                "main": {"temp": 285},
                "weather": [{"main": "Rain", "icon": "10d"}],
            },
            {
                "dt_txt": "2026-02-11 12:00:00",
                "main": {"temp": 290},
                "weather": [{"main": "Rain", "icon": "10d"}],
            },
        ],
    }


class TestWeatherSyncMixin:
    def test_should_refresh_weather_honors_interval(self):
        app = DummyWeatherSyncApp()

        with patch("app_mixins.weather_sync.time.monotonic", side_effect=[100.0, 120.0, 205.0]):
            assert app._should_refresh_weather() is True
            assert app._should_refresh_weather() is False
            assert app._should_refresh_weather() is True

    def test_apply_location_skips_refresh_when_throttled(self):
        app = DummyWeatherSyncApp()

        with patch.object(app, "_should_refresh_weather", return_value=False):
            with patch("app_mixins.weather_sync.weather_service.get_weather") as get_weather:
                app._apply_location(48.5, 7.9, force_refresh=False, track_as_gps=False)

        assert app.current_lat == 48.5
        assert app.current_lon == 7.9
        get_weather.assert_not_called()

    def test_apply_location_success_path_updates_state_and_calls_hooks(self):
        app = DummyWeatherSyncApp()
        payload = _sample_weather_payload()

        with patch("app_mixins.weather_sync.weather_service.get_weather", return_value=payload):
            with patch.object(app, "_log_location_roundtrip") as log_roundtrip:
                with patch.object(
                    app, "_update_location_labels_from_weather", return_value="Berlin, DE"
                ) as update_labels:
                    with patch.object(app, "_update_weather_display") as update_display:
                        with patch.object(app, "_refresh_forecast_screen") as refresh_forecast:
                            app._apply_location(
                                48.5,
                                7.9,
                                force_refresh=True,
                                track_as_gps=True,
                            )

        assert app.current_lat == 48.5
        assert app.current_lon == 7.9
        assert app.saved_locations[0] == (48.5, 7.9, None)
        assert app.saved_locations[1] == (48.5, 7.9, "Berlin, DE")
        assert app._weather_from_cache is False
        log_roundtrip.assert_called_once()
        update_labels.assert_called_once()
        update_display.assert_called_once()
        refresh_forecast.assert_called_once()

    def test_apply_location_error_uses_last_location_label_when_available(self):
        app = DummyWeatherSyncApp()
        app.last_location_label = "Hamburg, DE"

        with patch(
            "app_mixins.weather_sync.weather_service.get_weather",
            side_effect=weather_service.NetworkError("offline"),
        ):
            app._apply_location(50.0, 8.0, force_refresh=True)

        assert app._weather_from_cache is True
        assert app.labels[-1] == "Hamburg, DE"

    def test_apply_location_error_uses_generated_error_label_when_no_last_label(self):
        app = DummyWeatherSyncApp()
        app.last_location_label = None

        with patch(
            "app_mixins.weather_sync.weather_service.get_weather",
            side_effect=weather_service.APITokenExpiredError("bad token"),
        ):
            app._apply_location(50.0, 8.0, force_refresh=True, track_as_gps=True)

        assert app._weather_from_cache is True
        assert "API Key ungueltig" in app.labels[-1]

    def test_location_label_from_error_variants(self):
        app = DummyWeatherSyncApp()
        cases = [
            (weather_service.EnvNotFoundError("x"), ".env fehlt"),
            (weather_service.MissingAPIConfigError("x"), "API Konfig fehlt"),
            (weather_service.APITokenExpiredError("x"), "API Key ungueltig"),
            (weather_service.NetworkError("x"), "kein Internet"),
            (weather_service.ServiceUnavailableError("x"), "Wetterdienst down"),
            (weather_service.APIRequestError("x"), "API Anfragefehler"),
            (RuntimeError("x"), "Standort nicht verfuegbar"),
        ]

        for error, expected in cases:
            assert expected in app._location_label_from_error(error, track_as_gps=False)

        assert "GPS erkannt" in app._location_label_from_error(RuntimeError("x"), track_as_gps=True)

    def test_extract_location_label_from_city_object_and_top_level_fallback(self):
        app = DummyWeatherSyncApp()

        assert app._extract_location_label({"city": {"name": "Berlin", "country": "DE"}}) == "Berlin, DE"
        assert app._extract_location_label({"city": {"name": "Berlin"}}) == "Berlin"
        assert app._extract_location_label({"name": "Paris", "sys": {"country": "FR"}}) == "Paris, FR"
        assert app._extract_location_label({"city": "invalid"}) is None

    def test_update_location_labels_from_weather_with_valid_city(self):
        app = DummyWeatherSyncApp()

        label = app._update_location_labels_from_weather(
            {"city": {"name": "Berlin", "country": "DE"}},
            track_as_gps=True,
        )

        assert label == "GPS: Berlin, DE"
        assert app.labels[-1] == "GPS: Berlin, DE"

    def test_update_location_labels_from_weather_without_city_uses_fallback(self):
        app = DummyWeatherSyncApp()

        label = app._update_location_labels_from_weather({}, track_as_gps=False)

        assert label is None
        assert app.labels[-1] == "Standort nicht verfuegbar"

    def test_log_location_roundtrip_handles_missing_shapes(self):
        app = DummyWeatherSyncApp()
        app._log_location_roundtrip(48.5, 7.9, None)
        app._log_location_roundtrip(48.5, 7.9, {"city": "invalid"})
        app._log_location_roundtrip(48.5, 7.9, {"city": {"coord": "invalid"}})
        app._log_location_roundtrip(48.5, 7.9, {"city": {"coord": {"lat": "x", "lon": "y"}}})

    def test_refresh_forecast_screen_schedules_reload_when_screen_exists(self):
        app = DummyWeatherSyncApp()
        five_days_screen = app.root.ids.sm.get_screen("five_days")

        with patch(
            "app_mixins.weather_sync.Clock.schedule_once",
            side_effect=lambda cb, _delay: cb(0),
        ) as schedule_once:
            app._refresh_forecast_screen()

        schedule_once.assert_called_once()
        assert five_days_screen.load_calls == 1

    def test_refresh_forecast_screen_returns_early_without_root(self):
        app = DummyWeatherSyncApp()
        app.root = None
        app._refresh_forecast_screen()

    def test_update_weather_display_returns_early_for_missing_payload(self):
        app = DummyWeatherSyncApp()
        app._update_weather_display({})
        app._update_weather_display({"list": []})

    def test_update_weather_display_updates_today_and_tomorrow_screens(self):
        app = DummyWeatherSyncApp()
        payload = _sample_weather_payload()

        app._weather_from_cache = False
        app._update_weather_display(payload)

        today = app.root.ids.sm.get_screen("today")
        tomorrow = app.root.ids.sm.get_screen("tomorrow")

        assert today.temp_text.endswith("°C")
        assert today.condition_text == "Clouds"
        assert today.weather_icon == "icons/02d.png"
        assert today.location_icon_source == "icons/location.png"
        assert len(today.hourly_calls) == 1
        assert len(today.hourly_calls[0]) == len(payload["list"])

        assert "/" in tomorrow.minmax_text
        assert tomorrow.condition_text == "Rain"
        assert tomorrow.weather_icon == "icons/10d.png"
        assert tomorrow.location_icon_source == "icons/location.png"
        assert len(tomorrow.hourly_calls) == 1
        assert len(tomorrow.hourly_calls[0]) == 2

    def test_update_weather_display_uses_no_location_icon_when_data_from_cache(self):
        app = DummyWeatherSyncApp()
        payload = _sample_weather_payload()
        app._weather_from_cache = True

        app._update_weather_display(payload)

        today = app.root.ids.sm.get_screen("today")
        tomorrow = app.root.ids.sm.get_screen("tomorrow")
        assert today.location_icon_source == "icons/no_location.png"
        assert tomorrow.location_icon_source == "icons/no_location.png"
