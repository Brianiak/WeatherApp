# WeatherApp Entwicklungsdokumentation

## Inhaltsverzeichnis
1. [Übersicht](#übersicht)
2. [Hauptanwendung](#hauptanwendung)
3. [Basisklassen](#basisklassen)
4. [Mixins](#mixins)
5. [Bildschirme](#bildschirme)
6. [UI-Komponenten](#ui-komponenten)
7. [Services](#services)
8. [Fehlerbehandlung](#fehlerbehandlung)

---

## Übersicht

WeatherApp ist eine Kivy-basierte mobile Wetterbeschaffungsanwendung, die aktuelle Wetterverhältnisse und 5-Tage-Vorhersagen mithilfe der OpenWeatherMap API anzeigt. Die App bietet GPS-basierte Standortverfolgung auf Android-Geräten mit Fallback-Caching-Mechanismen.

### Architektur
- **Kivy Framework**: Plattformübergreifendes UI-Framework für Desktop und Mobil
- **Mixin-Muster**: GPS-Standort, Caching und Wetter-Synchronisation in wiederverwendbare Mixins aufgeteilt
- **Screen Manager**: Navigation zwischen drei Hauptbildschirmen (Heute, Morgen, 5-Tage-Vorhersage)
- **OpenWeatherMap API**: Wetter-Daten-Backend

---

## Hauptanwendung

### `src/main.py`

#### Klasse: `WeatherApp`
Hauptanwendungsklasse, die GPS-Standort und Wetterdaten-Features kombiniert.

**Elternklassen:**
- `AndroidLocationMixin`: Android GPS-Handling
- `LocationCacheMixin`: Standort-Caching-Funktionalität
- `WeatherSyncMixin`: Wetter-Datensynchronisation
- `App`: Kivy-Anwendungsbasisklasse

**Attribute:**
- `kv_file` (str): Pfad zur KV-Layout-Datei
- `GPS_TIMEOUT` (int): GPS-Akquisitions-Timeout in Sekunden (45)
- `WEATHER_REFRESH_INTERVAL` (int): Wetter-API Refresh-Drosselintervall (60 Sekunden)
- `current_lat`, `current_lon` (float): Aktuelle Standortkoordinaten
- `last_gps_lat`, `last_gps_lon` (float): Letzte erfolgreiche GPS-Koordinaten
- `_weather_from_cache` (bool): Flag, das anzeigt, ob Wetterdaten aus Cache stammen
- `_has_live_gps_fix` (bool): Flag, das anzeigt, ob Live-GPS-Fix erhalten wurde

**Methoden:**

##### `on_start()`
Initialisiert die Anwendung beim Start.

Lädt den letzten zwischengespeicherten Standort und initiiert den Standort-Flow. Auf Android-Geräten startet die GPS-Berechtigung und Standortverfolgung. Auf anderen Plattformen werden Fallback-Koordinaten (London) verwendet.

**Parameter:** Keine

**Rückgabewert:** Keine

**Beispiel:**
```python
# Wird automatisch von Kivy beim App-Start aufgerufen
app.on_start()  # Lädt zwischengespeicherten Standort und startet GPS auf Android
```

---

##### `navigate(key: str)`
Navigiert zu einem anderen Bildschirm in der Anwendung.

**Parameter:**
- `key` (str): Bildschirm-Kennung. Gültige Werte sind:
  - `'today'`: Heutiger Wetter-Bildschirm
  - `'tomorrow'`: Morgiger Wetter-Bildschirm
  - `'5days'`: 5-Tage-Vorhersage-Bildschirm

**Rückgabewert:** Keine

**Beispiel:**
```python
app.navigate('5days')  # Navigiert zum 5-Tage-Vorhersage-Bildschirm
```

---

## Basisklassen

### `src/base_screen.py`

#### Klasse: `BaseWeatherScreen`
Basisklasse für alle Wetter-Bildschirme mit Responsive-Layout-Unterstützung.

Behandelt automatische Größenänderungserkennung und Responsive-Layout-Updates, wenn die Fenstergröße ändert. Alle Wetter-Bildschirme erben von dieser Klasse, um konsistentes Responsive-Verhalten zu gewährleisten.

**Eigenschaften:**
- `card_width` (NumericProperty): Breite der Wetter-Karte (350dp)

**Methoden:**

##### `on_kv_post(base_widget)`
Wird aufgerufen, nachdem die KV-Datei für dieses Widget verarbeitet wurde.

Richtet eine Window-Resize-Event-Bindung ein, um Responsive-Layout-Updates zu triggern, wenn die Fenstergröße geändert wird.

**Parameter:**
- `base_widget`: Das Wurzel-Widget aus der KV-Datei

**Rückgabewert:** Keine

---

##### `_on_window_resize(_window, size)`
Behandelt Window-Resize-Events.

Interne Callback-Funktion, die durch Fenstergrößenänderungen ausgelöst wird. Triggert die `on_responsive_update()`-Methode, um Subklassen die Möglichkeit zu geben, auf Größenänderungen zu reagieren.

**Parameter:**
- `_window`: Das Window-Objekt (ungenutzt)
- `size` (tuple): Tupel von (Breite, Höhe) in Pixeln

**Rückgabewert:** Keine

---

##### `on_responsive_update()`
Wird aufgerufen, wenn ein Responsive-Layout-Update erforderlich ist.

Überschreiben Sie diese Methode in Subklassen, um benutzerdefiniertes Responsive-Verhalten zu implementieren, z. B. die Neuberechnung von RecycleView-Höhen oder die Anpassung von Widget-Dimensionen basierend auf verfügbarem Platz.

**Parameter:** Keine

**Rückgabewert:** Keine

---

## Mixins

### `src/app_mixins/weather_sync.py`

#### Klasse: `WeatherSyncMixin`
Mixin, das Wetterdata-Abruf und Display-Synchronisation bereitstellt.

Behandelt das Abrufen von Wetterdaten von der OpenWeatherMap API, die Verwaltung von Standortkoordinaten, die Aktualisierung aller Wetter-UI-Bildschirme mit aktuellen und Vorhersagedaten sowie die Fehlerbehandlung mit Fallback zu zwischengespeicherten Daten.

**Attribute:**
- `_weather_from_cache` (bool): Flag, das verfolgt, ob aktuelle Wetterdaten aus Cache stammen

**Methoden:**

##### `_should_refresh_weather() -> bool`
Überprüft, ob genug Zeit verstrichein ist, um Wetterdaten zu aktualisieren.

Verwendet das `WEATHER_REFRESH_INTERVAL`-Klassenattribut, um API-Aufrufe zu drosseln und übermäßige Anfragen zum Wetterdienst zu vermeiden.

**Parameter:** Keine

**Rückgabewert:**
- `bool`: True, wenn das Refresh-Intervall verstrichein ist, False sonst

**Beispiel:**
```python
if app._should_refresh_weather():
    data = weather_service.get_weather(lat, lon)
```

---

##### `_apply_location(lat, lon, force_refresh=False, track_as_gps=False)`
Wendet Standortkoordinaten an und ruft Wetterdaten ab.

Speichert die bereitgestellten Koordinaten, speichert sie optional zwischen, und ruft Wetterdaten von der API ab. Aktualisiert alle Wetter-UI-Bildschirme mit den abgerufenen Daten. Greift auf zwischengespeicherte Daten zurück, wenn der API-Aufruf fehlschlägt.

**Parameter:**
- `lat` (float): Koordinate Breitengrad (-90 bis 90)
- `lon` (float): Koordinate Längengrad (-180 bis 180)
- `force_refresh` (bool): Erzwingt API-Refresh auch wenn Drosselintervall aktiv ist (Standard: False)
- `track_as_gps` (bool): Als Live-GPS-Fix markieren und in Standort-Cache speichern (Standard: False)

**Rückgabewert:** Keine

**Beispiel:**
```python
# Wende GPS-Standort mit erzwungenem Refresh an (erster GPS-Fix)
app._apply_location(52.5200, 13.4050, force_refresh=True, track_as_gps=True)
```

---

##### `_log_location_roundtrip(requested_lat, requested_lon, weather_data)`
Protokolliert den Unterschied zwischen angeforderten und von der API zurückgegebenen Koordinaten.

Extrahiert den Stadtort aus der Wetter-API-Antwort und vergleicht ihn mit den angeforderten Koordinaten, um die Standortgenauigkeit zu überprüfen. Warnt, wenn sich die Koordinaten erheblich unterscheiden (>1 Grad).

**Parameter:**
- `requested_lat` (float): Der angeforderte Breitengrad
- `requested_lon` (float): Der angeforderte Längengrad
- `weather_data` (dict): Wetter-API-Antwort mit Stadt-Koordinaten-Info

**Rückgabewert:** Keine

---

##### `_location_label_from_error(error, track_as_gps) -> str`
Generiert ein benutzerfreundliches Standort-Label basierend auf dem Fehlertyp.

Ordnet spezifische Ausnahmtypen geeigneten deutschen Fehlermeldungen für die UI-Anzeige zu. Gibt unterschiedliche Nachrichten basierend auf dem Fehlertyp und der Aktivität der GPS-Verfolgung zurück.

**Parameter:**
- `error` (Exception): Die ausgelöste Exception
- `track_as_gps` (bool): Ob dies ein GPS-Verfolgungsversuch war

**Rückgabewert:**
- `str`: Deutsche Fehlermeldung zur Anzeige in der UI

**Fehler-Zuordnung:**
- `EnvNotFoundError` → "Standortname nicht verfuegbar (.env fehlt)"
- `MissingAPIConfigError` → "Standortname nicht verfuegbar (API Konfig fehlt)"
- `APITokenExpiredError` → "Standortname nicht verfuegbar (API Key ungueltig)"
- `NetworkError` → "Standortname nicht verfuegbar (kein Internet)"
- `ServiceUnavailableError` → "Standortname nicht verfuegbar (Wetterdienst down)"
- `APIRequestError` → "Standortname nicht verfuegbar (API Anfragefehler)"

---

##### `_update_location_labels_from_weather(weather_data, track_as_gps=False) -> str | None`
Extrahiert Standort-Label aus Wetterdaten und aktualisiert UI-Bildschirme.

Analysiert den Städtenamen und das Land aus der Wetter-API-Antwort und aktualisiert den auf den Bildschirmen "Heute" und "Morgen" angezeigten Standorttext.

**Parameter:**
- `weather_data` (dict): Wetter-API-Antwort mit Stadtinfo
- `track_as_gps` (bool): Ob dieser Standort von Live-GPS kommt (Standard: False)

**Rückgabewert:**
- `str | None`: Das formatierte Standort-Label oder None bei Extraktionsfehler

---

##### `_extract_location_label(weather_data) -> str | None`
Extrahiert Stadt- und Ländernam aus der Wetter-API-Antwort.

Analysiert das 'city'-Objekt aus der API-Antwort, um Standort-Informationen zu erhalten. Gibt formatierte Zeichenkette "Stadt, Land" oder nur "Stadt" zurück, wenn das Land nicht verfügbar ist.

**Parameter:**
- `weather_data` (dict): Wetter-API-Antwort mit Stadtinfo

**Rückgabewert:**
- `str | None`: Standort-Label wie "Berlin, DE" oder None, wenn nicht gefunden

---

##### `_refresh_forecast_screen()`
Triggert Datenaktualisierung auf dem 5-Tage-Vorhersage-Bildschirm.

Plant eine asynchrone Neuladung von Vorhersagedaten auf dem FiveDaysScreen, um die neueste Wettervorhersage für die aktuellen Koordinaten anzuzeigen.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_update_weather_display(weather_data)`
Aktualisiert alle Wetter-Bildschirme mit aktuellen Daten und Vorhersagen.

Analysiert die Wetter-API-Antwort und aktualisiert:
- Bildschirm "Heute": aktuelle Temperatur, Wetterzustand, stündliche Vorhersage
- Bildschirm "Morgen": Min/Max-Temperatur, stündliche Vorhersage, Wetter-Icon
- Bildschirm "Fünf Tage": Vorhersage-Datenaktualisierung

Nutzt Cache-Indikator-Icons und setzt Standort-Label. Updates werden asynchron auf die UI-Bildschirme angewendet.

**Parameter:**
- `weather_data` (dict): Wetter-API-Antwort mit Vorhersage-Einträgen

**Rückgabewert:** Keine

---

### `src/app_mixins/android_location.py`

#### Klasse: `AndroidLocationMixin`
Mixin, das Android GPS-Standortverfolgung und Berechtigungshandling bereitstellt.

Verwaltet Android-Standortberechtigungen, initialisiert GPS-Verfolgung über den Android LocationManager-Dienst, verarbeitet Standort-Updates mit Provider-Fallback, und implementiert Timeout-Fallback zu zwischengespeicherten Standorten, wenn die GPS-Akquisition fehlschlägt oder nicht verfügbar ist.

**Attribute:**
- `_location_manager`: Android LocationManager-Instanz
- `_location_listener`: Benutzerdefinierte LocationListener-Instanz
- `_gps_timeout_event`: Kivy Clock-Event für GPS-Timeout

**Methoden:**

##### `_start_android_location_flow()`
Startet den Android GPS-Standortakquisitions-Flow.

Fordert erforderliche Standortberechtigungen an (grob und präzise). Wenn Berechtigungen bereits gewährt wurden, startet sofort GPS. Wenn Berechtigungen verweigert werden, fällt auf zwischengespeicherten Standort zurück.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_on_android_permissions_result(permissions, grants)`
Verarbeitet das Ergebnis von Android-Berechtigungsanforderungen.

Wird aufgerufen, wenn der Benutzer auf Berechtigungsanforderungen antwortet. Wenn eine Standortberechtigung gewährt wird, startet GPS. Wenn alle Berechtigungen verweigert werden, fällt auf zwischengespeicherten oder Standard-Standort zurück.

**Parameter:**
- `permissions`: Liste der angeforderten Berechtigungs-IDs
- `grants`: Liste von Booleans, die anzeigen, ob jede Berechtigung gewährt wurde

**Rückgabewert:** Keine

---

##### `_start_gps()`
Startet GPS-Standort-Updates auf Android.

Initialisiert den Android LocationManager und beginnt mit der Anforderung von Standort-Updates von verfügbaren Providern (GPS und/oder Netzwerk). Richtet einen Timeout-Fallback (`GPS_TIMEOUT` Sekunden) ein, um zwischengespeicherten Standort zu verwenden, wenn die GPS-Akquisition fehlschlägt.

Auf Nicht-Android-Plattformen fällt auf zwischengespeicherten oder Standard-Standort zurück.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_init_android_location_manager()`
Initialisiert Android LocationManager und benutzerdefinierten LocationListener.

Richtet den Android-System-LocationManager-Dienst ein und erstellt einen benutzerdefinierten LocationListener, der Android-Standort-Callbacks an Kivy Clock für ordnungsgemäße UI-Thread-Planung verbindet.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_enabled_android_providers() -> list[str]`
Ruft Liste der aktuell aktivierten Android-Standort-Provider ab.

Fragt den Android LocationManager nach verfügbaren Standort-Providern (GPS_PROVIDER und NETWORK_PROVIDER) ab und gibt nur die zurück, die derzeit aktiviert sind.

**Parameter:** Keine

**Rückgabewert:**
- `list[str]`: Liste von aktivierten Provider-Namen (kann leer sein)

---

##### `_start_android_location_updates()`
Startet die Anforderung von Standort-Updates von Android-Providern.

Registriert den benutzerdefinierten LocationListener beim Android LocationManager für alle aktivierten Provider. Gibt auch den letzten bekannten Standort für jeden Provider aus, um sofort einen Standort-Fix zu erhalten, wenn verfügbar.

**Parameter:** Keine

**Rückgabewert:** Keine

**Löst aus:**
- `RuntimeError`: Wenn keine Standort-Provider aktiviert sind

---

##### `_emit_android_last_known_location(providers)`
Gibt den letzten bekannten Standort für jeden Provider aus.

Ruft den vom Android LocationManager zwischengespeicherten letzten bekannten Standort für jeden aktivierten Provider ab und gibt ihn aus. Dies bietet einen unmittelbaren Standort-Fix ohne Warten auf neue GPS-Fixes.

**Parameter:**
- `providers` (list[str]): Liste der zu befragenden Location-Provider-Namen

**Rückgabewert:** Keine

---

##### `_gps_timeout_fallback(_dt)`
Fallback-Handler, der aufgerufen wird, wenn GPS-Akquisition zeitüberschreitet.

Wird aufgerufen, wenn `GPS_TIMEOUT` Sekunden verstreichen ohne GPS-Fix. Fällt auf den letzten zwischengespeicherten Standort oder Standard-Koordinaten zurück.

**Parameter:**
- `_dt`: Delta-Zeit (verwendet von Kivy Clock, ungenutzt)

**Rückgabewert:** Keine

---

##### `on_gps_status(stype, status)`
Verarbeitet GPS-Statusänderungs-Events vom Android LocationListener.

Wird aufgerufen, wenn sich der GPS-Provider-Status ändert (aktiviert, deaktiviert, etc.). Fällt auf zwischengespeicherten Standort zurück, wenn der Status auf degradiertes GPS hinweist.

**Parameter:**
- `stype` (str): Art der Statusänderung ('provider' oder 'status')
- `status` (str): Beschreibung der Statusänderung

**Rückgabewert:** Keine

---

##### `on_gps_location(**kwargs)`
Verarbeitet neuen GPS-Standort-Update vom Android LocationListener.

Validiert die empfangenen Koordinaten, bricht ausstehende Timeouts ab, und wendet den Standort für den Wetterdaten-Abruf an. Ruft `_apply_location()` mit `force_refresh=True` beim ersten GPS-Fix auf.

**Parameter:**
- `**kwargs`: Muss 'lat' und 'lon' als floats enthalten, optionales 'accuracy'

**Rückgabewert:** Keine

---

##### `on_stop()`
Bereinigt GPS-Ressourcen beim Anwendungs-Stop.

Unregistriert den LocationListener vom Android LocationManager, um keine GPS-Updates mehr zu erhalten. Wird automatisch aufgerufen, wenn die App beendet wird.

**Parameter:** Keine

**Rückgabewert:** Keine

---

### `src/app_mixins/location_cache.py`

#### Klasse: `LocationCacheMixin`
Mixin, das Standort-Caching und Fallback-Standort-Funktionalität bereitstellt.

Verarbeitet das Speichern und Laden des letzten bekannten GPS-Standorts in Disk-Cache, stellt Fallback-Koordinaten bereit, wenn GPS nicht verfügbar ist, und formatiert Standort-Label für UI-Anzeige.

**Attribute:**
- `last_gps_lat`, `last_gps_lon` (float): Zuletzt zwischengespeicherte GPS-Koordinaten
- `last_location_label` (str): Zuletzt zwischengespeichertes Standort-Label

**Methoden:**

##### `_use_fallback_location()`
Nutzt fest programmierte Fallback-Koordinaten und wendet sie an.

Nutzt London-Koordinaten (51.5074, -0.1278) als Fallback, wenn kein GPS-Fix verfügbar und kein zwischengespeicherter Standort existiert.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_last_location_cache_path() -> Path`
Ruft den Dateisystem-Pfad zur Standort-Cache-Datei ab.

**Parameter:** Keine

**Rückgabewert:**
- `Path`: Pfad zu last_location.json im Benutzerdaten-Verzeichnis

---

##### `_load_last_known_location()`
Lädt den letzten bekannten Standort aus dem Disk-Cache.

Liest die zwischengespeicherte Standort-JSON-Datei und stellt die Koordinaten und das Standort-Label wieder her. Wenn das Laden fehlschlägt, gilt rückgabewert ohne Fehler.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_save_last_known_location(lat, lon, label=None)`
Speichert den aktuellen Standort in den Disk-Cache.

Speichert Koordinaten und optionales Standort-Label in einer JSON-Datei im Benutzerdaten-Verzeichnis für Persistanz über App-Sitzungen hinweg.

**Parameter:**
- `lat` (float): Zu speichernde Breitengrad-Koordinate
- `lon` (float): Zu speichernde Längengrad-Koordinate
- `label` (str | None): Optionales Standort-Label (Stadt, Land)

**Rückgabewert:** Keine

---

##### `_use_last_known_location_or_default(reason)`
Wendet letzten zwischengespeicherten Standort oder Fallback-Koordinaten an.

Versucht, den zuvor gespeicherten GPS-Standort zu verwenden. Wenn kein zwischengespeicherter Standort existiert, fällt auf fest programmierte Standard-Koordinaten zurück.

**Parameter:**
- `reason` (str): Der Grund, warum dieser Fallback ausgelöst wurde

**Rückgabewert:** Keine

---

##### `_coordinates_in_range(lat, lon) -> bool`
Validiert, dass Koordinaten innerhalb gültiger geografischer Bereiche liegen.

**Parameter:**
- `lat` (float): Zu validierende Breitengrad (-90 bis 90)
- `lon` (float): Zu validierender Längengrad (-180 bis 180)

**Rückgabewert:**
- `bool`: True, wenn Koordinaten gültig sind, False sonst

---

##### `_format_location_label(label, is_live_gps) -> str`
Formatiert ein Standort-Label für Anzeige, optionals mit Quell-Präfix.

Prebend optional "GPS:" oder "Fallback:" -Präfix basierend auf der Standort-Quelle. Wird durch das `SHOW_LOCATION_SOURCE_PREFIX`-Klassenattribut gesteuert.

**Parameter:**
- `label` (str): Das Basis-Standort-Label
- `is_live_gps` (bool): Ob dies von Live-GPS oder Fallback kommt

**Rückgabewert:**
- `str`: Das formatierte Standort-Label zur Anzeige

---

##### `_set_location_labels(label)`
Aktualisiert Standorttext auf allen Wetter-Bildschirmen.

Setzt die `location_text`-Eigenschaft auf den Bildschirmen "Heute" und "Morgen", um das bereitgestellte Standort-Label anzuzeigen.

**Parameter:**
- `label` (str): Das anzuzeigende Standort-Label

**Rückgabewert:** Keine

---

## Bildschirme

### `src/screens/today_screen.py`

#### Klasse: `HourForecast`
Stündliches Vorhersage-Kachel-Widget mit Zeit, Icon, Temperatur und Beschreibung.

**Eigenschaften:**
- `time_text` (StringProperty): Zeit im Format HH:MM
- `icon_source` (StringProperty): Pfad zum Wetter-Icon
- `temp_text` (StringProperty): Temperatur mit Grad-Symbol
- `desc_text` (StringProperty): Wetter-Beschreibung

---

#### Klasse: `TodayScreen`
Bildschirm-Modell für die Ansicht "Heute".

Stellt Eigenschaften aus dem KV-Layout bereit und ein Helper zum Ausfüllen des horizontalen stündlichen Vorhersage-Bereichs mit Elementen, die aus den API-3-stündlichen Vorhersage-Einträgen erstellt wurden.

**Eigenschaften:**
- `location_text` (StringProperty): Aktuelles Standort-Label
- `location_icon_source` (StringProperty): Standort-Icon (GPS oder zwischengespeichert)
- `temp_text` (StringProperty): Aktuelle Temperatur
- `condition_text` (StringProperty): Aktueller Wetterzustand
- `weather_icon` (StringProperty): Aktueller Wetter-Icon-Pfad
- `hourly_items` (ListProperty): Liste von stündlichen Vorhersage-Einträgen

**Methoden:**

##### `set_hourly_data(entries)`
Füllt die stündliche horizontale Vorhersage aus einer Liste von API-Einträgen.

Extrahiert Zeit, Icon, Temperatur und Beschreibung aus jedem Eintrag und erstellt HourForecast-Widgets. UI-Definition befindet sich in weather.kv. Zeigt bis zu 8 3-stündliche Einträge.

**Parameter:**
- `entries` (list): Liste von API-Vorhersage-Wörterbüchern

**Rückgabewert:** Keine

---

### `src/screens/tomorrow_screen.py`

#### Klasse: `TomorrowScreen`
Wetter-Vorhersage für morgen mit detaillierten stündlichen Informationen anzeigen.

Zeigt die Wetterbedingungen von morgen an, einschließlich Min/Max-Temperaturen, stündliche Vorhersage nach Tageszeit, und eine stündliche Aufschlüsselung des ganzen Tages.

**Eigenschaften:**
- `location_text` (StringProperty): Standort-Label für morgen
- `location_icon_source` (StringProperty): Standort-Icon
- `condition_text` (StringProperty): Wetterzustand für morgen
- `minmax_text` (StringProperty): Min/Max-Temperatur-Bereich
- `dayparts_text` (StringProperty): Temps nach Tageszeit
- `weather_icon` (StringProperty): Wetter-Icon für morgen
- `hourly_items` (ListProperty): Stündliche Vorhersage für morgen

**Methoden:**

##### `set_hourly_data(entries)`
Füllt die stündliche Vorhersage für morgen.

Extrahiert stündliche Wetterdaten und erstellt HourForecast-Widgets für jeden Eintrag während des Tages, um die stündliche Vorhersage des ganzen Tages anzuzeigen.

**Parameter:**
- `entries` (list): Liste von API-Vorhersage-Einträgen für morgen

**Rückgabewert:** Keine

---

### `src/screens/five_days_screen.py`

#### Klasse: `FiveDaysScreen`
Bildschirm mit 5-Tage-Wettervorhersage mit Temperatur- und Bedingungsdetails.

Dieser Bildschirm zeigt eine scrollbare Liste von 5 aufeinanderfolgenden Tagen mit täglichen Informationen: Datum, Wetter-Icon, Min/Max-Temperatur, und Temperatur-Aufschlüsselung nach Tageszeit (Morgen, Mittag, Abend, Nacht).

**Eigenschaften:**
- `forecast_items` (ListProperty): Liste von 5-Tage-Vorhersage-Wörterbüchern
- `card_width` (NumericProperty): Breite der Wetter-Karte

**Wichtige Methoden:**

##### `on_kv_post(base_widget)`
Initialisiert den Bildschirm, nachdem die KV-Datei verarbeitet wurde.

Ruft Wetter-Vorhersagedaten von der API auf und füllt die Forecast-Items-Liste mit 5 Tagen Wetterdaten. Berechnet die optimale RecycleView-Höhe basierend auf verfügbarem Platz.

**Parameter:**
- `base_widget`: Das von Kivy während der Initialisierung übergebene Basis-Widget

**Rückgabewert:** Keine

---

##### `_load_forecast_data()`
Ruft 5-Tage-Vorhersagedaten von der Wetter-API auf und verarbeitet sie.

Macht einen API-Aufruf, um Vorhersagedaten zu erhalten, verarbeitet sie in tägliche Zusammenfassungen mit Min/Max-Temperaturen und Aufschlüsselungen nach Tageszeit, und aktualisiert dann die Forecast-Items-Liste.

Fällt auf fest programmierte Daten zurück, wenn der API-Aufruf fehlschlägt.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_process_forecast_data(data) -> list`
Verarbeitet API-Vorhersagedaten in tägliche Zusammenfassungen.

Extrahiert 5 Tage an Wetter-Informationen aus der 3-Stunden-Intervall-API-Antwort, berechnet Min/Max-Temperaturen und extrahiert Temperaturen für verschiedene Tageszeiten.

**Parameter:**
- `data` (dict): API-Antwort mit Vorhersage-Liste in 3-Stunden-Intervallen

**Rückgabewert:**
- `list`: Liste von Wörterbüchern mit Vorhersage-Informationen für 5 Tage

---

##### `_load_fallback_data()`
Lädt fest programmierte Fallback-Daten für Tests, wenn API-Aufruf fehlschlägt.

Bietet statische 5-Tage-Vorhersagedaten mit vordefinierten Daten, Temperaturen und Wetter-Icons für Test- und Entwicklungszwecke.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `on_responsive_update()`
Verarbeitet Responsive-Layout-Updates bei Fenstergrößenänderung.

Wird aufgerufen, wenn das Fenster vergrößert wird. Berechnet die RecycleView-Höhe neu und aktualisiert sie, um im neuen verfügbaren Platz zu passen.

**Parameter:** Keine

**Rückgabewert:** Keine

---

##### `_update_rv_height()`
Berechnet und aktualisiert die RecycleView-Höhe basierend auf verfügbarem Platz.

Bestimmt die optimale Höhe für RecycleView durch:
1. Berechnung der Gesamtinhalts-Höhe (Anzahl Elemente × Reihen-Höhe)
2. Subtraktion von Navigations- und Padding-Höhen von der Karten-Höhe
3. Anwendung von Mindest-(140dp) und Höchst-Beschränkungen
4. Verwendung der kleineren von berechneter oder maximaler Höhe

Die RecycleView-Höhe wird gesetzt, um sicherzustellen, dass alle Vorhersage-Elemente sichtbar sind, während Bildschirmplatz-Einschränkungen respektiert werden.

**Parameter:** Keine

**Rückgabewert:** Keine

---

## UI-Komponenten

### `src/ui/weather_root.py`

#### Klasse: `WeatherRoot`
Wurzel-Widget, das Screen-Navigation und -Übergänge verwaltet.

Steuert den Screen Manager, verarbeitet die Navigation zwischen Wetter-Bildschirmen (Heute, Morgen, 5-Tage-Vorhersage) mit animierten Slide-Übergängen, und hält die Navigationsleiste mit dem aktuellen Bildschirm synchronisiert.

**Methoden:**

##### `on_kv_post(base_widget)`
Wird aufgerufen, nachdem die KV-Datei verarbeitet wurde.

Initialisiert das Wurzel-Widget durch Navigation zum Bildschirm "Heute".

**Parameter:**
- `base_widget`: Das Wurzel-Widget aus der KV-Datei

**Rückgabewert:** Keine

---

##### `navigate(key)`
Navigiert mit animiertem Übergang zu einem anderen Bildschirm.

Versucht, zum angegebenen Bildschirm mit einem Slide-Übergangs-Effekt zu navigieren. Bestimmt die Übergangs-Richtung basierend auf den aktuellen und Ziel-Bildschirm-Positionen.

**Parameter:**
- `key` (str): Bildschirm-Kennung ('today', 'tomorrow' oder '5days')

**Rückgabewert:** Keine

---

##### `_sync_nav_for_current()`
Aktualisiert Navigations-Buttons, um den aktuellen Bildschirm hervorzuheben.

Setzt den entsprechenden Navigations-Button auf 'down'-Status, um visuell anzuzeigen, welcher Bildschirm gerade angezeigt wird.

**Parameter:** Keine

**Rückgabewert:** Keine

---

### `src/ui/forecast_row.py`

#### Klasse: `ForecastRow`
Vorhersage-Zeilen-Widget, das tägliche Vorhersage-Informationen anzeigt.

Zeigt eine einzelne Reihe in der 5-Tage-Vorhersage-Liste mit Datum, Wetter-Icon, Min/Max-Temperaturen und stündlicher Temperatur-Aufschlüsselung (Morgen, Mittag, Abend, Nacht).

**Eigenschaften:**
- `date_text` (StringProperty): Datum im Format "Mo, 22.01."
- `icon_source` (StringProperty): Pfad zum Wetter-Icon-Bild
- `minmax_text` (StringProperty): Min/Max-Temperatur-Anzeige
- `dayparts_text` (StringProperty): Raumleerzeichengetrennte Temps für Morgen, Mittag, Abend, Nacht

---

## Services

### `src/services/weather_service.py`

Dieses Modul verarbeitet alle Wetterdaten-Abrufe von der OpenWeatherMap API mit umfassender Fehlerbehandlung und Caching-Mechanismen.

**Wichtige Funktionen:**

#### `load_dotenv(path=None)`
Lädt Schlüssel=Wert-Paare aus einer .env-Datei in die Prozess-Umgebung.

Sucht nach einer .env-Datei an mehreren Speicherorten (Projektroot, Android-Assets, aktuelles Verzeichnis). Werte werden als rohe Zeichenketten ohne Anführungszeichen-Stripping gespeichert.

**Parameter:**
- `path` (str | None): Expliziter Pfad zur .env-Datei oder None zum Suchen an Standard-Positionen

**Rückgabewert:**
- `dict`: Wörterbuch der geladenen Variablen

**Löst aus:**
- `EnvNotFoundError`: Wenn keine .env-Datei an irgendeinem Ort gefunden wird

---

#### `_get_config()`
Gibt (URL, API_KEY) aus Umgebung zurück oder löst MissingAPIConfigError aus.

Die Konfiguration wird validiert, wenn der Dienst tatsächlich verwendet wird (über `get_weather()`), was Seiteneffekte zur Importzeit vermeidet.

**Aufstöslungsreihenfolge:**
1. Umgebungsvariablen (URL, API_KEY)
2. .env-Datei (Dateisystem oder Android-Assets)
3. config.py-Fallback (immer als .py-Datei im APK enthalten)

**Parameter:** Keine

**Rückgabewert:**
- `tuple`: (URL, api_key) Zeichenketten

**Löst aus:**
- `MissingAPIConfigError`: Wenn weder Umgebung noch .env noch Fallback-Config gefunden wird

---

#### `build_request_url(url, api_key, lat=None, lon=None) -> str`
Erstellt eine Anforderungs-URL aus einer Basis-URL, wobei sichergestellt wird, dass appid, lat, lon gesetzt sind.

- Parsiert die bereitgestellte URL und aktualisiert Abfrage-Parameter
- Stellt sicher, dass appid auf api_key gesetzt ist
- Wenn lat/lon bereitgestellt werden, setzt/überschreibt sie sie in der Abfrage

**Parameter:**
- `url` (str): Basis-API-URL
- `api_key` (str): OpenWeatherMap API-Schlüssel
- `lat` (str | float | None): Optionale Breitengrad für standortbasierte Abfrage
- `lon` (str | float | None): Optionale Längengrad für standortbasierte Abfrage

**Rückgabewert:**
- `str`: Vollständige URL-Zeichenkette, bereit für requests.get()

---

#### `fetch_json(request_url, timeout=10) -> dict`
Führt HTTP GET gegen request_url aus und gibt geparste JSON zurück.

Verarbeitet verschiedene Fehlerbedingungen mit spezifischen Exception-Typen für ordnungsgemäße Fehlerbehandlung im Vorgelagerten.

**Parameter:**
- `request_url` (str): Vollständige URL zum Abrufen
- `timeout` (int): Anforderungs-Timeout in Sekunden (Standard: 10)

**Rückgabewert:**
- `dict`: Geparste JSON-Antwort

**Löst aus:**
- `NetworkError`: Netzwerk-Konnektivitätsprobleme
- `APITokenExpiredError`: API gibt 401 Unauthorized zurück
- `ServiceUnavailableError`: API gibt 5xx-Status zurück
- `APIRequestError`: Andere erfolglose Antworten oder ungültige JSON

---

#### `get_weather(lat=None, lon=None) -> dict`
High-Level-API: gibt Wetter-JSON vom konfigurierten Provider zurück.

Optionale lat/lon können bereitgestellt werden (floats oder Zeichenketten) und werden in die Abfrage-URL-Parameter eingefügt. Wenn weggelassen, werden die in der konfigurierten Basis-URL vorhandenen Koordinaten (oder keine) verwendet.

Wenn der API-Aufruf fehlschlägt, versucht er, zwischengespeicherte Wetterdaten aus der letzten erfolgreichen Anforderung zurückzugeben. Die Antwort hat ein '__cached__'-Flag, das auf True gesetzt ist, wenn Daten aus Cache stammen.

**Parameter:**
- `lat` (str | float | None): Optionale Breitengrad
- `lon` (str | float | None): Optionale Längengrad

**Rückgabewert:**
- `dict`: Wetterdaten von API oder Cache mit möglicherem '__cached__'-Flag

**Löst aus:**
- `APIRequestError`: Wenn sowohl API-Aufruf als auch Cache-Abruf fehlschlagen

---

## Fehlerbehandlung

### `src/utils/exceptions.py`

Alle benutzerdefinierten Exceptions vererben von Standard-Python-Exceptions zur Kompatibilität.

#### `MissingAPIConfigError`
Wird ausgelöst, wenn erforderliche API-Konfiguration fehlt.

Diese Exception signalisiert, dass URL und/oder API_KEY nicht in der Umgebung oder in der .env-Datei des Projekts gefunden wurden.

---

#### `EnvNotFoundError`
Wird ausgelöst, wenn die .env-Datei des Projekts nicht gefunden wird.

Diese unterschiedliche Exception macht es möglich, zwischen einer fehlenden Konfigurationsdatei und anderen Konfigurationsfehlern (wie einem fehlenden Schlüssel in einer vorhandenen .env) zu unterscheiden.

---

#### `NetworkError`
Wird ausgelöst, wenn ein Netzwerk-Fehler die Kontaktaufnahme mit der API verhindert.

Beispiele sind fehlende Internetkonnektivität oder DNS-Auflösungsfehler.

---

#### `ServiceUnavailableError`
Wird ausgelöst, wenn der Remote-Wetterdienst einen 5xx-Fehler zurückgibt.

---

#### `APITokenExpiredError`
Wird ausgelöst, wenn die API mit einem Authentifizierungsfehler antwortet (z. B. 401).

---

#### `APIRequestError`
Allgemeiner Fehler für fehlgeschlagene API-Anforderungen, die nicht von anderen Exceptions abgedeckt werden.

---

## Entwicklungs-Richtlinien

### Hinzufügen neuer Funktionen
1. Bei neuen Funktionen sollten immer umfassende Docstrings im Format dieses Leitfadens added werden
2. Geben Sie Parameter-Typen und Rückgabe-Typen ein
3. Dokumentieren Sie alle Exceptions, die möglicherweise ausgelöst werden
4. Stellen Sie Verwendungsbeispiele für komplexe Funktionen bereit
5. Aktualisieren Sie dieses Dokument mit neuer Funktionsdokumentation

### Fehlerbehandlung
- Verwenden Sie spezifische Exception-Typen aus `utils/exceptions.py`
- Erfassen Sie Exceptions auf der passenden Ebene (API-Schicht, UI-Schicht, etc.)
- Stellen Sie benutzerfreundliche deutsche Fehlermeldungen in der UI bereit
- Protokollieren Sie Fehler mit Kontext zum Debugging

### Standort- und Wetterdaten
- Validieren Sie immer Koordinaten vor der Verwendung
- Behandeln Sie API-Antworten elegant mit Fallback zu Cache
- Aktualisieren Sie Standort-Label auf allen relevanten Bildschirmen
- Respektieren Sie WEATHER_REFRESH_INTERVAL, um übermäßige API-Aufrufe zu vermeiden

---

**Zuletzt aktualisiert:** Februar 2026
**Dokumentations-Version:** 1.0
