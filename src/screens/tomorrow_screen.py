from kivy.properties import StringProperty, ListProperty
from kivy.factory import Factory

from base_screen import BaseWeatherScreen


class TomorrowScreen(BaseWeatherScreen):
    location_text = StringProperty("Standort wird ermittelt...")
    condition_text = StringProperty("Clouds")
    minmax_text = StringProperty("Min. Temp / Max. Temp")
    dayparts_text = StringProperty("Morgen / Mittag / Abend / Nacht")
    weather_icon = StringProperty("icons/01d.png")
    hourly_items = ListProperty([])

    def set_hourly_data(self, entries: list):
        """Populate the hourly forecast for tomorrow."""
        try:
            self.hourly_items = entries or []

            if "hourly_box" not in self.ids:
                return

            box = self.ids.hourly_box
            box.clear_widgets()

            if not entries:
                return

            # Show all entries for tomorrow (no limit)
            for entry in entries:
                dt_txt = entry.get("dt_txt", "")
                time_str = dt_txt.split()[1] if dt_txt and len(dt_txt.split()) > 1 else "00:00"
                time_text = time_str[:5]

                icon_code = entry.get("weather", [{}])[0].get("icon", "01d")
                icon_source = f"icons/{icon_code}.png"

                temp_k = entry.get("main", {}).get("temp")
                temp_text = f"{int(round(temp_k - 273.15))}°" if temp_k is not None else "--°"

                desc_text = entry.get("weather", [{}])[0].get("main", "")

                hour_forecast = Factory.HourForecast(
                    time_text=time_text,
                    icon_source=icon_source,
                    temp_text=temp_text,
                    desc_text=desc_text,
                )

                box.add_widget(hour_forecast)

        except Exception as e:
            print(f"Error populating hourly forecast for tomorrow: {e}")
