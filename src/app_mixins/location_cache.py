import json
from pathlib import Path


class LocationCacheMixin:
    """Mixin providing location caching and fallback location functionality.
    
    Handles saving and loading the last known GPS location to disk cache,
    providing fallback coordinates when GPS is unavailable, and formatting
    location labels for UI display.
    """
    
    def _use_fallback_location(self):
        """Use hardcoded fallback coordinates and apply them.
        
        Uses London coordinates (51.5074, -0.1278) as a fallback when
        no GPS fix is available and no cached location exists.
        """
        print("Using default fallback coordinates: lat=51.5074, lon=-0.1278 (London)")
        self._set_location_labels(
            self._format_location_label("Standort wird geladen...", False)
        )
        self._apply_location(51.5074, -0.1278)

    def _last_location_cache_path(self) -> Path:
        """Get the filesystem path to the location cache file.
        
        Returns:
            Path: Path to last_location.json in the user data directory
        """
        return Path(self.user_data_dir) / "last_location.json"

    def _load_last_known_location(self):
        """Load the last known location from disk cache.
        
        Reads the cached location JSON file and restores the coordinates
        and location label. If loading fails, silently returns without error.
        """
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
        """Save the current location to disk cache.
        
        Saves coordinates and optional location label to a JSON file in the
        user data directory for persistence across app sessions.
        
        Args:
            lat (float): Latitude coordinate to save
            lon (float): Longitude coordinate to save
            label (str | None): Optional location label (city, country)
        """
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
        """Apply last cached location or fallback to default coordinates.
        
        Attempts to use the previously saved GPS location. If no cached
        location exists, falls back to hardcoded default coordinates.
        
        Args:
            reason (str): The reason why this fallback was triggered
        """
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
        """Validate that coordinates are within valid geographic ranges.
        
        Args:
            lat (float): Latitude to validate (-90 to 90)
            lon (float): Longitude to validate (-180 to 180)
            
        Returns:
            bool: True if coordinates are valid, False otherwise
        """
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    def _format_location_label(self, label: str, is_live_gps: bool) -> str:
        """Format a location label for display, optionally with source prefix.
        
        Optionally prepends "GPS:" or "Fallback:" prefix based on the location source.
        Controlled by the SHOW_LOCATION_SOURCE_PREFIX class attribute.
        
        Args:
            label (str): The base location label
            is_live_gps (bool): Whether this is from live GPS or fallback
            
        Returns:
            str: The formatted location label for display
        """
        if not self.SHOW_LOCATION_SOURCE_PREFIX:
            return label
        source = "GPS" if is_live_gps else "Fallback"
        return f"{source}: {label}"

    def _set_location_labels(self, label: str):
        """Update location text on all weather screens.
        
        Sets the location_text property on Today and Tomorrow screens
        to display the provided location label.
        
        Args:
            label (str): The location label to display
        """
        if not self.root or "sm" not in self.root.ids:
            return

        sm = self.root.ids.sm
        for screen_name in ("today", "tomorrow"):
            if sm.has_screen(screen_name):
                screen = sm.get_screen(screen_name)
                if hasattr(screen, "location_text"):
                    screen.location_text = label
