from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import SlideTransition


class WeatherRoot(BoxLayout):
    def on_kv_post(self, base_widget):
        self.navigate("today")

    def navigate(self, key: str):
        sm = self.ids.sm
        mapping = {"today": "today", "tomorrow": "tomorrow", "5days": "five_days"}
        target = mapping.get(key)
        if not target:
            return

        # determine transition direction based on current and target indices
        try:
            names = list(sm.screen_names)
            current_index = names.index(sm.current) if sm.current in names else 0
            target_index = names.index(target)
            if target_index > current_index:
                direction = "left"
            elif target_index < current_index:
                direction = "right"
            else:
                direction = None
        except Exception:
            direction = None

        if direction:
            sm.transition = SlideTransition(direction=direction, duration=0.5)

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
