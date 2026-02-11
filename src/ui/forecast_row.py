from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class ForecastRow(BoxLayout):
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")
