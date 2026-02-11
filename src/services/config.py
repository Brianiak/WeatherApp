"""Fallback configuration for the WeatherApp.

This file is always bundled with the APK (as a .py file) and serves as
a reliable fallback when the .env file cannot be found on Android.

The GitHub Actions workflow overwrites this file with the real API key
from secrets before building the APK.
"""

# These values are overwritten by GitHub Actions during the build process.
# For local development, the .env file in the project root takes precedence.
URL = "https://api.openweathermap.org/data/2.5/forecast"
API_KEY = "afc49071bebd69a40a5b62a625cbfdc1"
