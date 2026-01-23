from kivy.app import App
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    ListProperty,
    NumericProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

ROW_HEIGHT = dp(66)


class ForecastRow(BoxLayout):
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")


class BaseWeatherScreen(Screen):
    is_mobile = BooleanProperty(True)
    card_width = NumericProperty(dp(420))
    MOBILE_BREAKPOINT = dp(600)

    def on_kv_post(self, base_widget):
        self._apply_responsive(Window.size)
        Window.bind(size=self._on_window_resize)

    def _on_window_resize(self, _window, size):
        self._apply_responsive(size)
        self.on_responsive_update()

    def _apply_responsive(self, size):
        width, _ = size
        self.is_mobile = width < self.MOBILE_BREAKPOINT
        self.card_width = max(dp(320), width - dp(30)) if self.is_mobile else min(dp(1050), width - dp(80))

    def on_responsive_update(self):
        pass


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


class SevenDaysScreen(BaseWeatherScreen):
    forecast_items = ListProperty([])

    def on_kv_post(self, base_widget):
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
            {"date_text": "Sa, 27.01.", "icon_source": "icons/sun_cloud.png",
             "minmax_text": "2° / 8°", "dayparts_text": "M: 3°   Mi: 8°   A: 6°   N: 2°"},
            {"date_text": "So, 28.01.", "icon_source": "icons/rain.png",
             "minmax_text": "1° / 7°", "dayparts_text": "M: 2°   Mi: 6°   A: 5°   N: 1°"},
        ]

        self._update_rv_height()

    def on_responsive_update(self):
        self._update_rv_height()

    def _update_rv_height(self):
        if "rv" not in self.ids or "card" not in self.ids or "nav" not in self.ids:
            return

        content_height = ROW_HEIGHT * len(self.forecast_items)
        padding_and_spacing = dp(44 + 14)

        available = self.ids.card.height - self.ids.nav.height - padding_and_spacing
        if available < dp(140):
            available = dp(140)

        self.ids.rv.height = min(content_height, available)


class WeatherRoot(BoxLayout):
    def on_kv_post(self, base_widget):
        self.navigate("today")

    def navigate(self, key: str):
        sm = self.ids.sm
        mapping = {"today": "today", "tomorrow": "tomorrow", "7days": "seven_days"}
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
        elif sm.current == "seven_days":
            nav.ids.btn_7days.state = "down"


class WeatherApp(App):
    def build(self):
        return WeatherRoot()

    def navigate(self, key: str):
        self.root.navigate(key)


if __name__ == "__main__":
    WeatherApp().run()
