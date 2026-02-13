from types import SimpleNamespace
from unittest.mock import patch

from kivy.metrics import dp

from base_screen import BaseWeatherScreen
from screens.five_days_screen import FiveDaysScreen, ROW_HEIGHT, VISIBLE_FORECAST_DAYS


class BindableWidget(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind_calls = []

    def bind(self, **kwargs):
        self.bind_calls.append(kwargs)


def _sample_forecast(entries_per_day=3, days=6):
    result = []
    for day_idx in range(days):
        day = 10 + day_idx
        for hour, temp in ((6, 280), (12, 285), (18, 290))[:entries_per_day]:
            result.append(
                {
                    "dt_txt": f"2026-02-{day:02d} {hour:02d}:00:00",
                    "main": {"temp": temp + day_idx},
                    "weather": [{"icon": "01d"}],
                }
            )
    return {"list": result}


class TestFiveDaysScreenLifecycle:
    def test_on_kv_post_calls_super_and_schedules_callbacks(self):
        screen = FiveDaysScreen()
        with patch.object(BaseWeatherScreen, "on_kv_post") as super_on_kv_post:
            with patch("screens.five_days_screen.Clock.schedule_once") as schedule_once:
                screen.on_kv_post(None)

        super_on_kv_post.assert_called_once_with(None)
        assert schedule_once.call_count == 2

    def test_bind_layout_updates_binds_existing_widgets_and_updates_height(self):
        screen = FiveDaysScreen()
        card = BindableWidget(height=500)
        nav = BindableWidget(height=90)
        frog = BindableWidget(height=40)
        screen.ids = {"card": card, "nav": nav, "frog_slot": frog}

        with patch.object(screen, "_update_rv_height") as update_height:
            screen._bind_layout_updates(0)

        assert len(card.bind_calls) == 1
        assert len(nav.bind_calls) == 1
        assert len(frog.bind_calls) == 1
        update_height.assert_called_once()

    def test_load_forecast_data_success_uses_api_data(self):
        screen = FiveDaysScreen()
        processed = [{"date_text": "Mo, 10.02.", "icon_source": "icons/01d.png"}]
        api_data = _sample_forecast(days=2)
        fake_app = SimpleNamespace(current_lat=51.0, current_lon=7.0)

        with patch("screens.five_days_screen.App.get_running_app", return_value=fake_app):
            with patch("screens.five_days_screen.weather_service.get_weather", return_value=api_data):
                with patch.object(screen, "_process_forecast_data", return_value=processed):
                    with patch.object(screen, "_load_fallback_data") as fallback:
                        with patch("screens.five_days_screen.Clock.schedule_once") as schedule_once:
                            screen._load_forecast_data()

        assert screen.forecast_items == processed
        fallback.assert_not_called()
        assert schedule_once.call_count >= 1

    def test_load_forecast_data_failure_uses_fallback(self):
        screen = FiveDaysScreen()
        fake_app = SimpleNamespace(current_lat=51.0, current_lon=7.0)

        with patch("screens.five_days_screen.App.get_running_app", return_value=fake_app):
            with patch(
                "screens.five_days_screen.weather_service.get_weather",
                side_effect=RuntimeError("network down"),
            ):
                with patch.object(screen, "_load_fallback_data") as fallback:
                    with patch("screens.five_days_screen.Clock.schedule_once"):
                        screen._load_forecast_data()

        fallback.assert_called_once()

    def test_on_forecast_items_schedules_height_update(self):
        screen = FiveDaysScreen()
        with patch("screens.five_days_screen.Clock.schedule_once") as schedule_once:
            screen.on_forecast_items(None, [])
        schedule_once.assert_called_once()


class TestFiveDaysScreenDataProcessing:
    def test_process_forecast_data_returns_empty_list_for_empty_payload(self):
        screen = FiveDaysScreen()
        assert screen._process_forecast_data({"list": []}) == []

    def test_process_forecast_data_limits_to_five_days(self):
        screen = FiveDaysScreen()
        result = screen._process_forecast_data(_sample_forecast(days=7))

        assert len(result) == 5
        assert all("date_text" in item for item in result)
        assert all("minmax_text" in item for item in result)
        assert all("dayparts_text" in item for item in result)

    def test_process_forecast_data_skips_entries_without_dt_txt(self):
        screen = FiveDaysScreen()
        data = {
            "list": [
                {"main": {"temp": 280}, "weather": [{"icon": "01d"}]},
                {
                    "dt_txt": "2026-02-10 12:00:00",
                    "main": {"temp": 285},
                    "weather": [{"icon": "01d"}],
                },
            ]
        }

        result = screen._process_forecast_data(data)

        assert len(result) == 1

    def test_process_forecast_data_uses_placeholders_for_missing_dayparts(self):
        screen = FiveDaysScreen()
        data = {
            "list": [
                {
                    "dt_txt": "2026-02-10 12:00:00",
                    "main": {"temp": 285},
                    "weather": [{"icon": "01d"}],
                }
            ]
        }

        result = screen._process_forecast_data(data)

        assert len(result) == 1
        assert "--" in result[0]["dayparts_text"]

    def test_load_fallback_data_populates_five_rows_with_required_fields(self):
        screen = FiveDaysScreen()
        screen._load_fallback_data()

        assert len(screen.forecast_items) == 5
        required = {"date_text", "icon_source", "minmax_text", "dayparts_text"}
        for item in screen.forecast_items:
            assert required.issubset(item.keys())
            assert item["icon_source"].startswith("icons/")


class TestFiveDaysScreenLayout:
    def test_on_responsive_update_calls_height_update(self):
        screen = FiveDaysScreen()
        with patch.object(screen, "_update_rv_height") as update_height:
            screen.on_responsive_update()
        update_height.assert_called_once()

    def test_update_rv_height_returns_early_when_ids_are_missing(self):
        screen = FiveDaysScreen()
        screen.ids = {}
        # Should not raise.
        screen._update_rv_height()

    def test_update_rv_height_uses_min_of_content_and_available(self):
        screen = FiveDaysScreen()
        screen.forecast_items = [1, 2]
        rv = SimpleNamespace(height=0)
        card = SimpleNamespace(height=500)
        nav = SimpleNamespace(height=90)
        frog_slot = SimpleNamespace(height=30)
        screen.ids = {"rv": rv, "card": card, "nav": nav, "frog_slot": frog_slot}

        screen._update_rv_height()

        content_height = ROW_HEIGHT * max(len(screen.forecast_items), VISIBLE_FORECAST_DAYS)
        fixed_spacing = dp(10 * 4)
        weather_card_vertical_padding = dp(44)
        available = card.height - weather_card_vertical_padding - nav.height - frog_slot.height - fixed_spacing
        if available < dp(140):
            available = dp(140)
        assert rv.height == min(content_height, available)

    def test_update_rv_height_enforces_minimum_available_height(self):
        screen = FiveDaysScreen()
        screen.forecast_items = list(range(20))
        rv = SimpleNamespace(height=0)
        card = SimpleNamespace(height=100)
        nav = SimpleNamespace(height=70)
        frog_slot = SimpleNamespace(height=30)
        screen.ids = {"rv": rv, "card": card, "nav": nav, "frog_slot": frog_slot}

        screen._update_rv_height()

        assert rv.height == dp(140)
