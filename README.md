# 🏠 Smart Notify

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)
[![Validate](https://github.com/maler-tom/smart-notify/actions/workflows/validate.yml/badge.svg)](https://github.com/maler-tom/smart-notify/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/maler-tom/smart-notify)](https://github.com/maler-tom/smart-notify/releases)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-green.svg)](LICENSE)

**Benachrichtigungen für Home Assistant, die wissen, wer zuhause ist.**

Die Waschmaschine ist fertig, der Trockner auch, die Spülmaschine piept. Smart Notify sagt Bescheid, aber nur denen, die gerade zuhause sind. Ist niemand da, wird die Nachricht aufgehoben und kommt, sobald jemand heimkommt. Auf Wunsch sagt Alexa oder ein anderer Lautsprecher es zusätzlich laut an.

Alles wird in der Oberfläche eingerichtet. Kein YAML, keine Skripte, keine Automationen zum Kopieren.

> 🇬🇧 *English summary: Presence-aware notifications for Home Assistant. Appliances report when they are done (by state or by power in watts); the message goes only to people who are at home, otherwise it is queued and delivered on arrival. Optional announcements via Alexa or any TTS player. Set up entirely in the UI; comes with its own sidebar page. The interface is currently German and English.*

---

## 🚀 Import in dein Home Assistant

**Schritt 1: Herunterladen** (öffnet HACS in deinem Home Assistant)

[![Smart Notify in HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maler-tom&repository=smart-notify&category=integration)

Dort **Herunterladen** anklicken, danach Home Assistant **neu starten**.

**Schritt 2: Einrichten** (öffnet die Einrichtung von Smart Notify)

[![Smart Notify zu Home Assistant hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=smart_notify)

> Beim ersten Klick fragt *My Home Assistant* einmal nach der Adresse deines Home Assistant (z. B. `http://homeassistant.local:8123`). Kein HACS? Dann [ZIP-Datei herunterladen](https://github.com/maler-tom/smart-notify/releases/latest/download/smart_notify.zip) und [Weg C](#weg-c-ohne-hacs-mit-der-zip-datei) folgen.

---

## Inhalt

- [Import in dein Home Assistant](#-import-in-dein-home-assistant)
- [Was kann Smart Notify?](#-was-kann-smart-notify)
- [Voraussetzungen](#-voraussetzungen)
- [Installation](#-installation) (HACS mit einem Klick, HACS von Hand, ZIP-Datei)
- [Einrichtung Schritt für Schritt](#-einrichtung-schritt-für-schritt)
- [Die Seite in der Seitenleiste](#-die-seite-in-der-seitenleiste)
- [Geräte: am Zustand oder an der Leistung](#-geräte-am-zustand-oder-an-der-leistung)
- [Lautsprecher (Ansagen)](#-lautsprecher-ansagen)
- [Zustellmodi](#-zustellmodi)
- [So funktioniert es](#-so-funktioniert-es)
- [Entitäten und Aktionen](#-entitäten-und-aktionen)
- [Einstellungen](#-einstellungen)
- [Aktualisieren und Entfernen](#-aktualisieren-und-entfernen)
- [Häufige Fragen und Probleme](#-häufige-fragen-und-probleme)
- [Bekannte Grenzen](#-bekannte-grenzen)
- [Fehler melden und mithelfen](#-fehler-melden-und-mithelfen)

---

## ✨ Was kann Smart Notify?

- 📍 **Nur an Anwesende:** Die Nachricht geht an die ausgewählten Personen, die gerade zuhause sind.
- 📦 **Nichts geht verloren:** Ist niemand zuhause, wartet die Nachricht in einer Warteschlange und kommt beim Heimkommen. Die Warteschlange übersteht auch einen Neustart von Home Assistant.
- 🔌 **Zwei Arten, „fertig“ zu erkennen:** am **Zustand** einer Entität (z. B. ein Sensor meldet `finished`) oder an der **Leistung in Watt** (Steckdose mit Strommessung, z. B. Shelly, Sonoff, TP-Link).
- 🔊 **Ansagen:** über Alexa (Alexa Media Player) oder jeden Player mit TTS, mit Ruhezeit (auch über Mitternacht) und „nur wenn jemand zuhause ist“.
- 📱 **Mehrere Wege pro Person:** Handy, Tablet, Telegram … beliebig kombinierbar.
- 🗂️ **Eigene Seite in der Seitenleiste:** Geräte, Personen und Lautsprecher übersichtlich auf einer Seite, mit Hinzufügen, Bearbeiten und Löschen.
- 🧩 **Aktion für eigene Automationen:** `smart_notify.send` schickt beliebige Nachrichten über dieselbe Logik.
- 🌍 Oberfläche auf **Deutsch** und **Englisch**.

---

## ✅ Voraussetzungen

| Was | Wozu |
| --- | --- |
| **Home Assistant 2026.3 oder neuer** | Smart Notify nutzt Untereinträge, die es erst ab dieser Version gibt. |
| **Personen** in Home Assistant mit Ortung (z. B. Companion-App) | Damit Smart Notify weiß, wer zuhause ist. |
| **Benachrichtigungsdienst** pro Person, z. B. `notify.mobile_app_…` | Darüber kommen die Nachrichten aufs Handy. |
| Optional: **HACS** | Für die Installation mit einem Klick und automatische Updates. |
| Optional: **Alexa Media Player** oder ein **TTS-Dienst** | Nur für gesprochene Ansagen. |

---

## 📥 Installation

Wähle **einen** der drei Wege. Weg A ist der einfachste.

### Weg A: Über HACS mit einem Klick (empfohlen)

1. Auf diesen Knopf klicken. Er öffnet dein Home Assistant direkt an der richtigen Stelle in HACS:

   [![In HACS öffnen](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=maler-tom&repository=smart-notify&category=integration)

2. **Herunterladen** anklicken und bestätigen.
3. Home Assistant **neu starten** (Einstellungen → System → oben rechts ⏻ → Neu starten).
4. Weiter mit der [Einrichtung](#-einrichtung-schritt-für-schritt).

### Weg B: Über HACS von Hand

1. In Home Assistant **HACS** öffnen.
2. Oben rechts **⋮** → **Benutzerdefinierte Repositories**.
3. Bei Repository `https://github.com/maler-tom/smart-notify` eintragen, als Typ **Integration** wählen, **Hinzufügen**.
4. In HACS nach **Smart Notify** suchen, öffnen, **Herunterladen**.
5. Home Assistant **neu starten**.

### Weg C: Ohne HACS mit der ZIP-Datei

1. [**smart_notify.zip** herunterladen](https://github.com/maler-tom/smart-notify/releases/latest/download/smart_notify.zip) (immer die neueste Version).
2. Die ZIP-Datei entpacken. Darin liegt der Ordner `smart_notify`.
3. Diesen Ordner nach `/config/custom_components/` kopieren, z. B. mit dem Add-on *Samba share* oder *File editor*. Danach gibt es `/config/custom_components/smart_notify/manifest.json`.
   Gibt es den Ordner `custom_components` noch nicht, einfach anlegen.
4. Home Assistant **neu starten**.

> Bei Weg C gibt es keine automatischen Update-Hinweise. Für ein Update dieselben Schritte mit der neuen ZIP-Datei wiederholen.

---

## 🛠️ Einrichtung Schritt für Schritt

### 1. Integration hinzufügen

[![Integration hinzufügen](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=smart_notify)

Oder: **Einstellungen → Geräte & Dienste → Integration hinzufügen → Smart Notify**.

### 2. Erste Person wählen

Smart Notify fragt zuerst nach einer **Person** und danach nach ihren **Benachrichtigungswegen**. Das passende Handy ist schon vorgeschlagen. Du kannst mehrere Wege wählen (Handy, Tablet, Telegram …); die Nachricht geht dann an alle gewählten.

### 3. Weitere Personen, Lautsprecher und Geräte anlegen

Das geht an zwei Stellen, ganz wie du magst:

- auf der **Smart-Notify-Seite in der Seitenleiste** (siehe unten), oder
- auf der Seite der Integration (Einstellungen → Geräte & Dienste → Smart Notify) über die Knöpfe **„Person hinzufügen“**, **„Lautsprecher hinzufügen“** und **„Gerät hinzufügen“**.

Empfohlene Reihenfolge: erst alle **Personen**, dann die **Lautsprecher** (falls gewünscht), zuletzt die **Geräte**. Beim Gerät wählst du nämlich aus, wer die Nachricht bekommt und welcher Lautsprecher ansagt.

### 4. Beispiel: Waschmaschine an einer Mess-Steckdose

| Feld | Wert |
| --- | --- |
| Woran erkennen? | **An der Leistung in Watt** |
| Name | Waschmaschine |
| Leistungs-Sensor | `sensor.waschmaschine_power` |
| Aktiv ab | 10 W |
| Fertig unter | 2 W |
| Bleibt darunter für | 8 min |
| Nachricht | *(leer lassen → „Waschmaschine ist fertig“)* |
| Lautsprecher | Küche-Echo |
| Empfänger | Anna, Ben |
| Zustellmodus | Sofort an Anwesende (sonst bei Ankunft) |

Fertig. Ab jetzt meldet sich die Waschmaschine von selbst.

---

## 🗂️ Die Seite in der Seitenleiste

Smart Notify bringt eine eigene Übersichtsseite mit. Sie erscheint in der Seitenleiste als **Smart Notify** (nur für Administratoren sichtbar).

- Drei Abschnitte, jeweils ein- und ausklappbar: **Geräte**, **Personen**, **Lautsprecher**
- Jeder Eintrag mit Kurzinfo, z. B. *„Leistung: über 10 W, dann 8 min unter 2 W · An: Anna · Ansage: Küche-Echo“*
- ✏️ Bearbeiten, 🗑️ Löschen und **„… hinzufügen“** direkt auf der Seite

Du willst die Seite nicht? Unter **Einstellungen → Geräte & Dienste → Smart Notify → ⚙️ (Zahnrad)** den Haken bei **„In der Seitenleiste anzeigen“** entfernen. Alles bleibt dann über die Integrationsseite erreichbar. Empfohlen ist, den Haken gesetzt zu lassen.

---

## 🔌 Geräte: am Zustand oder an der Leistung

Beim Hinzufügen eines Geräts fragt Smart Notify zuerst, **woran** es erkennt, dass das Gerät fertig ist.

### Am Zustand

Für Geräte, die selbst melden, wann sie fertig sind (viele smarte Waschmaschinen, Trockner, Spülmaschinen, Saugroboter, aber auch Schalter oder Binärsensoren).

| Feld | Bedeutung |
| --- | --- |
| Entität | z. B. `sensor.waschmaschine_status` |
| Von Zustand (optional) | Nur wenn der Wechsel *von* diesem Zustand kommt. Leer = egal. |
| Zu Zustand | Der Zustand für „fertig“, genau wie in den Entwicklerwerkzeugen, z. B. `off`, `finished`, `Ende` |
| Bleibt so lange | So viele Minuten muss der Zustand bleiben, bevor die Nachricht kommt |

Ein kurzer Verbindungsabbruch (`unavailable` oder `unknown` → Ziel-Zustand) zählt **nicht** als fertig.

### An der Leistung in Watt

Für ganz normale Geräte an einer Steckdose mit Strommessung.

1. Steigt die Leistung über **„Aktiv ab“**, ist das Gerät *scharf* (es läuft).
2. Fällt sie danach für **„Bleibt darunter für“** Minuten unter **„Fertig unter“**, kommt die Nachricht.

Kurze Pausen im Programm (z. B. Einweichen) lösen dadurch nichts aus.

| Gerät | Aktiv ab | Fertig unter | Bleibt darunter für |
| --- | --- | --- | --- |
| Waschmaschine | 10–20 W | 2–5 W | 5–8 min |
| Trockner | 50 W | 5 W | 3 min |
| Spülmaschine | 10 W | 3 W | 10 min |
| Wasserkocher / Kaffeemaschine | 100 W | 5 W | 1 min |

Die Werte sind Richtwerte. Am besten einmal im Verlauf des Leistungs-Sensors nachsehen, wie viel das Gerät im Stand-by und in Pausen braucht.

### Nachricht, Empfänger, Zustellmodus

- **Nachricht:** freier Text, kommt genau so an. Leer lassen = Gerätename plus „ist fertig“.
- **Empfänger:** mindestens eine Person.
- **Lautsprecher:** leer = keine Ansage.
- **Zustellmodus:** siehe [Zustellmodi](#-zustellmodi).

---

## 🔊 Lautsprecher (Ansagen)

Zwei Arten stehen zur Wahl:

| Art | Was du brauchst |
| --- | --- |
| **Alexa-Gerät** | Integration *Alexa Media Player* (HACS); gewählt wird der Dienst `notify.alexa_media_…` |
| **Anderer Player (TTS)** | Ein TTS-Dienst (z. B. Google Translate, Piper, Home Assistant Cloud) und ein `media_player` |

Für jeden Lautsprecher einstellbar:

- **Nur ansagen, wenn jemand zuhause ist**
- **Ruhezeit von / bis**, z. B. 22:00 bis 07:00. In dieser Zeit wird nichts angesagt; die Nachricht aufs Handy kommt trotzdem.

Angesagt wird in dem Moment, in dem das Gerät fertig ist. Beim Zustellmodus „Erst bei Ankunft“ gibt es keine Ansage.

---

## 📬 Zustellmodi

| Modus | Verhalten | Gut für |
| --- | --- | --- |
| **Sofort an Anwesende** *(Standard)* | Geht sofort an die Empfänger, die zuhause sind. Ist keiner da, wird sie gespeichert und beim Heimkommen zugestellt. | Waschmaschine, Trockner, Spülmaschine |
| **Erst bei Ankunft** | Wird immer gespeichert und beim nächsten Heimkommen zugestellt. | Post im Briefkasten, „Müll rausstellen“ |
| **Immer sofort** | Geht sofort ans Handy, egal wo die Person ist. | Wasseralarm, Rauchmelder, Tür offen |

Gespeicherte Nachrichten kommen kurz **nach** dem Heimkommen (Standard: 60 Sekunden, einstellbar). So piept das Handy nicht schon in der Einfahrt.

---

## 🔄 So funktioniert es

```
Gerät ist fertig
      │
      ├──▶ Ansage über die gewählten Lautsprecher 🔊 (außer bei „Erst bei Ankunft“)
      ▼
Zustellmodus „Immer sofort“? ──ja──▶ sofort an alle Empfänger ✅
      │ nein
      ▼
Ist ein Empfänger zuhause? ──ja──▶ sofort an die Anwesenden ✅
      │ nein
      ▼
Nachricht in die Warteschlange 📦
      │
      ▼
Jemand kommt heim 🏠 ── Wartezeit (Standard 60 s) ──▶ gespeicherte Nachrichten zustellen ✅
```

---

## 🧩 Entitäten und Aktionen

Smart Notify legt ein Gerät **Smart Notify** mit diesen Entitäten an (Namen auf Deutsch, die IDs können bei dir leicht abweichen):

| Entität | Bedeutung |
| --- | --- |
| `sensor.smart_notify_warteschlange` | Anzahl der wartenden Nachrichten |
| `binary_sensor.smart_notify_jemand_zuhause` | Ist mindestens eine eingerichtete Person zuhause? |
| `button.smart_notify_warteschlange_leeren` | Löscht alle wartenden Nachrichten |
| `button.smart_notify_warteschlange_jetzt_zustellen` | Stellt wartende Nachrichten sofort zu (an alle, die zuhause sind) |

### Aktion `smart_notify.send`

Damit schickst du eigene Nachrichten aus Automationen oder Skripten über dieselbe Logik:

```yaml
action: smart_notify.send
data:
  message: "Der Akku vom Rauchmelder im Flur ist schwach"
  title: "Rauchmelder"          # optional
  recipients:                   # optional, leer = alle eingerichteten Personen
    - person.anna
  mode: home_now                # home_now | on_arrival | always
```

Beispiel-Automation: Briefkasten wurde geöffnet, Nachricht kommt erst beim Heimkommen:

```yaml
alias: Post ist da
triggers:
  - trigger: state
    entity_id: binary_sensor.briefkasten
    to: "on"
actions:
  - action: smart_notify.send
    data:
      message: "Es ist Post im Briefkasten 📬"
      mode: on_arrival
```

### Aktion `smart_notify.clear_queue`

Löscht alle wartenden Nachrichten (wie der Knopf).

---

## ⚙️ Einstellungen

**Einstellungen → Geräte & Dienste → Smart Notify → ⚙️ (Zahnrad)**

| Einstellung | Standard | Bedeutung |
| --- | --- | --- |
| Wartezeit nach Ankunft | 60 s | So lange wird nach dem Heimkommen gewartet, bevor gespeicherte Nachrichten kommen. |
| In der Seitenleiste anzeigen | an | Blendet die Smart-Notify-Seite ein oder aus. |

---

## ⬆️ Aktualisieren und Entfernen

**Aktualisieren:** Mit HACS zeigt Home Assistant neue Versionen unter *Einstellungen → Updates* an. **Aktualisieren** anklicken und danach Home Assistant neu starten. Deine Einstellungen bleiben erhalten.

**Entfernen:**

1. Einstellungen → Geräte & Dienste → Smart Notify → ⋮ → **Löschen**
2. In HACS bei Smart Notify ⋮ → **Entfernen** (bei Weg C den Ordner `/config/custom_components/smart_notify` löschen)
3. Home Assistant neu starten

---

## ❓ Häufige Fragen und Probleme

<details>
<summary><b>„Smart Notify“ taucht bei „Integration hinzufügen“ nicht auf</b></summary>

Nach der Installation wurde Home Assistant noch nicht neu gestartet, oder der Ordner liegt falsch. Richtig ist `/config/custom_components/smart_notify/manifest.json`, nicht `/config/custom_components/smart_notify/smart_notify/…`. Danach den Browser mit **Strg+F5** neu laden.
</details>

<details>
<summary><b>Die Seite in der Seitenleiste fehlt oder zeigt alte Inhalte</b></summary>

Die Seite ist nur für Administratoren sichtbar. Prüfe den Haken „In der Seitenleiste anzeigen“ im Zahnrad. Nach einem Update hält der Browser manchmal die alte Fassung fest: Seite mit **Strg+F5** neu laden bzw. in der Companion-App unter *Einstellungen → Companion-App → Fehlerbehebung* den Cache leeren.
</details>

<details>
<summary><b>Die Nachricht kommt nicht</b></summary>

- Ist der Empfänger laut Home Assistant **zuhause**? Sonst liegt die Nachricht in der Warteschlange (`sensor.smart_notify_warteschlange`).
- Stimmt der **Zu Zustand** genau (Groß-/Kleinschreibung, siehe Entwicklerwerkzeuge → Zustände)?
- Bei Watt: Steigt die Leistung wirklich über „Aktiv ab“ und bleibt danach lange genug unter „Fertig unter“? Ein Blick in den Verlauf des Sensors hilft.
- Im Log nach `smart_notify` suchen (Einstellungen → System → Protokolle).
</details>

<details>
<summary><b>Die Nachricht kommt zu oft oder mitten im Programm</b></summary>

Bei Watt „Bleibt darunter für“ erhöhen oder „Fertig unter“ senken. Viele Waschmaschinen machen beim Einweichen oder Schleudern Pausen von einigen Minuten.
</details>

<details>
<summary><b>Alexa sagt nichts an</b></summary>

Läuft gerade die **Ruhezeit**? Ist **„Nur ansagen, wenn jemand zuhause ist“** aktiv und niemand da? Funktioniert der Dienst `notify.alexa_media_…` in den Entwicklerwerkzeugen → Aktionen?
</details>

<details>
<summary><b>Ich habe bisher die Smart-Notify-Blueprints benutzt</b></summary>

Die frühere Blueprint-Fassung (Skripte, Sensoren, Automationen zum Kopieren) wird nicht mehr weiterentwickelt; die Integration ersetzt sie komplett. Umstieg: Integration installieren und einrichten, die Geräte dort neu anlegen, danach die alten Blueprint-Automationen, Skripte und Sensoren löschen. Die alten Dateien gibt es weiterhin in der [Versionsgeschichte des Repos](https://github.com/maler-tom/smart-notify/tree/74c49b6).
</details>

---

## 🚧 Bekannte Grenzen

- Startet Home Assistant neu (oder wird die Integration neu geladen), während ein Gerät gerade läuft oder eine Wartezeit läuft, beginnt die Erkennung danach von vorn. Läuft das Gerät dann nicht mehr über „Aktiv ab“, kommt für diesen Durchgang keine Nachricht. Gespeicherte Nachrichten in der Warteschlange bleiben aber erhalten.
- Bei „Erst bei Ankunft“ bekommt die gespeicherte Nachricht, wer als Erstes heimkommt (und alle Empfänger, die dann schon zuhause sind).
- Noch nicht dabei (geplant): Erinnerungen mit „Erledigt“-Knopf, Licht-Signal, Status-Entitäten pro Gerät.

---

## 🐞 Fehler melden und mithelfen

- **Fehler oder Wünsche:** [Issue anlegen](https://github.com/maler-tom/smart-notify/issues). Bitte die Home-Assistant-Version, die Smart-Notify-Version und den Log-Ausschnitt mit `smart_notify` angeben.
- **Mithelfen:** Pull Requests sind willkommen. Die Tests laufen unter Linux mit `pip install -r requirements_test.txt` und `pytest`.

---

## 🛠️ Entwickelt von

[Smart Home Tom](https://github.com/maler-tom)

## 📄 Lizenz

Frei für alle: [MIT-Lizenz](LICENSE). Nutzen, ändern und weitergeben ist erlaubt.
