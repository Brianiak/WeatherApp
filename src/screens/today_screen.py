from kivy.properties import StringProperty, ListProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.factory import Factory

from base_screen import BaseWeatherScreen


class HourForecast(BoxLayout):
    """Hour forecast tile widget with time, icon, temperature, and description."""
    
    time_text = StringProperty("")
    icon_source = StringProperty("icons/01d.png")
    temp_text = StringProperty("--°")
    desc_text = StringProperty("")


class TodayScreen(BaseWeatherScreen):
    """Screen model for the 'Today' view.

    Provides properties used by the KV layout and a helper to populate
    the horizontal hourly forecast area with items built from the API
    3-hourly forecast entries.
    """

    location_text = StringProperty("Standort wird ermittelt...")
    location_icon_source = StringProperty("icons/location.png")
    temp_text = StringProperty("13\u00b0")
    condition_text = StringProperty("Clouds")
    weather_icon = StringProperty("icons/01d.png")

    # Holds the raw hourly items that were last applied. Not directly used
    # by KV but useful for inspection / testing.
    hourly_items = ListProperty([])

    def set_hourly_data(self, entries: list):
        """Populate the hourly horizontal forecast from a list of API entries.

        Extract time, icon, temperature, and description from each entry
        and create HourForecast widgets. UI definition is in weather.kv.
        """
        try:
            # keep a copy for introspection / testing
            self.hourly_items = entries or []

            if "hourly_box" not in self.ids:
                return

            box = self.ids.hourly_box
            # clear previous widgets
            box.clear_widgets()

            if not entries:
                return

            # Show up to 8 next 3-hourly entries
            MAX_ITEMS = 8
            count = 0
            for entry in entries:
                if count >= MAX_ITEMS:
                    break

                # Extract data from the API entry
                dt_txt = entry.get("dt_txt", "")
                time_str = dt_txt.split()[1] if dt_txt and len(dt_txt.split()) > 1 else "00:00"
                time_text = time_str[:5]

                icon_code = entry.get("weather", [{}])[0].get("icon", "01d")
                icon_source = f"icons/{icon_code}.png"

                temp_k = entry.get("main", {}).get("temp")
                temp_text = f"{int(round(temp_k - 273.15))}°" if temp_k is not None else "--°"

                desc_text = entry.get("weather", [{}])[0].get("main", "")

                # Create HourForecast widget via Factory (UI defined in KV)
                hour_forecast = Factory.HourForecast(
                    time_text=time_text,
                    icon_source=icon_source,
                    temp_text=temp_text,
                    desc_text=desc_text,
                )

                box.add_widget(hour_forecast)
                count += 1

        except Exception as e:
            print(f"Error populating hourly forecast: {e}")
