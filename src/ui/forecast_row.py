from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout


class ForecastRow(BoxLayout):
    """Forecast row widget displaying daily forecast information.
    
    Displays a single row in the 5-day forecast list with date, weather icon,
    min/max temperatures, and hourly temperature breakdown (morning, midday,
    evening, night).
    """
    
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")
