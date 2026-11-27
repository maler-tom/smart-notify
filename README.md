# 🏠 Smart Notify

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/maler-tom/smart-notify/actions/workflows/validate.yml/badge.svg)](https://github.com/maler-tom/smart-notify/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/maler-tom/smart-notify)](https://github.com/maler-tom/smart-notify/releases)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)

Anwesenheitsbasierte Benachrichtigungen für Home Assistant: Geräte melden, wenn sie fertig sind, und die Nachricht geht nur an die, die gerade zuhause sind.

- Jemand zuhause → Nachricht kommt sofort
- Niemand zuhause → Nachricht wird gespeichert → beim Heimkommen zugestellt

**Voraussetzung:** Home Assistant 2026.3 oder neuer.

## 🆕 Smart Notify Integration

Alles in einem: kein Kopieren von Skripten, Sensoren und Automationen mehr. Die Integration wird über HACS installiert und komplett in der Oberfläche eingerichtet.

**Installation über HACS**

[![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maler-tom&repository=smart-notify&category=integration)

1. Button oben anklicken – oder HACS → ⋮ → Benutzerdefinierte Repositories → `https://github.com/maler-tom/smart-notify`, Typ **Integration**
2. „Smart Notify“ herunterladen und Home Assistant neu starten
3. Einstellungen → Geräte & Dienste → Integration hinzufügen → **Smart Notify**

[![Integration hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=smart_notify)

**Manuell:** Ordner `custom_components/smart_notify` nach `/config/custom_components/` kopieren und Home Assistant neu starten.

**Einrichtung**

4. Bei der Einrichtung wählst du die erste **Person** und ihre Benachrichtigungswege (Handy, Tablet, Telegram … beliebig kombinierbar, das Handy wird vorgeschlagen).
5. Auf der Seite der Integration gibt es drei Abschnitte untereinander, jeweils mit „+“: **Person**, **Lautsprecher (TTS)** und **Gerät**. Alles steht danach als eigene Zeile darunter und lässt sich dort bearbeiten oder löschen.
6. **Gerät:** Beim „+“ wählst du zuerst, woran Smart Notify erkennt, dass das Gerät fertig ist: **am Zustand** (Entität und Von/Zu-Zustand, mit Verzögerung) oder **an der Leistung in Watt** (Leistungs-Sensor mit „Aktiv ab“ und „Fertig unter“). Bei den **Empfängern** musst du mindestens eine Person auswählen. Nachricht, Lautsprecher und Zustellmodus haben Vorgaben („[Name] ist fertig“, keine Ansage, sofort an Anwesende) und können leer bleiben. In der Nachricht genügt normaler Text; `[Name]` wird durch den Gerätenamen ersetzt.
7. **Lautsprecher (TTS):** ein Alexa-Gerät (`notify.alexa_media_…`) oder ein beliebiger Player mit TTS-Dienst. Optional „nur wenn jemand zuhause“ und eine Ruhezeit (auch über Mitternacht). In der Geräte-Zeile wählst du, welche Lautsprecher ansagen.

**Eigene Seite in der Seitenleiste:** Smart Notify bringt eine Übersichtsseite mit. Dort stehen **Geräte**, **Personen** und **Lautsprecher** in drei ein- und ausklappbaren Abschnitten; Hinzufügen, Bearbeiten und Löschen geht direkt dort mit denselben Dialogen. Wer sie nicht möchte, nimmt unter Zahnrad → „In der Seitenleiste anzeigen“ den Haken heraus (empfohlen: angehakt lassen).

**Zustellmodi**

| Modus | Verhalten |
| --- | --- |
| Sofort an Anwesende | geht an Empfänger, die zuhause sind; ist niemand da, wird gespeichert |
| Erst bei Ankunft | wird gespeichert und beim nächsten Heimkommen zugestellt |
| Immer sofort | geht sofort ans Handy, egal wo (z. B. Wasseralarm) |

**Entitäten:** `sensor.smart_notify_warteschlange`, `binary_sensor.smart_notify_jemand_zuhause`, Buttons zum Leeren und sofortigen Zustellen der Warteschlange.

**Service** `smart_notify.send` – eigene Nachrichten aus Automationen über dieselbe Logik schicken:

```yaml
action: smart_notify.send
data:
  message: "Der Akku vom Rauchmelder ist schwach"
  recipients: [person.thomas_kurz]
  mode: home_now
```

**Watt-Auslöser** (Gerät „an der Leistung in Watt“): Das Gerät wird scharf, sobald die Leistung über „Aktiv ab" steigt (z. B. 20 W). Fällt sie danach für die eingestellte Zeit unter „Fertig unter" (z. B. 5 W, 3 min), kommt die Nachricht. Alle Werte sind frei einstellbar und über das Stift-Symbol der Zeile jederzeit änderbar.

Noch nicht dabei: Erinnerungen, Licht-Signal. Die Blueprints unten funktionieren weiter.

**Fehler melden:** [Issues](https://github.com/maler-tom/smart-notify/issues) – bitte HA-Version und den Log-Ausschnitt mit `smart_notify` angeben.

---

## 📦 Blueprints (klassisch, ohne Integration)

### 📱 Smart Device Finished – State Based
Für Geräte mit Zustandswechsel (Switch, Sensor, Binary Sensor)

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/maler-tom/smart-notify/blob/main/smart_device_state_based.yaml)

### ⚡ Smart Device Finished – Power Based
Für Geräte mit Stromverbrauch (Sonoff, Shelly, TP-Link, etc.)

[![Import Blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https://github.com/maler-tom/smart-notify/blob/main/smart_device_power_based.yaml)

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

## 📄 Lizenz

Frei für alle: [MIT-Lizenz](LICENSE). Nutzen, ändern und weitergeben ist erlaubt.
