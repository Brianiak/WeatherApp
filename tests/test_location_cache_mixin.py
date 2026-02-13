import json
from pathlib import Path
from types import SimpleNamespace

from app_mixins.location_cache import LocationCacheMixin


class AttrDict(dict):
    __getattr__ = dict.__getitem__


class DummyScreen:
    def __init__(self):
        self.location_text = ""


class DummyScreenManager:
    def __init__(self):
        self._screens = {"today": DummyScreen(), "tomorrow": DummyScreen()}

    def has_screen(self, name):
        return name in self._screens

    def get_screen(self, name):
        return self._screens[name]


class DummyLocationApp(LocationCacheMixin):
    SHOW_LOCATION_SOURCE_PREFIX = False

    def __init__(self, user_data_dir):
        self.user_data_dir = str(user_data_dir)
        self.last_gps_lat = None
        self.last_gps_lon = None
        self.last_location_label = None
        self.root = None
        self.apply_calls = []

    def _apply_location(self, lat, lon):
        self.apply_calls.append((lat, lon))


def _root_with_screen_manager():
    sm = DummyScreenManager()
    root = SimpleNamespace(ids=AttrDict(sm=sm))
    return root, sm


class TestLocationCacheMixin:
    def test_last_location_cache_path_uses_user_data_dir(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        cache_path = app._last_location_cache_path()
        assert cache_path == Path(tmp_path) / "last_location.json"

    def test_coordinates_in_range(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        assert app._coordinates_in_range(0.0, 0.0) is True
        assert app._coordinates_in_range(90.0, 180.0) is True
        assert app._coordinates_in_range(91.0, 0.0) is False
        assert app._coordinates_in_range(0.0, 181.0) is False

    def test_format_location_label_without_and_with_prefix(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        assert app._format_location_label("Berlin, DE", is_live_gps=True) == "Berlin, DE"

        app.SHOW_LOCATION_SOURCE_PREFIX = True
        assert app._format_location_label("Berlin, DE", is_live_gps=True) == "GPS: Berlin, DE"
        assert app._format_location_label("Berlin, DE", is_live_gps=False) == "Fallback: Berlin, DE"

    def test_set_location_labels_updates_today_and_tomorrow_screens(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        root, sm = _root_with_screen_manager()
        app.root = root

        app._set_location_labels("Karlsruhe, DE")

        assert sm.get_screen("today").location_text == "Karlsruhe, DE"
        assert sm.get_screen("tomorrow").location_text == "Karlsruhe, DE"

    def test_set_location_labels_returns_early_without_root(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        # Should not raise.
        app._set_location_labels("Any")

    def test_save_last_known_location_persists_payload(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        app._save_last_known_location(48.5, 7.9, label="Karlsruhe, DE")

        payload = json.loads((tmp_path / "last_location.json").read_text(encoding="utf-8"))
        assert payload["lat"] == 48.5
        assert payload["lon"] == 7.9
        assert payload["label"] == "Karlsruhe, DE"
        assert app.last_gps_lat == 48.5
        assert app.last_gps_lon == 7.9
        assert app.last_location_label == "Karlsruhe, DE"

    def test_load_last_known_location_reads_cache_and_updates_labels(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        root, sm = _root_with_screen_manager()
        app.root = root

        cache_payload = {"lat": 51.2, "lon": 6.7, "label": "Koeln, DE"}
        (tmp_path / "last_location.json").write_text(
            json.dumps(cache_payload),
            encoding="utf-8",
        )

        app._load_last_known_location()

        assert app.last_gps_lat == 51.2
        assert app.last_gps_lon == 6.7
        assert app.last_location_label == "Koeln, DE"
        assert sm.get_screen("today").location_text == "Koeln, DE"

    def test_load_last_known_location_ignores_invalid_json(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        (tmp_path / "last_location.json").write_text("{ invalid json", encoding="utf-8")

        app._load_last_known_location()

        assert app.last_gps_lat is None
        assert app.last_gps_lon is None

    def test_use_last_known_location_or_default_prefers_cached_location(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        app.last_gps_lat = 49.0
        app.last_gps_lon = 8.4
        app.last_location_label = "Mannheim, DE"
        root, sm = _root_with_screen_manager()
        app.root = root

        app._use_last_known_location_or_default("gps timeout")

        assert app.apply_calls == [(49.0, 8.4)]
        assert sm.get_screen("today").location_text == "Mannheim, DE"

    def test_use_last_known_location_or_default_uses_fallback_when_no_cache(self, tmp_path):
        app = DummyLocationApp(tmp_path)
        root, sm = _root_with_screen_manager()
        app.root = root

        app._use_last_known_location_or_default("no gps")

        assert app.apply_calls == [(51.5074, -0.1278)]
        assert "Standort wird geladen" in sm.get_screen("today").location_text
