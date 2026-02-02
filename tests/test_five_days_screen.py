import sys
import unittest
from pathlib import Path

import coverage
from kivy.metrics import dp
from kivy.core.window import Window

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from five_days_screen import FiveDaysScreen, ROW_HEIGHT  # noqa: E402

# Initialize coverage
cov = coverage.Coverage()


class TestFiveDaysScreen(unittest.TestCase):
    """Test suite for FiveDaysScreen class"""

    def setUp(self):
        """Set up test fixtures before each test"""
        Window.size = (400, 800)
        self.screen = FiveDaysScreen()

    def test_initialization(self):
        """Test that FiveDaysScreen initializes correctly"""
        self.assertIsNotNone(self.screen)
        self.assertEqual(self.screen.card_width, dp(350))

    def test_forecast_items_count(self):
        """Test that exactly 5 forecast items are loaded"""
        self.screen.on_kv_post(None)
        self.assertEqual(len(self.screen.forecast_items), 5)

    def test_forecast_items_structure(self):
        """Test that forecast items have correct structure"""
        self.screen.on_kv_post(None)
        required_keys = {"date_text", "icon_source", "minmax_text", "dayparts_text"}
        for item in self.screen.forecast_items:
            self.assertTrue(required_keys.issubset(item.keys()))

    def test_forecast_items_dates(self):
        """Test that forecast items have valid dates"""
        self.screen.on_kv_post(None)
        expected_dates = ["Mo, 22.01.", "Di, 23.01.", "Mi, 24.01.", "Do, 25.01.", "Fr, 26.01."]
        actual_dates = [item["date_text"] for item in self.screen.forecast_items]
        self.assertEqual(actual_dates, expected_dates)

    def test_forecast_items_have_icons(self):
        """Test that all forecast items have valid icon sources"""
        self.screen.on_kv_post(None)
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
        self.screen.on_kv_post(None)
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
        self.screen.on_kv_post(None)

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


