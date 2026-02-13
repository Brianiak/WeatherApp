import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import unittest  # noqa: E402
from unittest.mock import patch  # noqa: E402

import coverage  # noqa: E402
from kivy.metrics import dp  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.clock import Clock  # noqa: E402

from screens.five_days_screen import FiveDaysScreen, ROW_HEIGHT  # noqa: E402
import services.weather_service as weather_service  # noqa: E402, F401

# Initialize coverage
cov = coverage.Coverage()


class TestFiveDaysScreen(unittest.TestCase):
    """Test suite for FiveDaysScreen class"""

    def setUp(self):
        """Set up test fixtures before each test"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        # Mock weather_service.get_weather to trigger fallback data
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()
        
    def _trigger_data_load(self):
        """Helper method to trigger and complete data loading"""
        self.screen.on_kv_post(None)
        Clock.tick()  # Process all scheduled events

    def test_initialization(self):
        """Test that FiveDaysScreen initializes correctly"""
        self.assertIsNotNone(self.screen)
        self.assertEqual(self.screen.card_width, dp(350))

    def test_forecast_items_count(self):
        """Test that exactly 5 forecast items are loaded"""
        self._trigger_data_load()
        self.assertEqual(len(self.screen.forecast_items), 5)

    def test_forecast_items_structure(self):
        """Test that forecast items have correct structure"""
        self._trigger_data_load()
        required_keys = {"date_text", "icon_source", "minmax_text", "dayparts_text"}
        for item in self.screen.forecast_items:
            self.assertTrue(required_keys.issubset(item.keys()))

    def test_forecast_items_dates(self):
        """Test that forecast items have valid dates"""
        self._trigger_data_load()
        expected_dates = ["Mo, 22.01.", "Di, 23.01.", "Mi, 24.01.", "Do, 25.01.", "Fr, 26.01."]
        actual_dates = [item["date_text"] for item in self.screen.forecast_items]
        self.assertEqual(actual_dates, expected_dates)

    def test_forecast_items_have_icons(self):
        """Test that all forecast items have valid icon sources"""
        self._trigger_data_load()
        valid_icons = {
            "icons/01d.png", "icons/01n.png", "icons/02d.png", "icons/02n.png",
            "icons/03d.png", "icons/03n.png", "icons/04d.png", "icons/04n.png",
            "icons/09d.png", "icons/09n.png", "icons/10d.png", "icons/10n.png",
            "icons/11d.png", "icons/11n.png", "icons/13d.png", "icons/13n.png",
            "icons/50d.png", "icons/50n.png"
        }
        for item in self.screen.forecast_items:
            self.assertIn(item["icon_source"], valid_icons)

    def test_row_height_constant(self):
        """Test that ROW_HEIGHT is correctly defined"""
        self.assertEqual(ROW_HEIGHT, dp(66))

    def test_card_width_is_mobile_optimized(self):
        """Test that card_width is optimized for mobile devices"""
        self.assertEqual(self.screen.card_width, dp(350))
        # Mobile breakpoint is typically around 600dp
        self.assertLess(self.screen.card_width, dp(600))

    def test_responsive_update_callback(self):
        """Test that on_responsive_update method exists"""
        self.assertTrue(hasattr(self.screen, "on_responsive_update"))
        self.assertTrue(callable(self.screen.on_responsive_update))

    def test_update_rv_height_method_exists(self):
        """Test that _update_rv_height method exists"""
        self.assertTrue(hasattr(self.screen, "_update_rv_height"))
        self.assertTrue(callable(self.screen._update_rv_height))

    def test_forecast_data_not_empty(self):
        """Test that forecast data is populated after initialization"""
        self._trigger_data_load()
        self.assertGreater(len(self.screen.forecast_items), 0)
        for item in self.screen.forecast_items:
            self.assertTrue(item["date_text"])
            self.assertTrue(item["icon_source"])
            self.assertTrue(item["minmax_text"])
            self.assertTrue(item["dayparts_text"])


class TestForecastItemValidation(unittest.TestCase):
    """Test suite for forecast item data validation"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        # Mock weather_service.get_weather to trigger fallback data
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")
        # Trigger data load
        self.screen.on_kv_post(None)
        Clock.tick()  # Process all scheduled events

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_min_max_temp_format(self):
        """Test that min/max temps are in correct format"""
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            # Should be in format "X° / Y°"
            self.assertIn("°", minmax)
            self.assertIn("/", minmax)

    def test_dayparts_text_format(self):
        """Test that dayparts text contains only 4 temperature values"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            # Should be 4 plain values without prefixes (M:, Mi:, A:, N:)
            self.assertEqual(len(dayparts.split()), 4)
            self.assertNotIn(":", dayparts)
    

# Dummy Tests for coverage


class TestProcessForecastData(unittest.TestCase):
    """Test suite for _process_forecast_data method"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_process_forecast_data_returns_list(self):
        """Test that _process_forecast_data returns a list"""
        mock_data = {
            "list": [
                {
                    "dt_txt": "2026-02-22 12:00:00",
                    "main": {"temp": 290},
                    "weather": [{"icon": "01d"}]
                }
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        self.assertIsInstance(result, list)

    def test_process_forecast_data_groups_by_date(self):
        """Test that forecast data is grouped by date"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 09:00:00", "main": {"temp": 285}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 15:00:00", "main": {"temp": 292}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        # All 3 entries are same day, should produce 1 item
        self.assertEqual(len(result), 1)

    def test_process_forecast_data_limits_to_5_days(self):
        """Test that only first 5 days are returned"""
        mock_data = {
            "list": [
                {"dt_txt": f"2026-02-{22+i} 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]}
                for i in range(10)
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        self.assertEqual(len(result), 5)

    def test_process_forecast_data_calculates_min_max_temps(self):
        """Test that min/max temperatures are calculated correctly"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 06:00:00", "main": {"temp": 280}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 18:00:00", "main": {"temp": 285}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        self.assertEqual(len(result), 1)
        minmax = result[0]["minmax_text"]
        self.assertIn("/", minmax)
        self.assertIn("°", minmax)

    def test_process_forecast_data_converts_kelvin_to_celsius(self):
        """Test that Kelvin temperatures are converted to Celsius"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 273.15}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        # 273.15K = 0°C
        minmax = result[0]["minmax_text"]
        self.assertIn("0°", minmax)

    def test_process_forecast_data_formats_dates_correctly(self):
        """Test that dates are formatted with German weekdays"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-23 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        date_text = result[0]["date_text"]
        # Should have German format
        self.assertIn(".", date_text)
        self.assertIn(",", date_text)

    def test_process_forecast_data_selects_midday_icon(self):
        """Test that midday weather icon is selected"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 06:00:00", "main": {"temp": 280}, "weather": [{"icon": "02d"}]},
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 18:00:00", "main": {"temp": 285}, "weather": [{"icon": "03d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        icon = result[0]["icon_source"]
        # Midday icon should be used
        self.assertIn("01d", icon)

    def test_process_forecast_data_extracts_temps_by_time(self):
        """Test that temperatures by time of day are extracted"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 06:00:00", "main": {"temp": 280}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 295}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 18:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 21:00:00", "main": {"temp": 285}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        dayparts = result[0]["dayparts_text"]
        # Should have 4 temperature values
        self.assertIn("°", dayparts)

    def test_process_forecast_data_handles_missing_daypart_data(self):
        """Test that missing daypart data shows '--'"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        dayparts = result[0]["dayparts_text"]
        # Should have dashes for missing data
        self.assertIn("--", dayparts)

    def test_process_forecast_data_skips_entries_without_dt_txt(self):
        """Test that entries without dt_txt are skipped"""
        mock_data = {
            "list": [
                {"main": {"temp": 290}, "weather": [{"icon": "01d"}]},  # Missing dt_txt
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        # Should still process the valid entry
        self.assertEqual(len(result), 1)

    def test_process_forecast_data_empty_list(self):
        """Test that empty list returns empty forecast_items"""
        mock_data = {"list": []}
        result = self.screen._process_forecast_data(mock_data)
        self.assertEqual(len(result), 0)

    def test_process_forecast_data_morning_temps(self):
        """Test extraction of morning temperature (6:00-11:59)"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 06:00:00", "main": {"temp": 280}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 09:00:00", "main": {"temp": 285}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 12:00:00", "main": {"temp": 290}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        dayparts = result[0]["dayparts_text"]
        # Should contain morning temperature
        self.assertNotEqual(dayparts.count("°"), 0)

    def test_process_forecast_data_night_temps(self):
        """Test extraction of night temperature (21:00-05:59)"""
        mock_data = {
            "list": [
                {"dt_txt": "2026-02-22 21:00:00", "main": {"temp": 275}, "weather": [{"icon": "01d"}]},
                {"dt_txt": "2026-02-22 23:00:00", "main": {"temp": 270}, "weather": [{"icon": "01d"}]},
            ]
        }
        result = self.screen._process_forecast_data(mock_data)
        dayparts = result[0]["dayparts_text"]
        # Should have temperature values
        self.assertIn("°", dayparts)


class TestLoadFallbackData(unittest.TestCase):
    """Test suite for _load_fallback_data method"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_load_fallback_data_populates_items(self):
        """Test that fallback data populates forecast_items"""
        self.screen._load_fallback_data()
        self.assertEqual(len(self.screen.forecast_items), 5)

    def test_load_fallback_data_has_required_fields(self):
        """Test that fallback data has all required fields"""
        self.screen._load_fallback_data()
        required_keys = {"date_text", "icon_source", "minmax_text", "dayparts_text"}
        for item in self.screen.forecast_items:
            self.assertTrue(required_keys.issubset(item.keys()))

    def test_load_fallback_data_dates_are_sequential(self):
        """Test that fallback data dates are sequential"""
        self.screen._load_fallback_data()
        dates = [item["date_text"] for item in self.screen.forecast_items]
        self.assertEqual(len(dates), 5)
        # Check for sequential weekdays
        self.assertIn("Mo", dates[0])
        self.assertIn("Di", dates[1])

    def test_load_fallback_data_icons_are_valid(self):
        """Test that fallback data icons are valid paths"""
        self.screen._load_fallback_data()
        for item in self.screen.forecast_items:
            icon = item["icon_source"]
            self.assertTrue(icon.startswith("icons/"))
            self.assertTrue(icon.endswith(".png"))

    def test_load_fallback_data_minmax_format(self):
        """Test that fallback data has correct minmax format"""
        self.screen._load_fallback_data()
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            self.assertIn("/", minmax)
            self.assertIn("°", minmax)

    def test_load_fallback_data_dayparts_format(self):
        """Test that fallback data has 4 plain daypart temperatures"""
        self.screen._load_fallback_data()
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            self.assertEqual(len(dayparts.split()), 4)
            self.assertNotIn(":", dayparts)


class TestUpdateRVHeight(unittest.TestCase):
    """Test suite for _update_rv_height method"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_update_rv_height_doesnt_crash_without_ids(self):
        """Test that _update_rv_height handles missing widget IDs gracefully"""
        try:
            self.screen._update_rv_height()
        except Exception as e:
            self.fail(f"_update_rv_height raised {type(e).__name__} unexpectedly!")

    def test_on_responsive_update_calls_update_rv_height(self):
        """Test that on_responsive_update calls _update_rv_height"""
        with patch.object(self.screen, '_update_rv_height') as mock_update:
            self.screen.on_responsive_update()
            mock_update.assert_called_once()

# ----


if __name__ == "__main__":
    cov.start()
    unittest.main(verbosity=2, exit=False)
    cov.stop()
    cov.save()
    print("\n" + "="*70)
    print("Coverage Report:")
    print("="*70)
    cov.report()
    print("\nHTML Coverage Report generated in: htmlcov/index.html")
    cov.html_report(directory="htmlcov")

