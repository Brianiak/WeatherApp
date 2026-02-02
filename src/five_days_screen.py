"""
5-Day Weather Forecast Screen Module

This module implements the FiveDaysScreen class which displays a 5-day weather forecast
with daily temperature ranges and hourly breakdowns (morning, midday, evening, night).

The screen is optimized for mobile devices and dynamically adjusts the RecycleView 
height based on available space while maintaining a fixed navigation bar at the top.

Classes:
    FiveDaysScreen: Main screen class for displaying 5-day forecast data

Constants:
    ROW_HEIGHT: Fixed height of each forecast row in dp (density-independent pixels)
"""

from datetime import datetime
from kivy.metrics import dp
from kivy.properties import ListProperty
from kivy.clock import Clock

from base_screen import BaseWeatherScreen
import weather_service

ROW_HEIGHT = dp(66)


class FiveDaysScreen(BaseWeatherScreen):
    """
    Screen displaying a 5-day weather forecast with temperature and condition details.
    
    This screen shows a scrollable list of 5 consecutive days with the following
    information for each day:
    - Date (e.g., "Mo, 22.01.")
    - Weather icon
    - Min/Max temperature
    - Temperature breakdown by time of day (morning, midday, evening, night)
    
    Attributes:
        forecast_items (ListProperty): List of forecast dictionaries containing:
            - date_text: Day and date string
            - icon_source: Path to weather icon image
            - minmax_text: Min/Max temperature display
            - dayparts_text: Temperature breakdown by time of day
    
    The RecycleView height is dynamically calculated to fit available space while
    respecting minimum and maximum constraints.
    """
    
    forecast_items = ListProperty([])

    def on_kv_post(self, base_widget):
        """
        Initialize screen after KV file is processed.
        
        Fetches weather forecast data from the API and populates the forecast_items 
        list with 5 days of weather data. Calculates the optimal RecycleView height 
        based on available space.
        
        Args:
            base_widget: The base widget passed by Kivy during initialization
        """
        super().on_kv_post(base_widget)
        
        # Load forecast data from API
        Clock.schedule_once(lambda dt: self._load_forecast_data(), 0)

    def _load_forecast_data(self):
        """
        Fetch and process 5-day forecast data from the weather API.
        
        Makes an API call to get forecast data, processes it into daily summaries
        with min/max temperatures and time-of-day breakdowns, then updates the
        forecast_items list.
        
        Falls back to hardcoded data if API call fails.
        """
        try:
            # Call the weather API forecast endpoint
            data = weather_service.get_weather()
            
            # Process the forecast data
            self.forecast_items = self._process_forecast_data(data)
            
        except Exception as e:
            print(f"Error loading forecast data: {e}")
            # Fallback to hardcoded data on error
            self._load_fallback_data()
        
        self._update_rv_height()

    def _process_forecast_data(self, data: dict) -> list:
        """
        Process API forecast data into daily summaries.
        
        Args:
            data: API response containing forecast list with 3-hour intervals
            
        Returns:
            List of dictionaries with forecast information for 5 days
        """
        from collections import defaultdict
        
        daily_data = defaultdict(list)
        
        # Group forecast entries by date
        for item in data.get("list", []):
            dt_text = item.get("dt_txt", "")
            if not dt_text:
                continue
            date = dt_text.split()[0]  # Extract date: "2026-02-04"
            daily_data[date].append(item)
        
        # Process first 5 days
        forecast_items = []
        for date in sorted(daily_data.keys())[:5]:
            entries = daily_data[date]
            
            # Calculate min/max temps for the day from all entries
            temps = [entry["main"]["temp"] for entry in entries]
            temp_min = min(temps) - 273.15  # Kelvin to Celsius
            temp_max = max(temps) - 273.15
            
            # Get most representative weather icon (prefer midday)
            midday_idx = len(entries) // 2
            icon_code = entries[midday_idx]["weather"][0]["icon"]
            
            # Format date with German weekday abbreviations
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            weekday_map = {
                "Mon": "Mo", "Tue": "Di", "Wed": "Mi", 
                "Thu": "Do", "Fri": "Fr", "Sat": "Sa", "Sun": "So"
            }
            date_str = date_obj.strftime("%a, %d.%m.")
            for en, de in weekday_map.items():
                date_str = date_str.replace(en, de)
            
            # Extract temperatures by time of day (find closest match for each period)
            temps_by_time = {
                "morning": None,   # 06:00 - 11:59
                "midday": None,    # 12:00 - 17:59
                "evening": None,   # 18:00 - 20:59
                "night": None      # 21:00 - 05:59
            }
            
            for entry in entries:
                hour = int(entry["dt_txt"].split()[1].split(":")[0])
                temp_celsius = int(entry["main"]["temp"] - 273.15)
                
                if 6 <= hour < 12 and temps_by_time["morning"] is None:
                    temps_by_time["morning"] = temp_celsius
                elif 12 <= hour < 18 and temps_by_time["midday"] is None:
                    temps_by_time["midday"] = temp_celsius
                elif 18 <= hour < 21 and temps_by_time["evening"] is None:
                    temps_by_time["evening"] = temp_celsius
                elif (21 <= hour or hour < 6) and temps_by_time["night"] is None:
                    temps_by_time["night"] = temp_celsius
            
            # Format day parts text, use "--" for missing data
            morning = temps_by_time["morning"] if temps_by_time["morning"] is not None else "--"
            midday = temps_by_time["midday"] if temps_by_time["midday"] is not None else "--"
            evening = temps_by_time["evening"] if temps_by_time["evening"] is not None else "--"
            night = temps_by_time["night"] if temps_by_time["night"] is not None else "--"
            
            dayparts_text = f"{morning}° {midday}° {evening}° {night}°"
            
            forecast_items.append({
                "date_text": date_str,
                "icon_source": f"icons/{icon_code}.png",
                "minmax_text": f"{int(temp_min)}° / {int(temp_max)}°",
                "dayparts_text": dayparts_text
            })
        
        return forecast_items

    def on_responsive_update(self):
        """
        Handle responsive layout updates when window size changes.
        
        Called whenever the window is resized. Recalculates and updates
        the RecycleView height to fit the new available space.
        """
        self._update_rv_height()

    def _update_rv_height(self):
        """
        Calculate and update the RecycleView height based on available space.
        
        Determines the optimal height for the RecycleView by:
        1. Calculating total content height (number of items × row height)
        2. Subtracting navigation and padding heights from card height
        3. Applying minimum (140dp) and maximum constraints
        4. Using the smaller of calculated or maximum height
        
        The RecycleView height is set to ensure all forecast items are visible
        while respecting screen space constraints.
        
        Raises:
            Returns early if required widget IDs are not found in the layout.
        """
        if "rv" not in self.ids or "card" not in self.ids or "nav" not in self.ids:
            return

        content_height = ROW_HEIGHT * len(self.forecast_items)
        padding_and_spacing = dp(44 + 14)

        available = self.ids.card.height - self.ids.nav.height - padding_and_spacing
        if available < dp(140):
            available = dp(140)

        self.ids.rv.height = min(content_height, available)