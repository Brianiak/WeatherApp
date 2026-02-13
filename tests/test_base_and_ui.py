from types import SimpleNamespace
from unittest.mock import patch

from base_screen import BaseWeatherScreen
from ui.forecast_row import ForecastRow
from ui.weather_root import WeatherRoot


class AttrDict(dict):
    __getattr__ = dict.__getitem__


class ResponsiveScreen(BaseWeatherScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.responsive_calls = 0

    def on_responsive_update(self):
        self.responsive_calls += 1


class DummyButton:
    def __init__(self):
        self.state = "normal"


class DummyNav:
    def __init__(self):
        self.ids = SimpleNamespace(
            btn_today=DummyButton(),
            btn_tomorrow=DummyButton(),
            btn_5days=DummyButton(),
        )


class DummyScreen:
    def __init__(self):
        self.ids = AttrDict(nav=DummyNav())


class DummyScreenManager:
    def __init__(self):
        self.screen_names = ["today", "tomorrow", "five_days"]
        self.current = "today"
        self.transition = None
        self._screens = {name: DummyScreen() for name in self.screen_names}

    def has_screen(self, name):
        return name in self._screens

    def get_screen(self, name):
        return self._screens[name]


def _build_root_with_manager():
    with patch.object(WeatherRoot, "on_kv_post", lambda self, base_widget: None):
        root = WeatherRoot()
    manager = DummyScreenManager()
    root.ids = {"sm": manager}
    return root, manager


class TestBaseWeatherScreen:
    def test_on_kv_post_binds_window_resize_event(self):
        screen = ResponsiveScreen()

        with patch("base_screen.Window.bind") as window_bind:
            screen.on_kv_post(None)

        window_bind.assert_called_once_with(size=screen._on_window_resize)

    def test_on_window_resize_triggers_responsive_update(self):
        screen = ResponsiveScreen()
        screen._on_window_resize(None, (400, 800))
        assert screen.responsive_calls == 1


class TestWeatherRoot:
    def test_on_kv_post_calls_navigate_today(self):
        root, _manager = _build_root_with_manager()

        with patch.object(root, "navigate") as navigate:
            WeatherRoot.on_kv_post(root, None)

        navigate.assert_called_once_with("today")

    def test_navigate_ignores_unknown_key(self):
        root, manager = _build_root_with_manager()
        root.navigate("unknown")
        assert manager.current == "today"

    def test_navigate_forward_sets_left_transition(self):
        root, manager = _build_root_with_manager()
        root.navigate("tomorrow")

        assert manager.current == "tomorrow"
        assert manager.transition is not None
        assert manager.transition.direction == "left"

    def test_navigate_backward_sets_right_transition(self):
        root, manager = _build_root_with_manager()
        manager.current = "five_days"
        root.navigate("today")

        assert manager.current == "today"
        assert manager.transition is not None
        assert manager.transition.direction == "right"

    def test_sync_nav_for_current_sets_active_button(self):
        root, manager = _build_root_with_manager()

        manager.current = "today"
        root._sync_nav_for_current()
        today_nav = manager.get_screen("today").ids["nav"]
        assert today_nav.ids.btn_today.state == "down"

        manager.current = "tomorrow"
        root._sync_nav_for_current()
        tomorrow_nav = manager.get_screen("tomorrow").ids["nav"]
        assert tomorrow_nav.ids.btn_tomorrow.state == "down"

        manager.current = "five_days"
        root._sync_nav_for_current()
        five_days_nav = manager.get_screen("five_days").ids["nav"]
        assert five_days_nav.ids.btn_5days.state == "down"


class TestForecastRow:
    def test_defaults(self):
        row = ForecastRow()
        assert row.date_text == ""
        assert row.icon_source == ""
        assert row.minmax_text == ""
        assert row.dayparts_text == ""
