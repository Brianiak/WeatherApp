from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image


class ForecastRow(BoxLayout):
    """Forecast row widget displaying daily forecast information.
    
    Displays a single row in the 5-day forecast list with date, weather icon,
    min/max temperatures, and hourly temperature breakdown (morning, midday,
    evening, night).
    """
    
    date_text = StringProperty("")
    icon_source = StringProperty("")
    minmax_text = StringProperty("")
    dayparts_text = StringProperty("")


class ForecastIcon(Image):
    """Image widget that crops known weather icons to their visible content.

    OpenWeather PNG assets include different transparent paddings, which makes
    icons look misaligned although widget size is identical. This widget crops
    each icon texture to an empirically measured visible bounding box so all
    icons render with consistent apparent size in the 5-day list.
    """

    # Bounds are (left, top, right, bottom) in source pixel coordinates.
    _ICON_BOUNDS = {
        "01d": (13, 12, 36, 35),
        "01n": (14, 13, 40, 32),
        "02d": (8, 11, 46, 32),
        "02n": (5, 11, 43, 32),
        "03d": (8, 12, 42, 30),
        "03n": (8, 12, 42, 30),
        "04d": (5, 12, 46, 33),
        "04n": (5, 12, 46, 33),
        "09d": (5, 11, 47, 39),
        "09n": (5, 11, 47, 39),
        "10d": (6, 10, 43, 38),
        "10n": (5, 11, 43, 38),
        "11d": (4, 10, 46, 43),
        "11n": (4, 10, 46, 43),
        "13d": (5, 11, 47, 38),
        "13n": (5, 11, 47, 38),
        "50d": (6, 14, 40, 34),
        "50n": (6, 14, 40, 34),
    }
    _CROPPED_TEXTURE_CACHE = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._is_applying_crop = False

    def on_texture(self, *_args):
        """Replace raw icon texture with cached cropped region."""
        if self._is_applying_crop or not self.texture or not self.source:
            return

        icon_name = self.source.replace("\\", "/").rsplit("/", 1)[-1]
        icon_code = icon_name.split(".", 1)[0].lower()
        bounds = self._ICON_BOUNDS.get(icon_code)
        if not bounds:
            return

        tex_w, tex_h = int(self.texture.size[0]), int(self.texture.size[1])
        if tex_w <= 0 or tex_h <= 0:
            return

        left, top, right, bottom = bounds
        left = max(0, min(left, tex_w - 1))
        right = max(left, min(right, tex_w - 1))
        top = max(0, min(top, tex_h - 1))
        bottom = max(top, min(bottom, tex_h - 1))
        crop_w = right - left + 1
        crop_h = bottom - top + 1

        cache_key = (icon_code, tex_w, tex_h)
        cropped_texture = self._CROPPED_TEXTURE_CACHE.get(cache_key)
        if cropped_texture is None:
            y_from_bottom = tex_h - (bottom + 1)
            cropped_texture = self.texture.get_region(left, y_from_bottom, crop_w, crop_h)
            self._CROPPED_TEXTURE_CACHE[cache_key] = cropped_texture

        if self.texture is cropped_texture:
            return

        self._is_applying_crop = True
        try:
            self.texture = cropped_texture
        finally:
            self._is_applying_crop = False
