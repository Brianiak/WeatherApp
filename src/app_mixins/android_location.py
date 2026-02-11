from kivy.clock import Clock
from kivy.utils import platform as kivy_platform

try:
    from jnius import autoclass, PythonJavaClass, java_method
except Exception:  # pragma: no cover - desktop/test environments
    autoclass = None
    PythonJavaClass = object

    def java_method(_signature):
        def decorator(func):
            return func

        return decorator


class AndroidLocationMixin:
    def _start_android_location_flow(self):
        try:
            from android.permissions import Permission, check_permission, request_permissions

            required = [Permission.ACCESS_COARSE_LOCATION, Permission.ACCESS_FINE_LOCATION]
            if any(check_permission(permission) for permission in required):
                self._start_gps()
                return

            request_permissions(required, self._on_android_permissions_result)
        except Exception as e:
            print("Android permission flow failed:", e)
            self._use_last_known_location_or_default("android permission flow failed")

    def _on_android_permissions_result(self, permissions, grants):
        grants = [bool(grant) for grant in grants]
        if any(grants):
            if not all(grants):
                print(
                    "Location permission partially granted "
                    "(coarse location only). Continuing with available precision."
                )
            self._start_gps()
            return

        print(f"Location permission denied: {list(zip(permissions, grants))}")
        self._use_last_known_location_or_default("location permission denied")

    def _start_gps(self):
        if kivy_platform != "android":
            print(f"GPS via pyjnius is Android-only (platform={kivy_platform}).")
            self._use_last_known_location_or_default("GPS not available on this platform")
            return

        if autoclass is None:
            print("pyjnius import failed; cannot start Android GPS.")
            self._use_last_known_location_or_default("pyjnius unavailable")
            return

        try:
            if self._location_manager is None:
                self._init_android_location_manager()
            self._start_android_location_updates()
            self._gps_timeout_event = Clock.schedule_once(
                self._gps_timeout_fallback, self.GPS_TIMEOUT
            )
        except Exception as e:
            print("Failed to start GPS:", e)
            self._use_last_known_location_or_default("failed to start GPS")

    def _init_android_location_manager(self):
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity
        if activity is None:
            raise RuntimeError("PythonActivity.mActivity is None")

        self._location_manager = activity.getSystemService(Context.LOCATION_SERVICE)
        if self._location_manager is None:
            raise RuntimeError("Could not obtain Android LocationManager")

        app_ref = self

        class AndroidLocationListener(PythonJavaClass):
            __javainterfaces__ = ["android/location/LocationListener"]
            __javacontext__ = "app"

            def __init__(self):
                super().__init__()

            @java_method("(Landroid/location/Location;)V")
            def onLocationChanged(self, location):
                if location is None:
                    return

                lat = float(location.getLatitude())
                lon = float(location.getLongitude())
                provider = str(location.getProvider()) if location.getProvider() else "unknown"
                try:
                    accuracy = float(location.getAccuracy())
                except Exception:
                    accuracy = None

                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_location(
                        lat=lat,
                        lon=lon,
                        accuracy=accuracy,
                        provider=provider,
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;)V")
            def onProviderDisabled(self, provider):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "provider", f"{provider_name} disabled"
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;)V")
            def onProviderEnabled(self, provider):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "provider", f"{provider_name} enabled"
                    ),
                    0,
                )

            @java_method("(Ljava/lang/String;ILandroid/os/Bundle;)V")
            def onStatusChanged(self, provider, status, extras):
                provider_name = str(provider)
                Clock.schedule_once(
                    lambda _dt: app_ref.on_gps_status(
                        "status", f"{provider_name} status={status}"
                    ),
                    0,
                )

        self._location_listener = AndroidLocationListener()

    def _enabled_android_providers(self) -> list[str]:
        LocationManager = autoclass("android.location.LocationManager")
        providers: list[str] = []
        for provider in (LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER):
            try:
                if self._location_manager.isProviderEnabled(provider):
                    providers.append(provider)
            except Exception as e:
                print(f"Could not query provider '{provider}': {e}")
        return providers

    def _start_android_location_updates(self):
        Looper = autoclass("android.os.Looper")
        providers = self._enabled_android_providers()
        if not providers:
            raise RuntimeError("No enabled Android location providers (GPS/NETWORK)")

        print(f"Starting Android location updates via providers: {providers}")
        for provider in providers:
            self._location_manager.requestLocationUpdates(
                provider,
                1000,
                0.0,
                self._location_listener,
                Looper.getMainLooper(),
            )

        self._emit_android_last_known_location(providers)

    def _emit_android_last_known_location(self, providers: list[str]):
        for provider in providers:
            try:
                last = self._location_manager.getLastKnownLocation(provider)
            except Exception as e:
                print(f"Could not read last known location for provider '{provider}': {e}")
                continue

            if last is None:
                continue

            try:
                lat = float(last.getLatitude())
                lon = float(last.getLongitude())
            except Exception as e:
                print(f"Invalid last known location from provider '{provider}': {e}")
                continue

            try:
                accuracy = float(last.getAccuracy())
            except Exception:
                accuracy = None

            print(
                "Using Android last known location from provider "
                f"'{provider}': lat={lat:.6f}, lon={lon:.6f}, accuracy={accuracy}"
            )
            self.on_gps_location(lat=lat, lon=lon, accuracy=accuracy, provider=provider)
            return

    def _gps_timeout_fallback(self, _dt):
        self._gps_timeout_event = None
        if self.current_lat is None or self.current_lon is None:
            print(
                f"GPS timeout after {self.GPS_TIMEOUT}s with no fix. "
                "Falling back to last known location."
            )
            self._use_last_known_location_or_default("GPS timeout")

    def on_gps_status(self, stype, status):
        print(f"GPS status: type={stype}, status={status}")
        status_text = str(status).lower()
        degraded = ("disabled", "out of service", "unavailable", "denied")
        if any(marker in status_text for marker in degraded):
            self._use_last_known_location_or_default(f"GPS status: {status}")

    def on_gps_location(self, **kwargs):
        if self._gps_timeout_event:
            self._gps_timeout_event.cancel()
            self._gps_timeout_event = None

        lat = kwargs.get("lat")
        lon = kwargs.get("lon")
        if lat is None or lon is None:
            print(f"Ignoring GPS update without coordinates: {kwargs}")
            self._use_last_known_location_or_default("GPS update without coordinates")
            return

        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            print(f"Ignoring invalid GPS coordinates: lat={lat}, lon={lon}")
            self._use_last_known_location_or_default("invalid GPS coordinates")
            return

        if not self._coordinates_in_range(lat, lon):
            print(f"Ignoring out-of-range GPS coordinates: lat={lat}, lon={lon}")
            self._use_last_known_location_or_default("out-of-range GPS coordinates")
            return

        accuracy = kwargs.get("accuracy")
        if accuracy is not None:
            print(f"GPS parsed coordinates: lat={lat:.6f}, lon={lon:.6f}, accuracy={accuracy}")
        else:
            print(f"GPS parsed coordinates: lat={lat:.6f}, lon={lon:.6f}")

        print("GPS location:", kwargs)
        is_first_live_fix = not self._has_live_gps_fix
        self._has_live_gps_fix = True
        self._set_location_labels("GPS erkannt, Standort wird geladen...")
        self._apply_location(
            lat,
            lon,
            track_as_gps=True,
            force_refresh=is_first_live_fix,
        )

    def on_stop(self):
        try:
            if (
                kivy_platform == "android"
                and self._location_manager
                and self._location_listener
            ):
                self._location_manager.removeUpdates(self._location_listener)
                print("Stopped Android location updates.")
        except Exception:
            pass
