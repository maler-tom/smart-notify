# 🏠 Smart Home Blueprints

Eine Sammlung von **produktionsreifen Home Assistant Blueprints** für intelligente Gerätbenachrichtigungen, Licht-Integration und Presence Awareness.

---

## 🚀 Features

✨ **2 spezialisierte Blueprints:**
- 📱 **State-Based** – Für Switch/Sensor mit ON/OFF Status
- ⚡ **Power-Based** – Für Smart Plugs mit Watt-Sensoren

✅ **Alle Blueprints enthalten:**
- 🔔 **Intelligente Benachrichtigungen** – Telegram, HA App, Alexa, Custom Services
- 💡 **Licht-Integration** – RGB-Farben mit Farbkreis-Selector
- 👥 **Presence Awareness** – Nur benachrichtigen wenn jemand zuhause ist
- 🎛️ **100% UI-konfigurierbar** – Keine YAML-Bearbeitung notwendig
- 🔒 **Produktionsreif** – Getestet in realen Smart Homes

---

## 📋 Blueprints

### 1️⃣ State-Based Blueprint
**Für:** Switch, Binary Sensor, Sensor mit Zustandsänderung  
**Beispiele:** Waschmaschine (ON/OFF), Türsensor, Bewegungsmelder

**Features:**
- Auslösung nach Zustandsänderung (z.B. ON → OFF)
- Konfigurierbare Verzögerung vor Trigger
- Alle Standard-Features

**Verwendung:**
- Waschmaschine mit Toggle-Switch
- Spülmaschine mit Status-Sensor
- Türen/Fenster Überwachung
- Beliebige Sensoren mit definierten Zuständen

---

### 2️⃣ Power-Based Blueprint
**Für:** Smart Plugs mit Watt-Sensoren  
**Beispiele:** Sonoff POW, Shelly, TP-Link Kasa

**Features:**
- Automatische Erkennung: Gerät startet → unter Stromverbrauch-Schwelle
- Automatische Erkennung: Gerät fertig → unter Stromverbrauch-Schwelle
- Konfigurierbare Start/End Thresholds in Watt
- Hysterese-Einstellungen für stabile Erkennung
- Alle Standard-Features

**Verwendung:**
- Waschmaschine mit Smart Plug
- Spülmaschine mit Smart Plug
- Trockner, Backofen, etc.
- Alle Geräte mit variablem Stromverbrauch

---

## ⚙️ Gemeinsame Features (beide Blueprints)

### 🔔 Benachrichtigungen
Flexible Actions – Du entscheidest welche Services:
- ✉️ **Telegram** – Chat-Benachrichtigungen
- 📱 **Mobile App** – HA Companion App (Android/iOS)
- 🔊 **Alexa** – Sprachausgabe auf Echo Devices
- 🎤 **TTS** – Text-to-Speech
- 📬 **Email** – Mail-Benachrichtigungen
- 🔔 **Persistent Notification** – Im HA Dashboard
- ⚙️ **Custom Services** – Beliebige andere Services

### 💡 Licht-Integration
- **Farbkreis-Selector** – Wähle die Farbe visuell, nicht per RGB-Code
- **Helligkeit** – Slider 10-100%
- **Auto-Aus** – Optional automatisch nach X Minuten ausschalten
- **Sanfte Übergänge** – 1-2 Sekunden Transition

### 👥 Presence Awareness
- **Optional aktivierbar** – Für Privatsphäre & Effizienz
- **Flexible Entities** – Nutze `group.all_people`, `person.*`, oder binary_sensor
- **Konfigurierbare States** – "home", "away", "sleeping", etc.

---

## 📦 Installation

### Schnellstart (2 Minuten)

1. **Blueprints herunterladen:**
   ```bash
   https://github.com/maler-tom/smart-notify/blob/main/smart_device_power_based.yaml
   ```

2. **In Home Assistant kopieren:**
   ```
   /config/blueprints/automation/
   ```

3. **In HA neu laden:**
   - Settings → Automations & Scenes → ⟳ Reload Automations

4. **Automation erstellen:**
   - Settings → Automations & Scenes → Create Automation → Blueprint wählen

Detaillierte Anleitung → siehe **INSTALLATION.md**

---

## 🎯 Anwendungsbeispiele

### Waschmaschine (State-Based)
```
Gerät: switch.waschmaschine
Von: "on" → Zu: "off"
Presence: ✅ Aktiviert
Licht: ✅ Blau, 5 Min
Benachrichtigungen: Mobile App + Telegram
```
→ Wenn Waschmaschine fertig ist UND jemand zuhause:
- 🔔 Telegram + Mobile App Nachricht
- 💡 Blaues Licht für 5 Min
- 📱 HA Benachrichtigung

### Smart Plug Waschmaschine (Power-Based)
```
Power Sensor: sensor.waschmaschine_power
Start-Schwelle: 100W
End-Schwelle: 5W
Presence: ✅ Aktiviert
Licht: ✅ Orange, 10 Min
Benachrichtigungen: Alexa + Mobile App
```
→ Automatische Erkennung:
- ⚡ Start: Stromverbrauch > 100W für 1 Min
- ⚡ Fertig: Stromverbrauch < 5W für 5 Min
- 🔊 Alexa sagt Nachricht an
- 📱 Mobile App Benachrichtigung
- 💡 Orange Licht für 10 Min

---

## 🔧 Anforderungen

- **Home Assistant** 2024.1 oder neuer
- **YAML Support** für Blueprints
- Für Benachrichtigungen: Entsprechende Services konfiguriert
  - Telegram: `telegram_bot` Integration
  - Mobile App: `HA Companion App` Installation
  - Alexa: `Alexa Media Player` Integration
  - etc.

---

## 🐛 Häufige Probleme

### "Blueprint lässt sich nicht speichern"
→ Stelle sicher, dass alle erforderlichen Input-Felder gefüllt sind

### "Benachrichtigung wird nicht gesendet"
→ Überprüfe, ob der Service in HA verfügbar ist:
- Services → `notify.*` oder `alexa_media.*` sollten existieren

### "Gerät wird nicht erkannt (Power-Based)"
→ Überprüfe die Schwellenwerte:
- Starte Gerät, schau in Logs was der Stromverbrauch ist
- Passe Start-Schwelle & Thresholds an

---

## 📚 Weitere Dokumentation

- **[INSTALLATION.md](./docs/INSTALLATION.md)** – Detaillierte Setup-Anleitung
- **[STATE_BASED.md](./docs/STATE_BASED.md)** – Blueprint Detailanleitung
- **[POWER_BASED.md](./docs/POWER_BASED.md)** – Power Sensor Anleitung
- **[TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** – Häufige Fehler & Lösungen

---

## 🤝 Beitragen

Hast du Verbesserungsvorschläge? Issues oder Pull Requests sind willkommen! 

---

## 📄 Lizenz

MIT License – Frei nutzbar, veränderbar und verteilbar

---

## 🎉 Credits

Basierend auf bewährten HA-Community-Patterns und optimiert für Production-Use.

Made with ❤️ for Smart Home Automation

---

**Noch Fragen?** → Schau in die [Dokumentation](./docs/) oder stelle ein Issue! 🚀
