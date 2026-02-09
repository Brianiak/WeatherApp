import sys
import os
import unittest
from unittest.mock import patch, Mock
from pathlib import Path

import coverage
import services.weather_service as weather_service

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Initialize coverage
cov = coverage.Coverage()

class TestWeatherService(unittest.TestCase):
    """Unit tests for `weather_service` that mock network calls.

    These tests mock `requests.get` so no real API tokens are consumed.
    """

    def setUp(self):
        # Ensure environment variables exist for the service to read.
        # Prevent the real .env from being loaded during tests
        self.patcher = patch("services.weather_service.load_dotenv", return_value={})
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

        with patch("services.weather_service.requests.get", return_value=fake) as mock_get:
            data = weather_service.get_weather()
            self.assertEqual(data, {"ok": True})
            # Verify the called URL contains the expected appid (API key)
            _, kwargs = mock_get.call_args
            called_url = kwargs.get("url")
            self.assertIsNotNone(called_url)
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(called_url)
            query = parse_qs(parsed.query)
            self.assertEqual(query.get("appid", [None])[0], "TESTKEY")

    def test_network_error_raises(self):
        with patch("services.weather_service.requests.get", side_effect=weather_service.requests.ConnectionError("x")):
            with self.assertRaises(weather_service.NetworkError):
                weather_service.get_weather()

    def test_401_raises_token_error(self):
        fake = Mock()
        fake.status_code = 401
        fake.ok = False
        fake.text = "Unauthorized"
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APITokenExpiredError):
                weather_service.get_weather()

    def test_5xx_raises_service_unavailable(self):
        fake = Mock()
        fake.status_code = 503
        fake.ok = False
        fake.text = "Service Unavailable"
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.ServiceUnavailableError):
                weather_service.get_weather()

    def test_4xx_raises_api_request_error(self):
        fake = Mock()
        fake.status_code = 404
        fake.ok = False
        fake.text = "Not Found"
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APIRequestError):
                weather_service.get_weather()

    def test_invalid_json_raises_api_request_error(self):
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.text = "not json"
        fake.json.side_effect = ValueError("invalid json")
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APIRequestError):
                weather_service.get_weather()

    def test_missing_env_raises_env_not_found(self):
        # Simulate missing .env by forcing load_dotenv to raise
        with patch("services.weather_service.load_dotenv", side_effect=weather_service.EnvNotFoundError()):
            with self.assertRaises(weather_service.EnvNotFoundError):
                weather_service.get_weather()


# Dummy Tests for coverage


class TestBuildRequestUrl(unittest.TestCase):
    """Tests for build_request_url function"""

    def test_build_request_url_with_lat_lon(self):
        """Test building URL with latitude and longitude"""
        url = "https://api.example.com/forecast"
        api_key = "testkey123"
        result = weather_service.build_request_url(url, api_key, lat=48.5, lon=7.9)
        
        self.assertIn("appid=testkey123", result)
        self.assertIn("lat=48.5", result)
        self.assertIn("lon=7.9", result)

    def test_build_request_url_without_coordinates(self):
        """Test building URL without coordinates"""
        url = "https://api.example.com/forecast"
        api_key = "testkey456"
        result = weather_service.build_request_url(url, api_key)
        
        self.assertIn("appid=testkey456", result)
        self.assertNotIn("lat=", result)
        self.assertNotIn("lon=", result)

    def test_build_request_url_with_existing_params(self):
        """Test building URL when base URL already has query params"""
        url = "https://api.example.com/forecast?units=metric"
        api_key = "testkey789"
        result = weather_service.build_request_url(url, api_key, lat=10.0, lon=20.0)
        
        self.assertIn("appid=testkey789", result)
        self.assertIn("units=metric", result)
        self.assertIn("lat=10.0", result)
        self.assertIn("lon=20.0", result)

    def test_build_request_url_with_string_coordinates(self):
        """Test building URL with string coordinates"""
        url = "https://api.example.com/forecast"
        api_key = "stringkey"
        result = weather_service.build_request_url(url, api_key, lat="51.5", lon="-0.1")
        
        self.assertIn("lat=51.5", result)
        self.assertIn("lon=-0.1", result)


class TestFetchJson(unittest.TestCase):
    """Tests for fetch_json function"""

    def test_fetch_json_timeout_raises_network_error(self):
        """Test that timeout raises NetworkError"""
        with patch("services.weather_service.requests.get", side_effect=weather_service.requests.Timeout()):
            with self.assertRaises(weather_service.NetworkError):
                weather_service.fetch_json("http://example.com/api")

    def test_fetch_json_success_with_valid_json(self):
        """Test successful fetch with valid JSON response"""
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.json.return_value = {"temp": 20, "humidity": 65}
        
        with patch("services.weather_service.requests.get", return_value=fake):
            result = weather_service.fetch_json("http://example.com/api")
            self.assertEqual(result, {"temp": 20, "humidity": 65})

    def test_fetch_json_custom_timeout(self):
        """Test that custom timeout is passed to requests"""
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.json.return_value = {}
        
        with patch("services.weather_service.requests.get", return_value=fake) as mock_get:
            weather_service.fetch_json("http://example.com/api", timeout=5)
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args[1]
            self.assertEqual(call_kwargs.get("timeout"), 5)


class TestLoadDotenv(unittest.TestCase):
    """Tests for load_dotenv function"""

    def test_load_dotenv_with_custom_path(self):
        """Test loading .env from custom path"""
        # Create a temporary .env content
        env_content = "TEST_VAR=test_value\nANOTHER_VAR=another_value"
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = env_content.split('\n')
            with patch("pathlib.Path.exists", return_value=True):
                result = weather_service.load_dotenv("/custom/path/.env")
                self.assertIn("TEST_VAR", result)

    def test_load_dotenv_ignores_comments(self):
        """Test that load_dotenv ignores lines starting with #"""
        env_lines = [
            "# This is a comment",
            "VALID_KEY=value",
            "# Another comment",
            "ANOTHER_KEY=another_value"
        ]
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = env_lines
            with patch("pathlib.Path.exists", return_value=True):
                result = weather_service.load_dotenv("/custom/.env")
                self.assertIn("VALID_KEY", result)
                self.assertIn("ANOTHER_KEY", result)
                self.assertEqual(len(result), 2)

    def test_load_dotenv_raises_on_missing_file(self):
        """Test that EnvNotFoundError is raised for missing .env"""
        with patch("pathlib.Path.exists", return_value=False):
            with self.assertRaises(weather_service.EnvNotFoundError):
                weather_service.load_dotenv("/nonexistent/.env")


class TestGetWeatherWithCoordinates(unittest.TestCase):
    """Tests for get_weather function with coordinates"""

    def setUp(self):
        self.patcher = patch("services.weather_service.load_dotenv", return_value={})
        self.patcher.start()
        os.environ.setdefault("URL", "http://example.com/api?key=")
        os.environ.setdefault("API_KEY", "TESTKEY")

    def tearDown(self):
        os.environ.pop("URL", None)
        os.environ.pop("API_KEY", None)
        self.patcher.stop()

    def test_get_weather_with_lat_lon(self):
        """Test get_weather with latitude and longitude"""
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.json.return_value = {"list": [{"main": {"temp": 290}}]}
        
        with patch("services.weather_service.requests.get", return_value=fake):
            result = weather_service.get_weather(lat=48.0, lon=7.0)
            self.assertIn("list", result)

    def test_get_weather_passes_coordinates_to_build_url(self):
        """Test that coordinates are passed through to build_request_url"""
        fake = Mock()
        fake.status_code = 200
        fake.ok = True
        fake.json.return_value = {}
        
        with patch("services.weather_service.requests.get", return_value=fake) as mock_get:
            weather_service.get_weather(lat=40.0, lon=-74.0)
            called_url = mock_get.call_args[1]["url"]
            self.assertIn("lat=40.0", called_url)
            self.assertIn("lon=-74.0", called_url)


class TestErrorHandling(unittest.TestCase):
    """Tests for error handling"""

    def setUp(self):
        self.patcher = patch("services.weather_service.load_dotenv", return_value={})
        self.patcher.start()
        os.environ.setdefault("URL", "http://example.com/api?key=")
        os.environ.setdefault("API_KEY", "TESTKEY")

    def tearDown(self):
        os.environ.pop("URL", None)
        os.environ.pop("API_KEY", None)
        self.patcher.stop()

    def test_missing_url_raises_error(self):
        """Test that missing URL raises MissingAPIConfigError"""
        os.environ.pop("URL")
        with self.assertRaises(weather_service.MissingAPIConfigError):
            weather_service.get_weather()

    def test_missing_api_key_raises_error(self):
        """Test that missing API_KEY raises MissingAPIConfigError"""
        os.environ.pop("API_KEY")
        with self.assertRaises(weather_service.MissingAPIConfigError):
            weather_service.get_weather()

    def test_400_bad_request_raises_error(self):
        """Test that 400 status code raises APIRequestError"""
        fake = Mock()
        fake.status_code = 400
        fake.ok = False
        fake.text = "Bad Request"
        
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.APIRequestError):
                weather_service.get_weather()

    def test_500_internal_error_raises_service_unavailable(self):
        """Test that 500 status raises ServiceUnavailableError"""
        fake = Mock()
        fake.status_code = 500
        fake.ok = False
        fake.text = "Internal Server Error"
        
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.ServiceUnavailableError):
                weather_service.get_weather()

    def test_502_bad_gateway_raises_service_unavailable(self):
        """Test that 502 status raises ServiceUnavailableError"""
        fake = Mock()
        fake.status_code = 502
        fake.ok = False
        fake.text = "Bad Gateway"
        
        with patch("services.weather_service.requests.get", return_value=fake):
            with self.assertRaises(weather_service.ServiceUnavailableError):
                weather_service.get_weather()

# ----


if __name__ == "__main__":
    unittest.main()