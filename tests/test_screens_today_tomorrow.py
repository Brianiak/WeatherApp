from unittest.mock import patch

from screens.today_screen import TodayScreen
from screens.tomorrow_screen import TomorrowScreen


class DummyBox:
    def __init__(self):
        self.widgets = []
        self.cleared = False

    def clear_widgets(self):
        self.widgets.clear()
        self.cleared = True

    def add_widget(self, widget):
        self.widgets.append(widget)


def _entry(hour, temp=280, icon="01d", main="Clouds"):
    return {
        "dt_txt": f"2026-02-10 {hour:02d}:00:00",
        "main": {"temp": temp},
        "weather": [{"icon": icon, "main": main}],
    }


class TestTodayScreen:
    def test_set_hourly_data_keeps_items_when_hourly_box_is_missing(self):
        screen = TodayScreen()
        entries = [_entry(9), _entry(12)]
        screen.ids = {}

        screen.set_hourly_data(entries)

        assert screen.hourly_items == entries

    def test_set_hourly_data_clears_and_populates_up_to_eight_widgets(self):
        screen = TodayScreen()
        box = DummyBox()
        screen.ids = {"hourly_box": box}
        entries = [_entry(hour=(i % 24), temp=273.15 + i) for i in range(10)]

        with patch("screens.today_screen.Factory.HourForecast", side_effect=lambda **kwargs: kwargs):
            screen.set_hourly_data(entries)

        assert box.cleared is True
        assert len(box.widgets) == 8
        assert box.widgets[0]["time_text"] == "00:00"
        assert box.widgets[0]["icon_source"] == "icons/01d.png"

    def test_set_hourly_data_uses_defaults_for_missing_fields(self):
        screen = TodayScreen()
        box = DummyBox()
        screen.ids = {"hourly_box": box}

        with patch("screens.today_screen.Factory.HourForecast", side_effect=lambda **kwargs: kwargs):
            screen.set_hourly_data([{}])

        assert len(box.widgets) == 1
        widget = box.widgets[0]
        assert widget["time_text"] == "00:00"
        assert widget["icon_source"] == "icons/01d.png"
        assert widget["temp_text"].startswith("--")
        assert widget["desc_text"] == ""

    def test_set_hourly_data_handles_factory_errors_without_raising(self):
        screen = TodayScreen()
        box = DummyBox()
        screen.ids = {"hourly_box": box}

        with patch("screens.today_screen.Factory.HourForecast", side_effect=RuntimeError("ui error")):
            screen.set_hourly_data([_entry(9)])

        assert box.widgets == []


class TestTomorrowScreen:
    def test_set_hourly_data_keeps_items_when_hourly_box_is_missing(self):
        screen = TomorrowScreen()
        entries = [_entry(9), _entry(12)]
        screen.ids = {}

        screen.set_hourly_data(entries)

        assert screen.hourly_items == entries

    def test_set_hourly_data_populates_all_entries_without_limit(self):
        screen = TomorrowScreen()
        box = DummyBox()
        screen.ids = {"hourly_box": box}
        entries = [_entry(hour=(i % 24), temp=280 + i, icon="02d") for i in range(12)]

        with patch(
            "screens.tomorrow_screen.Factory.HourForecast",
            side_effect=lambda **kwargs: kwargs,
        ):
            screen.set_hourly_data(entries)

        assert box.cleared is True
        assert len(box.widgets) == 12
        assert box.widgets[0]["icon_source"] == "icons/02d.png"

    def test_set_hourly_data_uses_defaults_for_missing_fields(self):
        screen = TomorrowScreen()
        box = DummyBox()
        screen.ids = {"hourly_box": box}

        with patch(
            "screens.tomorrow_screen.Factory.HourForecast",
            side_effect=lambda **kwargs: kwargs,
        ):
            screen.set_hourly_data([{}])

        assert len(box.widgets) == 1
        widget = box.widgets[0]
        assert widget["time_text"] == "00:00"
        assert widget["icon_source"] == "icons/01d.png"
        assert widget["temp_text"].startswith("--")
        assert widget["desc_text"] == ""
