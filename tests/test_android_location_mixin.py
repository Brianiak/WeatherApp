import sys
import types
from unittest.mock import Mock, patch

from app_mixins.android_location import AndroidLocationMixin


class DummyTimeoutEvent:
    def __init__(self):
        self.canceled = False

    def cancel(self):
        self.canceled = True


class DummyAndroidApp(AndroidLocationMixin):
    GPS_TIMEOUT = 45

    def __init__(self):
        self._gps_timeout_event = None
        self.current_lat = None
        self.current_lon = None
        self._location_manager = None
        self._location_listener = object()
        self._has_live_gps_fix = False
        self.fallback_reasons = []
        self.labels = []
        self.apply_calls = []

    def _use_last_known_location_or_default(self, reason):
        self.fallback_reasons.append(reason)

    def _coordinates_in_range(self, lat, lon):
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0

    def _set_location_labels(self, label):
        self.labels.append(label)

    def _apply_location(self, lat, lon, track_as_gps=False, force_refresh=False):
        self.current_lat = lat
        self.current_lon = lon
        self.apply_calls.append(
            {
                "lat": lat,
                "lon": lon,
                "track_as_gps": track_as_gps,
                "force_refresh": force_refresh,
            }
        )


def _install_fake_android_permissions_module(check_permission_result=False):
    android_module = types.ModuleType("android")
    permissions_module = types.ModuleType("android.permissions")

    class Permission:
        ACCESS_COARSE_LOCATION = "coarse"
        ACCESS_FINE_LOCATION = "fine"

    calls = {"requested": None}

    def check_permission(_permission):
        return check_permission_result

    def request_permissions(required, callback):
        calls["requested"] = (required, callback)

    permissions_module.Permission = Permission
    permissions_module.check_permission = check_permission
    permissions_module.request_permissions = request_permissions
    android_module.permissions = permissions_module

    return {"android": android_module, "android.permissions": permissions_module}, calls


class TestAndroidLocationMixin:
    def test_start_android_location_flow_starts_gps_when_permission_exists(self):
        app = DummyAndroidApp()
        modules, _calls = _install_fake_android_permissions_module(check_permission_result=True)

        with patch.dict(sys.modules, modules):
            with patch.object(app, "_start_gps") as start_gps:
                app._start_android_location_flow()

        start_gps.assert_called_once()

    def test_start_android_location_flow_requests_permissions_when_missing(self):
        app = DummyAndroidApp()
        modules, calls = _install_fake_android_permissions_module(check_permission_result=False)

        with patch.dict(sys.modules, modules):
            app._start_android_location_flow()

        assert calls["requested"] is not None
        required, callback = calls["requested"]
        assert "coarse" in required
        assert "fine" in required
        assert callback == app._on_android_permissions_result

    def test_start_android_location_flow_falls_back_on_import_error(self):
        app = DummyAndroidApp()
        with patch.dict(sys.modules, {}, clear=True):
            app._start_android_location_flow()

        assert "android permission flow failed" in app.fallback_reasons[-1]

    def test_on_android_permissions_result_granted_starts_gps(self):
        app = DummyAndroidApp()
        with patch.object(app, "_start_gps") as start_gps:
            app._on_android_permissions_result(["coarse", "fine"], [1, 0])
        start_gps.assert_called_once()

    def test_on_android_permissions_result_denied_uses_fallback(self):
        app = DummyAndroidApp()
        app._on_android_permissions_result(["coarse", "fine"], [0, 0])
        assert "location permission denied" in app.fallback_reasons[-1]

    def test_start_gps_non_android_platform_uses_fallback(self):
        app = DummyAndroidApp()
        with patch("app_mixins.android_location.kivy_platform", "win"):
            app._start_gps()
        assert "GPS not available on this platform" in app.fallback_reasons[-1]

    def test_start_gps_without_pyjnius_uses_fallback(self):
        app = DummyAndroidApp()
        with patch("app_mixins.android_location.kivy_platform", "android"):
            with patch("app_mixins.android_location.autoclass", None):
                app._start_gps()
        assert "pyjnius unavailable" in app.fallback_reasons[-1]

    def test_start_gps_initializes_and_schedules_timeout(self):
        app = DummyAndroidApp()
        timeout_event = DummyTimeoutEvent()

        with patch("app_mixins.android_location.kivy_platform", "android"):
            with patch("app_mixins.android_location.autoclass", object()):
                with patch.object(app, "_init_android_location_manager") as init_manager:
                    with patch.object(app, "_start_android_location_updates") as start_updates:
                        with patch(
                            "app_mixins.android_location.Clock.schedule_once",
                            return_value=timeout_event,
                        ) as schedule_once:
                            app._start_gps()

        init_manager.assert_called_once()
        start_updates.assert_called_once()
        schedule_once.assert_called_once()
        assert app._gps_timeout_event is timeout_event

    def test_start_gps_does_not_reinit_when_location_manager_exists(self):
        app = DummyAndroidApp()
        app._location_manager = object()

        with patch("app_mixins.android_location.kivy_platform", "android"):
            with patch("app_mixins.android_location.autoclass", object()):
                with patch.object(app, "_init_android_location_manager") as init_manager:
                    with patch.object(app, "_start_android_location_updates"):
                        with patch("app_mixins.android_location.Clock.schedule_once"):
                            app._start_gps()

        init_manager.assert_not_called()

    def test_start_gps_uses_fallback_on_internal_error(self):
        app = DummyAndroidApp()
        with patch("app_mixins.android_location.kivy_platform", "android"):
            with patch("app_mixins.android_location.autoclass", object()):
                with patch.object(
                    app,
                    "_init_android_location_manager",
                    side_effect=RuntimeError("boom"),
                ):
                    app._start_gps()
        assert "failed to start GPS" in app.fallback_reasons[-1]

    def test_init_android_location_manager_raises_when_activity_is_none(self):
        app = DummyAndroidApp()

        class FakePythonActivity:
            mActivity = None

        class FakeContext:
            LOCATION_SERVICE = "location"

        def fake_autoclass(name):
            if name == "org.kivy.android.PythonActivity":
                return FakePythonActivity
            if name == "android.content.Context":
                return FakeContext
            raise AssertionError(name)

        with patch("app_mixins.android_location.autoclass", side_effect=fake_autoclass):
            with patch("app_mixins.android_location.PythonJavaClass", object):
                with patch(
                    "app_mixins.android_location.java_method",
                    side_effect=lambda _sig: (lambda fn: fn),
                ):
                    with patch("app_mixins.android_location.Clock.schedule_once"):
                        try:
                            app._init_android_location_manager()
                        except RuntimeError as exc:
                            assert "mActivity is None" in str(exc)
                        else:
                            raise AssertionError("RuntimeError expected")

    def test_init_android_location_manager_sets_manager_and_listener(self):
        app = DummyAndroidApp()
        fake_location_manager = object()

        class FakeActivity:
            def getSystemService(self, _service_name):
                return fake_location_manager

        class FakePythonActivity:
            mActivity = FakeActivity()

        class FakeContext:
            LOCATION_SERVICE = "location"

        def fake_autoclass(name):
            if name == "org.kivy.android.PythonActivity":
                return FakePythonActivity
            if name == "android.content.Context":
                return FakeContext
            raise AssertionError(name)

        with patch("app_mixins.android_location.autoclass", side_effect=fake_autoclass):
            with patch("app_mixins.android_location.PythonJavaClass", object):
                with patch(
                    "app_mixins.android_location.java_method",
                    side_effect=lambda _sig: (lambda fn: fn),
                ):
                    with patch("app_mixins.android_location.Clock.schedule_once"):
                        app._init_android_location_manager()

        assert app._location_manager is fake_location_manager
        assert app._location_listener is not None

    def test_enabled_android_providers_returns_only_enabled(self):
        app = DummyAndroidApp()
        app._location_manager = Mock()

        class FakeLocationManager:
            GPS_PROVIDER = "gps"
            NETWORK_PROVIDER = "network"

        app._location_manager.isProviderEnabled.side_effect = lambda provider: provider == "gps"

        with patch("app_mixins.android_location.autoclass", return_value=FakeLocationManager):
            providers = app._enabled_android_providers()

        assert providers == ["gps"]

    def test_start_android_location_updates_raises_without_enabled_providers(self):
        app = DummyAndroidApp()
        app._location_manager = Mock()

        with patch("app_mixins.android_location.autoclass", return_value=object()):
            with patch.object(app, "_enabled_android_providers", return_value=[]):
                try:
                    app._start_android_location_updates()
                except RuntimeError as exc:
                    assert "No enabled Android location providers" in str(exc)
                else:
                    raise AssertionError("RuntimeError expected")

    def test_start_android_location_updates_requests_updates_and_emits_last_known(self):
        app = DummyAndroidApp()
        app._location_manager = Mock()
        app._location_listener = object()

        class FakeLooper:
            @staticmethod
            def getMainLooper():
                return "main-looper"

        with patch("app_mixins.android_location.autoclass", return_value=FakeLooper):
            with patch.object(app, "_enabled_android_providers", return_value=["gps", "network"]):
                with patch.object(app, "_emit_android_last_known_location") as emit_last_known:
                    app._start_android_location_updates()

        assert app._location_manager.requestLocationUpdates.call_count == 2
        emit_last_known.assert_called_once_with(["gps", "network"])

    def test_emit_android_last_known_location_uses_first_valid_provider(self):
        app = DummyAndroidApp()
        app._location_manager = Mock()

        class FakeLocation:
            def getLatitude(self):
                return 50.1

            def getLongitude(self):
                return 8.6

            def getAccuracy(self):
                return 12.0

        app._location_manager.getLastKnownLocation.side_effect = [FakeLocation(), FakeLocation()]

        with patch.object(app, "on_gps_location") as on_gps_location:
            app._emit_android_last_known_location(["gps", "network"])

        on_gps_location.assert_called_once()
        kwargs = on_gps_location.call_args.kwargs
        assert kwargs["lat"] == 50.1
        assert kwargs["lon"] == 8.6
        assert kwargs["provider"] == "gps"

    def test_gps_timeout_fallback_uses_fallback_when_no_fix(self):
        app = DummyAndroidApp()
        app.current_lat = None
        app.current_lon = None
        app._gps_timeout_fallback(0)
        assert app._gps_timeout_event is None
        assert "GPS timeout" in app.fallback_reasons[-1]

    def test_gps_timeout_fallback_does_nothing_when_fix_exists(self):
        app = DummyAndroidApp()
        app.current_lat = 50.0
        app.current_lon = 8.0
        app._gps_timeout_fallback(0)
        assert app.fallback_reasons == []

    def test_on_gps_status_triggers_fallback_on_degraded_status(self):
        app = DummyAndroidApp()
        app.on_gps_status("provider", "gps disabled")
        assert "GPS status: gps disabled" in app.fallback_reasons[-1]

    def test_on_gps_status_ignores_non_degraded_status(self):
        app = DummyAndroidApp()
        app.on_gps_status("provider", "gps enabled")
        assert app.fallback_reasons == []

    def test_on_gps_location_without_coordinates_uses_fallback(self):
        app = DummyAndroidApp()
        app.on_gps_location(provider="gps")
        assert "GPS update without coordinates" in app.fallback_reasons[-1]

    def test_on_gps_location_with_invalid_coordinates_uses_fallback(self):
        app = DummyAndroidApp()
        app.on_gps_location(lat="x", lon="y")
        assert "invalid GPS coordinates" in app.fallback_reasons[-1]

    def test_on_gps_location_with_out_of_range_coordinates_uses_fallback(self):
        app = DummyAndroidApp()
        app.on_gps_location(lat=100.0, lon=8.0)
        assert "out-of-range GPS coordinates" in app.fallback_reasons[-1]

    def test_on_gps_location_first_fix_sets_force_refresh_true(self):
        app = DummyAndroidApp()
        timeout_event = DummyTimeoutEvent()
        app._gps_timeout_event = timeout_event

        app.on_gps_location(lat=49.5, lon=8.4, accuracy=5.0, provider="gps")

        assert timeout_event.canceled is True
        assert app._gps_timeout_event is None
        assert app._has_live_gps_fix is True
        assert app.labels[-1] == "GPS erkannt, Standort wird geladen..."
        assert app.apply_calls[-1]["track_as_gps"] is True
        assert app.apply_calls[-1]["force_refresh"] is True

    def test_on_gps_location_second_fix_sets_force_refresh_false(self):
        app = DummyAndroidApp()
        app._has_live_gps_fix = True

        app.on_gps_location(lat=49.5, lon=8.4, provider="gps")

        assert app.apply_calls[-1]["track_as_gps"] is True
        assert app.apply_calls[-1]["force_refresh"] is False

    def test_on_stop_removes_updates_on_android(self):
        app = DummyAndroidApp()
        app._location_manager = Mock()
        app._location_listener = object()

        with patch("app_mixins.android_location.kivy_platform", "android"):
            app.on_stop()

        app._location_manager.removeUpdates.assert_called_once_with(app._location_listener)

    def test_on_stop_ignores_exceptions(self):
        app = DummyAndroidApp()
        manager = Mock()
        manager.removeUpdates.side_effect = RuntimeError("ignored")
        app._location_manager = manager
        app._location_listener = object()

        with patch("app_mixins.android_location.kivy_platform", "android"):
            app.on_stop()
