from kivy.properties import StringProperty

from base_screen import BaseWeatherScreen


class TodayScreen(BaseWeatherScreen):
    location_text = StringProperty("Standort wird ermittelt...")
    temp_text = StringProperty("13\u00b0")
    condition_text = StringProperty("Clouds")
    humidity_text = StringProperty("82%")
    wind_text = StringProperty("6 km/h")
