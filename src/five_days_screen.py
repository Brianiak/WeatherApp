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

from kivy.metrics import dp
from kivy.properties import ListProperty

from base_screen import BaseWeatherScreen

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
        
        Populates the forecast_items list with 5 days of weather data and
        calculates the optimal RecycleView height based on available space.
        
        Args:
            base_widget: The base widget passed by Kivy during initialization
        """
        super().on_kv_post(base_widget)

        self.forecast_items = [
            {"date_text": "Mo, 22.01.", "icon_source": "icons/sun_cloud.png",
             "minmax_text": "4° / 10°", "dayparts_text": "M: 5°   Mi: 9°   A: 7°   N: 4°"},
            {"date_text": "Di, 23.01.", "icon_source": "icons/rain.png",
             "minmax_text": "3° / 8°", "dayparts_text": "M: 4°   Mi: 7°   A: 6°   N: 3°"},
            {"date_text": "Mi, 24.01.", "icon_source": "icons/sun.png",
             "minmax_text": "2° / 9°", "dayparts_text": "M: 3°   Mi: 9°   A: 6°   N: 2°"},
            {"date_text": "Do, 25.01.", "icon_source": "icons/cloud.png",
             "minmax_text": "1° / 7°", "dayparts_text": "M: 2°   Mi: 6°   A: 5°   N: 1°"},
            {"date_text": "Fr, 26.01.", "icon_source": "icons/rain.png",
             "minmax_text": "0° / 6°", "dayparts_text": "M: 1°   Mi: 5°   A: 4°   N: 0°"},
        ]

        self._update_rv_height()

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

