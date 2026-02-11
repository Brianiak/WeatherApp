"""Fallback configuration for the WeatherApp.

This file is bundled with the APK (as a .py file) and can be used as
fallback when the `.env` file cannot be read at runtime.

Primary configuration should be provided via `.env` (`URL`, `API_KEY`).
"""

# Keep as fallback only; .env takes precedence in weather_service._get_config().
URL = "https://api.openweathermap.org/data/2.5/forecast"
API_KEY = "afc49071bebd69a40a5b62a625cbfdc1"