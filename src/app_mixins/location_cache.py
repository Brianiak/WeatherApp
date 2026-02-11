import json
from pathlib import Path


class LocationCacheMixin:
    def _use_fallback_location(self):
        print("Using default fallback coordinates: lat=51.5074, lon=-0.1278 (London)")
        self._set_location_labels(
            self._format_location_label("Standort wird geladen...", False)
        )
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

    def _coordinates_in_range(self, lat: float, lon: float) -> bool:
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    def _format_location_label(self, label: str, is_live_gps: bool) -> str:
        if not self.SHOW_LOCATION_SOURCE_PREFIX:
            return label
        source = "GPS" if is_live_gps else "Fallback"
        return f"{source}: {label}"

    def _set_location_labels(self, label: str):
        if not self.root or "sm" not in self.root.ids:
            return

        sm = self.root.ids.sm
        for screen_name in ("today", "tomorrow"):
            if sm.has_screen(screen_name):
                screen = sm.get_screen(screen_name)
                if hasattr(screen, "location_text"):
                    screen.location_text = label
