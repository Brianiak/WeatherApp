from kivy.properties import StringProperty

from base_screen import BaseWeatherScreen


class TomorrowScreen(BaseWeatherScreen):
    location_text = StringProperty("Standort wird ermittelt...")
    condition_text = StringProperty("Clouds")
    minmax_text = StringProperty("Min. Temp / Max. Temp")
    dayparts_text = StringProperty("Morgen / Mittag / Abend / Nacht")
