"""
Main entry point for the WeatherApp Android application.

This wrapper file serves as the entry point for Buildozer/python-for-android.
It adds the src directory to the Python path and imports the actual application.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path so all imports work correctly
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import and run the actual application from src/main.py
if __name__ == "__main__":
    from main import WeatherApp
    WeatherApp().run()
