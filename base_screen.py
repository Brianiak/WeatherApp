from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.screenmanager import Screen


class BaseWeatherScreen(Screen):
    card_width = NumericProperty(dp(350))

    def on_kv_post(self, base_widget):
        Window.bind(size=self._on_window_resize)

    def _on_window_resize(self, _window, size):
        self.on_responsive_update()

    def on_responsive_update(self):
        pass
