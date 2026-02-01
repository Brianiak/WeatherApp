from kivy.metrics import dp
from kivy.properties import ListProperty

from base_screen import BaseWeatherScreen

ROW_HEIGHT = dp(66)


class FiveDaysScreen(BaseWeatherScreen):
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

