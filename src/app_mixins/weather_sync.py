import time

from kivy.clock import Clock

import services.weather_service as weather_service


class WeatherSyncMixin:
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
            #print(json.dumps(data, indent=2))
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

    def _log_location_roundtrip(
        self,
        requested_lat: float,
        requested_lon: float,
        weather_data: dict,
    ):
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
        city_info = weather_data.get("city", {}) if isinstance(weather_data, dict) else {}
        if not isinstance(city_info, dict):
            city_info = {}

        city = city_info.get("name")
        country = city_info.get("country")

        if not city and isinstance(weather_data, dict):
            city = weather_data.get("name")
            sys_info = weather_data.get("sys", {})
            if isinstance(sys_info, dict):
                country = sys_info.get("country")

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
        try:
            if not weather_data or "list" not in weather_data or not weather_data["list"]:
                return
            if not self.root or "sm" not in self.root.ids:
                return

            current_forecast = weather_data["list"][0]
            temp_kelvin = current_forecast.get("main", {}).get("temp")
            if temp_kelvin is None:
                return

            temp_celsius = round(temp_kelvin - 273.15)
            today_screen = self.root.ids.sm.get_screen("today")
            today_screen.temp_text = f"{temp_celsius}\u00b0C"

            condition = current_forecast.get("weather", [{}])[0].get("main", "Unknown")
            today_screen.condition_text = condition
            
            # Update current weather icon
            icon_code = current_forecast.get("weather", [{}])[0].get("icon", "01d")
            today_screen.weather_icon = f"icons/{icon_code}.png"

            # The detailed hourly forecast (3-hour entries) is passed to the
            # Today screen so it can populate the horizontal hourly scroller.
            try:
                if isinstance(weather_data, dict) and "list" in weather_data:
                    today_screen.set_hourly_data(weather_data.get("list", []))
            except Exception as e:
                print(f"Error setting hourly data on TodayScreen: {e}")

            # Update Tomorrow Screen
            try:
                tomorrow_screen = self.root.ids.sm.get_screen("tomorrow")
                
                # Get current date from first entry
                current_date_str = current_forecast.get("dt_txt", "").split()[0]
                
                # Find entries for tomorrow (next day)
                tomorrow_entries = []
                if current_date_str:
                    from datetime import datetime, timedelta
                    current_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
                    tomorrow_date = (current_date + timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    for entry in weather_data.get("list", []):
                        entry_date_str = entry.get("dt_txt", "").split()[0]
                        if entry_date_str == tomorrow_date:
                            tomorrow_entries.append(entry)
                
                # Calculate min and max temp for tomorrow
                if tomorrow_entries:
                    temps = [e.get("main", {}).get("temp") for e in tomorrow_entries if e.get("main", {}).get("temp") is not None]
                    if temps:
                        min_temp = round(min(temps) - 273.15)
                        max_temp = round(max(temps) - 273.15)
                        tomorrow_screen.minmax_text = f"{min_temp}° / {max_temp}°"
                    
                    # Get weather icon and condition from first tomorrow entry
                    first_tomorrow = tomorrow_entries[0]
                    tomorrow_icon = first_tomorrow.get("weather", [{}])[0].get("icon", "01d")
                    tomorrow_condition = first_tomorrow.get("weather", [{}])[0].get("main", "Unknown")
                    
                    tomorrow_screen.weather_icon = f"icons/{tomorrow_icon}.png"
                    tomorrow_screen.condition_text = tomorrow_condition
                    
                    # Set hourly data for tomorrow
                    tomorrow_screen.set_hourly_data(tomorrow_entries)
                
            except Exception as e:
                print(f"Error updating TomorrowScreen: {e}")

            print(f"Weather display updated: {temp_celsius}\u00b0C, {condition}")
        except Exception as e:
            print(f"Error updating weather display: {e}")
