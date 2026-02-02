import sys
from pathlib import Path
import os
import unittest
from unittest.mock import patch, Mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))
import weather_service

import coverage

# Initialize coverage
cov = coverage.Coverage()

class TestWeatherService(unittest.TestCase):
    """Unit tests for `weather_service` that mock network calls.

    These tests mock `requests.get` so no real API tokens are consumed.
    """

    def setUp(self):
        # Ensure environment variables exist for the service to read.
        # Prevent the real .env from being loaded during tests
        self.patcher = patch("weather_service.load_dotenv", return_value={})
        self.patcher.start()

        os.environ.setdefault("URL", "http://example.com/api?key=")
        os.environ.setdefault("API_KEY", "TESTKEY")

    def tearDown(self):
        os.environ.pop("URL", None)
        os.environ.pop("API_KEY", None)
        self.patcher.stop()

    def test_get_weather_success(self):
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.text = "{}"
        fake.json.return_value = {"ok": True}

        with patch("weather_service.requests.get", return_value=fake) as mock_get:
            data = weather_service.get_weather()
            self.assertEqual(data, {"ok": True})
            mock_get.assert_called_once_with(
                url="http://example.com/api?key=TESTKEY", timeout=10
            )

    def test_network_error_raises(self):
        with patch("weather_service.requests.get", side_effect=weather_service.requests.ConnectionError("x")):
            with self.assertRaises(weather_service.NetworkError):
                weather_service.get_weather()

    def test_401_raises_token_error(self):
        fake = Mock()
        fake.status_code = 401
        fake.ok = False
        fake.text = "Unauthorized"
        with patch("weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APITokenExpiredError):
                weather_service.get_weather()

    def test_5xx_raises_service_unavailable(self):
        fake = Mock()
        fake.status_code = 503
        fake.ok = False
        fake.text = "Service Unavailable"
        with patch("weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.ServiceUnavailableError):
                weather_service.get_weather()

    def test_4xx_raises_api_request_error(self):
        fake = Mock()
        fake.status_code = 404
        fake.ok = False
        fake.text = "Not Found"
        with patch("weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APIRequestError):
                weather_service.get_weather()

    def test_invalid_json_raises_api_request_error(self):
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.text = "not json"
        fake.json.side_effect = ValueError("invalid json")
        with patch("weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APIRequestError):
                weather_service.get_weather()

    def test_missing_env_raises_env_not_found(self):
        # Simulate missing .env by forcing load_dotenv to raise
        with patch("weather_service.load_dotenv", side_effect=weather_service.EnvNotFoundError()):
            with self.assertRaises(weather_service.EnvNotFoundError):
                weather_service.get_weather()


if __name__ == "__main__":
    unittest.main()