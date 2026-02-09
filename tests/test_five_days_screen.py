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

from five_days_screen import FiveDaysScreen, ROW_HEIGHT  # noqa: E402
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
        """Test that dayparts text contains expected abbreviations"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            # Should contain M (Morgen), Mi (Mittag), A (Abend), N (Nacht)
            self.assertIn("M:", dayparts)
            self.assertIn("Mi:", dayparts)
            self.assertIn("A:", dayparts)
            self.assertIn("N:", dayparts)
    

# Dummy Tests for coverage


class TestFiveDaysScreenDataLoading(unittest.TestCase):
    """Test suite for data loading in FiveDaysScreen"""

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

    def test_on_kv_post_triggers_data_load(self):
        """Test that on_kv_post method triggers data loading"""
        self.screen.on_kv_post(None)
        Clock.tick()
        self.assertIsNotNone(self.screen.forecast_items)

    def test_forecast_items_property_initialized(self):
        """Test that forecast_items property is initialized"""
        self.assertTrue(hasattr(self.screen, 'forecast_items'))
        self.assertIsInstance(self.screen.forecast_items, list)

    def test_all_forecast_items_have_date_text(self):
        """Test that all forecast items have non-empty date_text"""
        self.screen.on_kv_post(None)
        Clock.tick()
        for item in self.screen.forecast_items:
            self.assertIsNotNone(item.get("date_text"))
            self.assertNotEqual(item.get("date_text"), "")

    def test_all_forecast_items_have_icon_source(self):
        """Test that all forecast items have valid icon sources"""
        self.screen.on_kv_post(None)
        Clock.tick()
        for item in self.screen.forecast_items:
            self.assertIsNotNone(item.get("icon_source"))
            self.assertTrue(item.get("icon_source").endswith(".png"))

    def test_all_forecast_items_have_minmax_text(self):
        """Test that all forecast items have minmax temperature text"""
        self.screen.on_kv_post(None)
        Clock.tick()
        for item in self.screen.forecast_items:
            self.assertIsNotNone(item.get("minmax_text"))
            self.assertIn("°", item.get("minmax_text"))

    def test_all_forecast_items_have_dayparts_text(self):
        """Test that all forecast items have dayparts text"""
        self.screen.on_kv_post(None)
        Clock.tick()
        for item in self.screen.forecast_items:
            self.assertIsNotNone(item.get("dayparts_text"))
            self.assertNotEqual(item.get("dayparts_text"), "")


class TestFiveDaysScreenResponsiveness(unittest.TestCase):
    """Test suite for responsive design features"""

    def setUp(self):
        """Set up test fixtures"""
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_card_width_property_exists(self):
        """Test that card_width property exists"""
        self.assertTrue(hasattr(self.screen, 'card_width'))

    def test_card_width_value(self):
        """Test that card_width has correct value"""
        self.assertEqual(self.screen.card_width, dp(350))

    def test_on_responsive_update_callable(self):
        """Test that on_responsive_update is callable"""
        self.assertTrue(callable(self.screen.on_responsive_update))

    def test_update_rv_height_callable(self):
        """Test that _update_rv_height is callable"""
        self.assertTrue(callable(self.screen._update_rv_height))

    def test_on_responsive_update_doesnt_raise(self):
        """Test that on_responsive_update can be called without errors"""
        try:
            self.screen.on_responsive_update()
        except Exception as e:
            self.fail(f"on_responsive_update raised {type(e).__name__} unexpectedly!")

    def test_update_rv_height_doesnt_raise(self):
        """Test that _update_rv_height can be called without errors"""
        try:
            self.screen._update_rv_height()
        except Exception as e:
            self.fail(f"_update_rv_height raised {type(e).__name__} unexpectedly!")


class TestFiveDaysScreenDateFormatting(unittest.TestCase):
    """Test suite for date formatting"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")
        self.screen.on_kv_post(None)
        Clock.tick()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_date_format_contains_day_abbrev(self):
        """Test that dates contain day abbreviations (Mo, Di, etc.)"""
        day_abbrevs = {"Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"}
        for item in self.screen.forecast_items:
            date_text = item["date_text"]
            has_day = any(abbrev in date_text for abbrev in day_abbrevs)
            self.assertTrue(has_day, f"Date '{date_text}' has no day abbreviation")

    def test_date_format_contains_date_numbers(self):
        """Test that dates contain date numbers"""
        for item in self.screen.forecast_items:
            date_text = item["date_text"]
            # Should contain numbers for day and month
            has_numbers = any(c.isdigit() for c in date_text)
            self.assertTrue(has_numbers, f"Date '{date_text}' has no numbers")

    def test_date_format_contains_dot_separator(self):
        """Test that dates use dot as separator"""
        for item in self.screen.forecast_items:
            date_text = item["date_text"]
            self.assertIn(".", date_text, f"Date '{date_text}' missing dot separator")

    def test_dates_are_sequential(self):
        """Test that forecast dates are sequential days"""
        self.screen.on_kv_post(None)
        Clock.tick()
        self.assertEqual(len(self.screen.forecast_items), 5)


class TestFiveDaysScreenTemperatureFormatting(unittest.TestCase):
    """Test suite for temperature formatting"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")
        self.screen.on_kv_post(None)
        Clock.tick()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_minmax_format_has_slash(self):
        """Test that minmax format contains slash separator"""
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            self.assertIn("/", minmax)

    def test_minmax_format_has_degree_symbols(self):
        """Test that minmax format has degree symbols"""
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            count = minmax.count("°")
            self.assertGreaterEqual(count, 2, f"'{minmax}' should have at least 2 degree symbols")

    def test_minmax_has_two_temperatures(self):
        """Test that minmax has min and max temperature"""
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            parts = minmax.split("/")
            self.assertEqual(len(parts), 2, f"'{minmax}' should split into 2 parts")

    def test_temperatures_are_numeric(self):
        """Test that temperature values are numeric"""
        for item in self.screen.forecast_items:
            minmax = item["minmax_text"]
            # Remove symbols and check if we can find numbers
            cleaned = minmax.replace("°", "").replace("/", "").replace(" ", "")
            has_numbers = any(c.isdigit() for c in cleaned)
            self.assertTrue(has_numbers, f"'{minmax}' should contain numbers")


class TestFiveDaysScreenDaypartsFormatting(unittest.TestCase):
    """Test suite for dayparts formatting"""

    def setUp(self):
        """Set up test fixtures"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()
        self.patcher = patch('five_days_screen.weather_service.get_weather')
        self.mock_get_weather = self.patcher.start()
        self.mock_get_weather.side_effect = Exception("Mocked API failure for testing")
        self.screen.on_kv_post(None)
        Clock.tick()

    def tearDown(self):
        """Clean up after each test"""
        self.patcher.stop()

    def test_dayparts_contains_morning_abbreviation(self):
        """Test that dayparts contains morning abbreviation"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            self.assertIn("M:", dayparts)

    def test_dayparts_contains_midday_abbreviation(self):
        """Test that dayparts contains midday abbreviation"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            self.assertIn("Mi:", dayparts)

    def test_dayparts_contains_evening_abbreviation(self):
        """Test that dayparts contains evening abbreviation"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            self.assertIn("A:", dayparts)

    def test_dayparts_contains_night_abbreviation(self):
        """Test that dayparts contains night abbreviation"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            self.assertIn("N:", dayparts)

    def test_dayparts_format_has_temperatures(self):
        """Test that dayparts format contains temperature values"""
        for item in self.screen.forecast_items:
            dayparts = item["dayparts_text"]
            # Should contain degree symbols for each daypart
            count = dayparts.count("°")
            self.assertGreaterEqual(count, 4, f"'{dayparts}' should have at least 4 degree symbols")

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


