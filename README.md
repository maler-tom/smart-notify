# 🏠 HA Smart Blueprints

Intelligente Home Assistant Blueprints für Geräte-Benachrichtigungen mit automatischem Pending-System.

- Jemand zuhause → Sofortige Benachrichtigung
- Niemand zuhause → Benachrichtigung gespeichert → beim Heimkommen gesendet

---

## 📦 Blueprints

### 📱 Smart Device Finished – State Based
Für Geräte mit Zustandswechsel (Switch, Sensor, Binary Sensor)

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/maler-tom/ha-smart-blueprints/blob/main/blueprints/smart_device_state_based.yaml)

### ⚡ Smart Device Finished – Power Based
Für Geräte mit Stromverbrauch (Sonoff, Shelly, TP-Link, etc.)

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/maler-tom/ha-smart-blueprints/blob/main/blueprints/smart_device_power_based.yaml)

---

## ⚙️ Installation

### Schritt 1: Scripts einrichten

Inhalt von `scripts/scripts.yaml` in deine `scripts.yaml` kopieren und anpassen:

```yaml
# ANPASSEN:
notify.mobile_app_DEIN_HANDY      → z.B. notify.mobile_app_thomas_iphone
notify.alexa_media_DEIN_ECHO      → z.B. notify.alexa_media_echo_dot
person.DEINE_PERSON_1             → z.B. person.thomas
person.DEINE_PERSON_2             → z.B. person.susi (optional)
```

### Schritt 2: Sensoren einrichten

Inhalt von `sensors/sensors.yaml` in deine `configuration.yaml` kopieren:

```yaml
template: !include sensors.yaml
```

Personen anpassen:
```yaml
# ANPASSEN:
person.DEINE_PERSON_1             → z.B. person.thomas
person.DEINE_PERSON_2             → z.B. person.susi
```

### Schritt 3: Automation einrichten

Inhalt von `automations/send_pending_notifications.yaml` in HA importieren:

- Einstellungen → Automationen → Neue Automation → YAML einfügen

### Schritt 4: HA neu starten

```
Einstellungen → System → Neu starten
```

### Schritt 5: Blueprint importieren

Die Import-Buttons oben verwenden oder manuell:

- Blueprint YAML in `/config/blueprints/automation/` kopieren
- Einstellungen → Automationen → Blueprint → Blueprint importieren

---

## 🔔 Wie es funktioniert

```
Gerät fertig
    ↓
script.notify_those_at_home
    ↓
Person zuhause? ──JA──→ Sofort senden ✅
    │
   NEIN
    ↓
append_pending_notification
(Benachrichtigung gespeichert)
    ↓
Person kommt nach Hause
    ↓
binary_sensor.ist_jemand_zuhause → "on"
    ↓
send_pending_notifications (3 Min. Verzögerung)
    ↓
Alle gespeicherten Benachrichtigungen senden ✅
```

---

## 💡 Beispiel Konfiguration

**Waschmaschine (State Based):**
```
📱 Gerät: switch.waschmaschine
🔄 Von Zustand: on
🎯 Zu Zustand: off
⏱️ Verzögerung: 5 min
💡 Licht: light.kueche (optional)
🔔 Benachrichtigung: script.notify_those_at_home
```

**Spülmaschine (Power Based):**
```
⚡ Power Sensor: sensor.spuelmaschine_power
⚡ Start-Schwelle: 5W
⏱️ Start-Hysterese: 1 min
⚡ End-Schwelle: 5W
⏱️ End-Hysterese: 5 min
🔔 Benachrichtigung: script.notify_those_at_home
```

---

## 🛠️ Entwickelt von

[Smart Home Tom](https://github.com/maler-tom) – Professionelle Smart Home Lösungen
