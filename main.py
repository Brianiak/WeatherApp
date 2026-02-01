from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout

from base_screen import BaseWeatherScreen
from five_days_screen import FiveDaysScreen

ROW_HEIGHT = dp(66)


class ForecastRow(BoxLayout):
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")


class TodayScreen(BaseWeatherScreen):
    location_text = StringProperty("Houston, US")
    temp_text = StringProperty("13°")
    condition_text = StringProperty("Clouds")
    humidity_text = StringProperty("82%")
    wind_text = StringProperty("6 km/h")


class TomorrowScreen(BaseWeatherScreen):
    location_text = StringProperty("Houston, US")
    condition_text = StringProperty("Clouds")
    minmax_text = StringProperty("Min. Temp / Max. Temp")
    dayparts_text = StringProperty("Morgen / Mittag / Abend / Nacht")


class WeatherRoot(BoxLayout):
    def on_kv_post(self, base_widget):
        self.navigate("today")

    def navigate(self, key: str):
        sm = self.ids.sm
        mapping = {"today": "today", "tomorrow": "tomorrow", "5days": "five_days"}
        target = mapping.get(key)
        if not target:
            return

        sm.current = target
        self._sync_nav_for_current()

    def _sync_nav_for_current(self):
        sm = self.ids.sm
        screen = sm.get_screen(sm.current)

        if "nav" not in screen.ids:
            return

        nav = screen.ids.nav
        if sm.current == "today":
            nav.ids.btn_today.state = "down"
        elif sm.current == "tomorrow":
            nav.ids.btn_tomorrow.state = "down"
        elif sm.current == "five_days":
            nav.ids.btn_5days.state = "down"


class WeatherApp(App):
    def build(self):
        return WeatherRoot()

    def navigate(self, key: str):
        self.root.navigate(key)


if __name__ == "__main__":
    WeatherApp().run()
