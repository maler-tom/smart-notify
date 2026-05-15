# 📦 Installation & Setup Anleitung

Schritt-für-Schritt Anleitung zur Installation der Blueprints.

---

## ✅ Voraussetzungen

- **Home Assistant** 2024.1 oder neuer
- **Zugriff auf Dateisystem** (Samba/SSH oder File Editor Add-on)
- **Geräte konfiguriert** (Switch, Sensor, Smart Plug)

---

## 🚀 Installation (5 Minuten)

### Schritt 1: Repository klonen oder herunterladen

**Option A: Mit Git (empfohlen)**
```bash
cd /config
git clone https://github.com/yourusername/smart-home-blueprints.git
```

**Option B: Manuell herunterladen**
- Gehe zu GitHub Repository
- Download ZIP
- Entpacke in `/config/blueprints/automation/`

---

### Schritt 2: Blueprint-Dateien kopieren

Kopiere die YAML-Dateien in das Blueprints-Verzeichnis:

```
/config/blueprints/automation/
├── smart_device_state_based.yaml
└── smart_device_power_based.yaml
```

**Mit Samba (UI-basiert):**
1. Öffne Samba Share auf deinem Computer
2. Navigiere zu `config/blueprints/automation/`
3. Kopiere die `.yaml` Dateien dorthin

**Mit SSH:**
```bash
scp smart_device_*.yaml user@homeassistant.local:/config/blueprints/automation/
```

---

### Schritt 3: Home Assistant neu laden

**Methode 1: Web-UI (einfach)**
1. Home Assistant öffnen
2. **Settings** (⚙️)
3. **Automations & Scenes**
4. **Hamburger Menu** (☰) oben rechts
5. **⟳ Reload Automations**

**Methode 2: Developer Tools**
1. **Developer Tools** (Tools → Developer Tools)
2. **YAML** Tab
3. Auf "**Reload Automations**" klicken

**Methode 3: YAML (terminal)**
```bash
homeassistant:
  # ...
  automation: !include automations.yaml
```
Dann in Terminal:
```bash
ha core restart
```

---

## 🎯 Erste Automation erstellen

### Über Web-UI (empfohlen)

**Schritt 1: Automation erstellen starten**
1. **Settings** → **Automations & Scenes**
2. **Create Automation**

**Schritt 2: Blueprint auswählen**
```
Schritt 1: Automation Type
↓
"Blueprint" wählen
↓
"Smart Device Finished – State Based" (oder Power Based)
↓
"Create from Blueprint"
```

**Schritt 3: Felder ausfüllen**

#### Beispiel 1: Waschmaschine (State-Based)

| Feld | Wert | Erklärung |
|------|------|-----------|
| **Gerät / Sensor** | `switch.waschmaschine` | Der Switch der Waschmaschine |
| **Von Zustand** | `on` | Wenn Gerät läuft |
| **Zu Zustand** | `off` | Wenn Gerät aus ist |
| **Trigger-Verzögerung** | `0` sec | Direkt auslösen |
| **Presence Awareness** | ✅ ON | Nur benachrichtigen wenn zuhause |
| **Presence Entity** | `group.all_people` | Deine Presence Group |
| **'Zu Hause' State** | `home` | Standard-Zustand |
| **Licht aktivieren** | ✅ ON | Sollen Licht einschalten |
| **Licht Entity** | `light.schlafzimmer` | Welches Licht |
| **Licht-Farbe** | 🟠 Orange | Mit Farbkreis wählen |
| **Helligkeit** | 100% | Maximale Helligkeit |
| **Licht Dauer** | 5 min | Nach 5 Min ausschalten |
| **Benachrichtigungen** | (siehe unten) | Welche Aktionen |

#### Beispiel 2: Smart Plug Waschmaschine (Power-Based)

| Feld | Wert | Erklärung |
|------|------|-----------|
| **Power Sensor** | `sensor.waschmaschine_power` | Der Watt-Sensor |
| **Start-Schwelle** | `100` W | Wenn über 100W → läuft |
| **Start-Hysterese** | `1` min | Muss 1 Min > 100W sein |
| **End-Schwelle** | `5` W | Wenn unter 5W → fertig |
| **End-Hysterese** | `5` min | Muss 5 Min < 5W sein |
| **Presence Awareness** | ✅ ON | Nur zuhause |
| **Presence Entity** | `group.all_people` | Deine Presence Group |
| **'Zu Hause' State** | `home` | Standard |
| **Licht aktivieren** | ✅ ON | Licht einschalten |
| **Licht Entity** | `light.schlafzimmer` | Welches Licht |
| **Licht-Farbe** | 🔵 Blau | Mit Farbkreis wählen |
| **Helligkeit** | 80% | 80% Helligkeit |
| **Licht Dauer** | 10 min | Nach 10 Min ausschalten |
| **Benachrichtigungen** | (siehe unten) | Welche Aktionen |

---

### 🔔 Benachrichtigungen konfigurieren

Bei der Konfiguration der Benachrichtigungen klickst du auf **"+ Benachrichtigung hinzufügen"** und wählst dann die Services:

#### Mobile App (HA Companion)
```
Aktion Typ: Benachrichtigung senden
Service: notify.mobile_app_<dein_gerät>
Titel: Waschmaschine fertig
Nachricht: Deine Waschmaschine hat ihren Zyklus beendet
```

**Liste deiner Mobile Apps:** Settings → Devices & Services → Mobile App

#### Telegram
```
Aktion Typ: Benachrichtigung senden
Service: notify.telegram
Titel: 🔔 Waschmaschine
Nachricht: Deine Waschmaschine ist fertig!
```

Voraussetzung: Telegram Bot muss konfiguriert sein
- [Telegram Setup Anleitung](https://www.home-assistant.io/integrations/telegram_bot/)

#### Alexa (Text-to-Speech)
```
Aktion Typ: Benachrichtigung senden
Service: notify.alexa_media
Titel: Waschmaschine fertig
Nachricht: Deine Waschmaschine hat ihren Zyklus beendet
Target: media_player.your_echo_device
```

Voraussetzung: Alexa Media Player Integration
- [Alexa Media Setup](https://github.com/custom-components/alexa_media_player)

#### Persistente Benachrichtigung (Dashboard)
```
Aktion Typ: Benachrichtigung senden
Service: persistent_notification.create
Titel: ⚠️ Waschmaschine fertig
Nachricht: Die Waschmaschine braucht Aufmerksamkeit!
```

---

## 🎛️ Thresholds anpassen (Power-Based)

### Wie finde ich die richtigen Werte?

**Schritt 1: Gerät in Logs beobachten**
1. Developer Tools → **States**
2. Suche: `sensor.waschmaschine_power`
3. Beobachte den Wert während:
   - Gerät startet
   - Gerät läuft
   - Gerät fertig wird

**Beispiel Werte für Waschmaschine:**
```
Standby:     1-2 W
Starting:    ↑ Plötzlich auf 500+ W
Running:     200-400 W (variabel)
Finished:    ↓ Sinkt unter 5 W
```

**Schritt 2: Thresholds setzen**
- **Start-Schwelle:** Ein Punkt über Standby (z.B. 20 W statt 1 W)
- **End-Schwelle:** Ein Punkt unter normalem Betrieb (z.B. 5 W)
- **Hysteresen:** Je nach Stabilität (1-5 Minuten)

**Schritt 3: Testen**
- Starte Gerät → sollte sofort erkannt werden
- Beobachte Logs für Fehler

---

## ✨ Tipps & Best Practices

### 🎯 Presence Awareness
- Nutze `group.all_people` für Mehrpersonen-Haushalte
- Setze State auf `home` (Standard in HA)
- Bei Bedarf: Erstelle separate Gruppen nach Raum

### 💡 Licht-Integration
- Höchste Helligkeit verwenden (100%)
- Farben haben emotionale Wirkung:
  - 🔵 Blau = Entspannung
  - 🟠 Orange = Aufmerksamkeit
  - 🟢 Grün = Bestätigung
- Dauer kurz halten (1-5 Min) um Energie zu sparen

### ⚡ Power-Sensor Tipps
- Smart Plugs kalibrieren vor Nutzung
- Verschiedene Geräte brauchen unterschiedliche Thresholds
- Hysterese erhöhen bei instabilen Sensoren (> 2 Min)

### 🔔 Benachrichtigungen
- Mehrere Services kombinieren für Redundanz
- Nicht zu viele Benachrichtigungen (vermeidbar)
- Test mit "**Services**" Tool vor Deployment

---

## 🔧 Troubleshooting

### Automation wird nicht getriggert

**State-Based:**
- [ ] Gerät Entity ist korrekt konfiguriert
- [ ] Von/Zu Zustand sind korrekt
- [ ] Trigger-Verzögerung ist sinnvoll (nicht zu hoch)
- [ ] Logfile: Automation triggert aber fehlt Aktion?

**Power-Based:**
- [ ] Power Sensor ist korrekt
- [ ] Thresholds sind realistisch (schau in States)
- [ ] Hysterese ist nicht zu hoch
- [ ] Gerät muss über Start-Schwelle gehen für Trigger

### Benachrichtigungen werden nicht gesendet

1. **Service existiert?**
   - Tools → Services
   - Suche nach `notify.*` oder `alexa_media.*`
   
2. **Service konfiguriert?**
   - Settings → Devices & Services
   - Ist die Integration aktiv?

3. **Automation Log prüfen?**
   - Settings → Automations
   - Automation auswählen
   - "**Logs**" Tab anschauen

### Licht wird nicht eingeschaltet

- [ ] Licht Entity ist korrekt
- [ ] Licht ist erreichbar & reagiert
- [ ] Helligkeit ist nicht 0%
- [ ] Transition Zeit ist realistisch

---

## 🆘 Support & Hilfe

### Logs checken
```
Settings → System → Logs → 
Suche nach "automation" oder Entity-Namen
```

### Community Support
- Home Assistant Forum: https://community.home-assistant.io
- GitHub Issues: Stelle ein Issue in dem Repository

### Schnelle Checks
```bash
# Automation Syntax prüfen
hassfest --all /config/automations.yaml

# Gerät vorhanden?
ha service call homeassistant check_config
```

---

**Glückwunsch! Deine Automations sind jetzt ready!** 🎉
