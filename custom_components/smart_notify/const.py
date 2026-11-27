"""Konstanten für Smart Notify."""

from __future__ import annotations

DOMAIN = "smart_notify"

# Personen
CONF_PERSONS = "persons"
CONF_PERSON = "person"
CONF_NOTIFY = "notify_service"  # älterer Stand: ein Dienst pro Person
CONF_NOTIFY_SERVICES = "notify_services"  # mehrere Dienste pro Person

# Geräte
CONF_DEVICES = "devices"
CONF_DEVICE_ID = "id"
CONF_NAME = "name"
CONF_ENTITY = "entity_id"
CONF_FROM = "from_state"
CONF_TO = "to_state"
CONF_FOR = "for_minutes"
CONF_TITLE = "title"
CONF_MESSAGE = "message"
CONF_RECIPIENTS = "recipients"
CONF_MODE = "mode"
CONF_TRIGGER = "trigger"
CONF_ABOVE = "power_above"
CONF_BELOW = "power_below"

# Auslöser-Arten
TRIGGER_STATE = "state"  # Zustandswechsel (Standard, ältere Geräte ohne Feld)
TRIGGER_POWER = "power"  # Watt: erst über "above", dann dauerhaft unter "below"
DEFAULT_POWER_ABOVE = 20  # W
DEFAULT_POWER_BELOW = 5  # W

# Untereinträge (jede Person / jedes Gerät steht unter der Integration)
SUBENTRY_PERSON = "person"
SUBENTRY_DEVICE = "device"  # alle Geräte; Zustand oder Watt steht in CONF_TRIGGER
SUBENTRY_SPEAKER = "speaker"  # Alexa oder TTS-Player
# Ältere Typen, nur noch für die Migration:
SUBENTRY_ACTION = "action"  # früher Zwischenstand
SUBENTRY_STATE = "state_device"  # bis Version 3: Gerät (Zustand)
SUBENTRY_POWER = "power_device"  # bis Version 3: Gerät (Watt)
OLD_DEVICE_TYPES = (SUBENTRY_ACTION, SUBENTRY_STATE, SUBENTRY_POWER)

# Lautsprecher
CONF_SPEAKERS = "speakers"
CONF_KIND = "kind"
KIND_ALEXA = "alexa"  # notify.alexa_media_*
KIND_TTS = "tts"  # tts.speak auf einem media_player
CONF_TTS_ENTITY = "tts_entity"
CONF_PLAYER = "media_player"
CONF_ONLY_HOME = "only_home"
CONF_QUIET_FROM = "quiet_from"
CONF_QUIET_TO = "quiet_to"
# Allgemein
CONF_ARRIVAL_DELAY = "arrival_delay"
CONF_SHOW_PANEL = "show_panel"  # Seite „Smart Notify“ in der Seitenleiste
DEFAULT_SHOW_PANEL = True
DEFAULT_ARRIVAL_DELAY = 60  # Sekunden nach Ankunft, bevor die Warteschlange zugestellt wird
DEFAULT_TITLE = "Smart Notify"

# Zustellmodi
MODE_HOME = "home_now"  # sofort an Anwesende, sonst Warteschlange
MODE_ARRIVAL = "on_arrival"  # immer sammeln, bei Ankunft zustellen
MODE_ALWAYS = "always"  # immer sofort, egal wo
MODES = [MODE_HOME, MODE_ARRIVAL, MODE_ALWAYS]

# Services
SERVICE_SEND = "send"
SERVICE_CLEAR_QUEUE = "clear_queue"

STORAGE_VERSION = 1


def person_services(data) -> list[str]:
    """Alle Benachrichtigungswege einer Person (alte Einträge haben nur einen)."""
    services = list(data.get(CONF_NOTIFY_SERVICES) or [])
    if not services and data.get(CONF_NOTIFY):
        services = [data[CONF_NOTIFY]]
    return services


def signal_queue_updated(entry_id: str) -> str:
    """Dispatcher-Signal, wenn sich die Warteschlange ändert."""
    return f"{DOMAIN}_queue_updated_{entry_id}"
