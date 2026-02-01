# WeatherApp

WeatherApp is a simple Kivy-based desktop UI that presents a clean, card-style weather overview.
It focuses on layout and navigation rather than live data, and ships with sample values and icons.

## What the app does
- Shows three views: Today, Tomorrow, and a 7‑day forecast.
- Displays location, temperature, condition, humidity, and wind for “Today”.
- Shows min/max temperature and day‑part breakdown for “Tomorrow”.
- Lists a 7‑day forecast with icons and per‑day morning/midday/evening/night temperatures.
- Adapts the card width to the window size for a responsive layout.

## Notes
- Data is currently hardcoded in `src/main.py` for demonstration.
- UI layout and styling live in `src/weather.kv`.
