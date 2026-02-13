from pathlib import Path
from unittest.mock import Mock, patch
import os

import pytest

import services.config as config
import services.weather_service as weather_service


class TestEnvLoading:
    def test_parse_env_lines_filters_comments_and_blank_lines(self):
        lines = [
            "# comment",
            "",
            " URL = https://api.example.test/forecast ",
            "API_KEY = abc123",
            "INVALID_LINE_WITHOUT_EQUALS",
        ]

        parsed = weather_service._parse_env_lines(lines)

        assert parsed == {
            "URL": "https://api.example.test/forecast",
            "API_KEY": "abc123",
        }

    def test_default_env_paths_adds_android_hints_once(self):
        env_values = {"ANDROID_ARGUMENT": "/tmp/p4a", "ANDROID_PRIVATE": "/tmp/p4a"}
        with patch(
            "services.weather_service.os.getenv",
            side_effect=lambda key: env_values.get(key),
        ):
            paths = weather_service._default_env_paths()

        as_strings = [str(path) for path in paths]
        assert as_strings.count(str(Path("/tmp/p4a/.env"))) == 1
        assert as_strings.count(str(Path("/tmp/p4a/app/.env"))) == 1

    def test_load_dotenv_from_explicit_path_updates_environment(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text(
            "URL=https://api.example.test/forecast\nAPI_KEY=test-key\n",
            encoding="utf-8",
        )

        with patch.dict(os.environ, {}, clear=True):
            loaded = weather_service.load_dotenv(str(env_file))
            assert os.environ["URL"] == "https://api.example.test/forecast"
            assert os.environ["API_KEY"] == "test-key"

        assert loaded["URL"] == "https://api.example.test/forecast"
        assert loaded["API_KEY"] == "test-key"

    def test_load_dotenv_missing_explicit_path_raises(self, tmp_path):
        missing_path = tmp_path / "missing.env"
        with pytest.raises(weather_service.EnvNotFoundError):
            weather_service.load_dotenv(str(missing_path))

    def test_load_dotenv_uses_android_assets_when_files_missing(self):
        asset_env = {"URL": "https://asset.example/api", "API_KEY": "asset-key"}
        with patch(
            "services.weather_service._default_env_paths",
            return_value=[Path("/does/not/exist/.env")],
        ):
            with patch(
                "services.weather_service._load_dotenv_from_android_assets",
                return_value=asset_env,
            ):
                with patch.dict(os.environ, {}, clear=True):
                    loaded = weather_service.load_dotenv()
                    assert os.environ["URL"] == "https://asset.example/api"
                    assert os.environ["API_KEY"] == "asset-key"

        assert loaded == asset_env

    def test_load_dotenv_without_any_source_raises(self):
        with patch(
            "services.weather_service._default_env_paths",
            return_value=[Path("/still/missing/.env")],
        ):
            with patch(
                "services.weather_service._load_dotenv_from_android_assets",
                return_value=None,
            ):
                with pytest.raises(weather_service.EnvNotFoundError):
                    weather_service.load_dotenv()

    def test_android_asset_loader_returns_none_if_pyjnius_missing(self):
        real_import = __import__

        def fake_import(name, *args, **kwargs):
            if name == "jnius":
                raise ImportError("pyjnius missing in tests")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=fake_import):
            assert weather_service._load_dotenv_from_android_assets() is None


class TestConfigResolution:
    def test_get_config_prefers_process_environment(self):
        with patch.dict(
            os.environ,
            {"URL": "https://env.example/api", "API_KEY": "env-key"},
            clear=True,
        ):
            url, api_key = weather_service._get_config()

        assert url == "https://env.example/api"
        assert api_key == "env-key"

    def test_get_config_loads_dotenv_when_environment_is_empty(self):
        def fake_load_dotenv():
            os.environ["URL"] = "https://dotenv.example/api"
            os.environ["API_KEY"] = "dotenv-key"
            return {"URL": os.environ["URL"], "API_KEY": os.environ["API_KEY"]}

        with patch.dict(os.environ, {}, clear=True):
            with patch("services.weather_service.load_dotenv", side_effect=fake_load_dotenv):
                url, api_key = weather_service._get_config()

        assert url == "https://dotenv.example/api"
        assert api_key == "dotenv-key"

    def test_get_config_uses_config_fallback_when_dotenv_is_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "services.weather_service.load_dotenv",
                side_effect=weather_service.EnvNotFoundError("missing"),
            ):
                with patch.object(config, "URL", "https://config.example/api"):
                    with patch.object(config, "API_KEY", "config-key"):
                        url, api_key = weather_service._get_config()

        assert url == "https://config.example/api"
        assert api_key == "config-key"

    def test_get_config_raises_when_all_sources_are_missing(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "services.weather_service.load_dotenv",
                side_effect=weather_service.EnvNotFoundError("missing"),
            ):
                with patch.object(config, "URL", ""):
                    with patch.object(config, "API_KEY", ""):
                        with pytest.raises(weather_service.MissingAPIConfigError):
                            weather_service._get_config()


class TestUrlAndCacheHelpers:
    def test_build_request_url_sets_appid_and_coordinates(self):
        built = weather_service.build_request_url(
            "https://api.example.test/forecast?units=metric",
            "my-api-key",
            lat=48.5,
            lon=7.9,
        )

        assert "appid=my-api-key" in built
        assert "units=metric" in built
        assert "lat=48.5" in built
        assert "lon=7.9" in built

    def test_get_weather_cache_path_points_to_expected_file(self):
        cache_path = weather_service._get_weather_cache_path()
        expected_suffix = Path("src") / "json" / "last_weather.json"
        assert str(cache_path).endswith(str(expected_suffix))

    def test_save_and_load_weather_cache_roundtrip(self, tmp_path):
        cache_file = tmp_path / "json" / "last_weather.json"
        payload = {"cod": "200", "list": [{"main": {"temp": 280}}]}

        with patch("services.weather_service._get_weather_cache_path", return_value=cache_file):
            weather_service._save_weather_cache(payload)
            loaded = weather_service._load_weather_cache()

        assert loaded == payload

    def test_load_weather_cache_returns_none_when_file_is_missing(self, tmp_path):
        cache_file = tmp_path / "json" / "does-not-exist.json"

        with patch("services.weather_service._get_weather_cache_path", return_value=cache_file):
            loaded = weather_service._load_weather_cache()

        assert loaded is None


class TestFetchJson:
    @staticmethod
    def _response(
        status_code=200,
        ok=True,
        payload=None,
        text="",
    ):
        fake = Mock()
        fake.status_code = status_code
        fake.ok = ok
        fake.text = text
        if payload is None:
            payload = {"cod": "200", "list": []}
        fake.json.return_value = payload
        return fake

    def test_fetch_json_raises_network_error_on_timeout(self):
        with patch(
            "services.weather_service.requests.get",
            side_effect=weather_service.requests.Timeout(),
        ):
            with pytest.raises(weather_service.NetworkError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_raises_api_token_error_on_401(self):
        response = self._response(status_code=401, ok=False, text="Unauthorized")
        with patch("services.weather_service.requests.get", return_value=response):
            with pytest.raises(weather_service.APITokenExpiredError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_raises_service_unavailable_on_5xx(self):
        response = self._response(status_code=503, ok=False, text="Service unavailable")
        with patch("services.weather_service.requests.get", return_value=response):
            with pytest.raises(weather_service.ServiceUnavailableError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_raises_api_request_error_on_non_ok_4xx(self):
        response = self._response(status_code=404, ok=False, text="Not found")
        with patch("services.weather_service.requests.get", return_value=response):
            with pytest.raises(weather_service.APIRequestError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_raises_api_request_error_on_invalid_json(self):
        response = self._response()
        response.json.side_effect = ValueError("invalid json")
        with patch("services.weather_service.requests.get", return_value=response):
            with pytest.raises(weather_service.APIRequestError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_raises_api_request_error_on_payload_cod_error(self):
        response = self._response(payload={"cod": "404", "message": "city not found"})
        with patch("services.weather_service.requests.get", return_value=response):
            with pytest.raises(weather_service.APIRequestError):
                weather_service.fetch_json("https://api.example.test/forecast")

    def test_fetch_json_returns_payload_and_saves_cache_on_success(self):
        payload = {"cod": "200", "list": [{"main": {"temp": 295}}]}
        response = self._response(payload=payload)
        with patch("services.weather_service.requests.get", return_value=response):
            with patch("services.weather_service._save_weather_cache") as save_cache:
                result = weather_service.fetch_json("https://api.example.test/forecast")

        assert result == payload
        save_cache.assert_called_once_with(payload)


class TestGetWeather:
    def test_get_weather_builds_url_and_returns_fetch_result(self):
        with patch(
            "services.weather_service._get_config",
            return_value=("https://api.example.test/forecast", "key-123"),
        ):
            with patch(
                "services.weather_service.build_request_url",
                return_value="https://api.example.test/forecast?appid=key-123&lat=1&lon=2",
            ) as build_url:
                with patch(
                    "services.weather_service.fetch_json",
                    return_value={"cod": "200", "list": []},
                ) as fetch_json:
                    result = weather_service.get_weather(lat=1, lon=2)

        assert result == {"cod": "200", "list": []}
        build_url.assert_called_once_with(
            "https://api.example.test/forecast",
            "key-123",
            lat=1,
            lon=2,
        )
        fetch_json.assert_called_once()

    def test_get_weather_returns_cached_payload_when_fetch_fails(self):
        with patch(
            "services.weather_service._get_config",
            return_value=("https://api.example.test/forecast", "key-123"),
        ):
            with patch(
                "services.weather_service.fetch_json",
                side_effect=weather_service.NetworkError("offline"),
            ):
                with patch(
                    "services.weather_service._load_weather_cache",
                    return_value={"cod": "200", "list": [{"main": {"temp": 300}}]},
                ):
                    result = weather_service.get_weather()

        assert result["__cached__"] is True
        assert result["cod"] == "200"

    def test_get_weather_reraises_original_error_when_cache_is_missing(self):
        with patch(
            "services.weather_service._get_config",
            return_value=("https://api.example.test/forecast", "key-123"),
        ):
            with patch(
                "services.weather_service.fetch_json",
                side_effect=weather_service.APIRequestError("bad request"),
            ):
                with patch("services.weather_service._load_weather_cache", return_value=None):
                    with pytest.raises(weather_service.APIRequestError):
                        weather_service.get_weather()
