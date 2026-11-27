"""Eigene Seite „Smart Notify“ in der Seitenleiste.

Drei ein- und ausklappbare Abschnitte (Geräte, Personen, Lautsprecher). Hinzufügen
und Bearbeiten laufen über dieselben Untereintrag-Dialoge wie auf der
Integrationsseite; die Seite zeigt sie nur übersichtlich an.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant.components import frontend, panel_custom, websocket_api
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_ABOVE,
    CONF_BELOW,
    CONF_ENTITY,
    CONF_FOR,
    CONF_FROM,
    CONF_KIND,
    CONF_MODE,
    CONF_ONLY_HOME,
    CONF_PERSON,
    CONF_PLAYER,
    CONF_QUIET_FROM,
    CONF_QUIET_TO,
    CONF_RECIPIENTS,
    CONF_SPEAKERS,
    CONF_TO,
    CONF_TRIGGER,
    CONF_NOTIFY,
    DOMAIN,
    KIND_TTS,
    MODE_ALWAYS,
    MODE_ARRIVAL,
    SUBENTRY_DEVICE,
    SUBENTRY_PERSON,
    SUBENTRY_SPEAKER,
    TRIGGER_POWER,
    person_services,
)

PANEL_URL = "smart-notify"
PANEL_ELEMENT = "smart-notify-panel"
STATIC_URL = "/smart_notify_panel"
_STATIC_FLAG = f"{DOMAIN}_static_registered"
_WS_FLAG = f"{DOMAIN}_ws_registered"

_FRONTEND_DIR = Path(__file__).parent / "frontend"
_JS_FILE = _FRONTEND_DIR / "smart-notify-panel.js"

MODE_TEXT = {
    MODE_ARRIVAL: "erst bei Ankunft",
    MODE_ALWAYS: "immer sofort",
}


def _num(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    return str(int(number)) if number == int(number) else str(number)


def _name_of(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state else entity_id


def _alexa_name(hass: HomeAssistant, service: str | None) -> str:
    """Lesbarer Name zu einem Dienst wie notify.alexa_media_kueche_echo."""
    if not service:
        return "–"
    slug = service.split(".", 1)[-1].removeprefix("alexa_media").strip("_")
    if not slug:
        return "alle Alexa-Geräte"
    state = hass.states.get(f"media_player.{slug}")
    if state is not None:
        return state.name
    return slug.replace("_", " ")


def _person_item(sub) -> dict[str, Any]:
    services = person_services(sub.data)
    return {
        "id": sub.subentry_id,
        "title": sub.title,
        "lines": [", ".join(services) if services else "Kein Benachrichtigungsweg"],
    }


def _speaker_item(hass: HomeAssistant, sub) -> dict[str, Any]:
    data = sub.data
    if data.get(CONF_KIND) == KIND_TTS:
        target = f"TTS auf {_name_of(hass, data.get(CONF_PLAYER, ''))}"
    else:
        target = f"Alexa: {_alexa_name(hass, data.get(CONF_NOTIFY))}"
    extras = []
    if data.get(CONF_ONLY_HOME, True):
        extras.append("nur wenn jemand zuhause ist")
    if data.get(CONF_QUIET_FROM) and data.get(CONF_QUIET_TO):
        extras.append(
            f"Ruhe {str(data[CONF_QUIET_FROM])[:5]}–{str(data[CONF_QUIET_TO])[:5]}"
        )
    lines = [target]
    if extras:
        lines.append(", ".join(extras))
    return {"id": sub.subentry_id, "title": sub.title, "lines": lines}


def _device_item(hass: HomeAssistant, entry: ConfigEntry, sub) -> dict[str, Any]:
    data = sub.data
    if data.get(CONF_TRIGGER) == TRIGGER_POWER:
        trigger = (
            f"Leistung: über {_num(data.get(CONF_ABOVE))} W, "
            f"dann {_num(data.get(CONF_FOR, 0))} min unter {_num(data.get(CONF_BELOW))} W"
        )
    else:
        source = data.get(CONF_FROM)
        trigger = f"Zustand: {f'{source} → ' if source else ''}{data.get(CONF_TO, '')}"
        if data.get(CONF_FOR):
            trigger += f" für {_num(data[CONF_FOR])} min"

    people = {
        s.data[CONF_PERSON]: s.title
        for s in entry.subentries.values()
        if s.subentry_type == SUBENTRY_PERSON
    }
    recipients = data.get(CONF_RECIPIENTS) or []
    to = ", ".join(people.get(r, r) for r in recipients) if recipients else "alle"
    mode = MODE_TEXT.get(data.get(CONF_MODE))

    speakers = [
        s.title
        for s in entry.subentries.values()
        if s.subentry_type == SUBENTRY_SPEAKER and s.subentry_id in (data.get(CONF_SPEAKERS) or [])
    ]
    lines = [f"{_name_of(hass, data.get(CONF_ENTITY, ''))} · {trigger}"]
    send = f"An: {to}"
    if mode:
        send += f" ({mode})"
    if speakers:
        send += f" · Ansage: {', '.join(speakers)}"
    lines.append(send)
    return {"id": sub.subentry_id, "title": sub.title, "lines": lines}


def build_overview(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Inhalt der drei Abschnitte, fertig als Text für die Seite."""
    subs = list(entry.subentries.values())

    def of_type(kind: str):
        return sorted((s for s in subs if s.subentry_type == kind), key=lambda s: s.title.lower())

    return {
        "entry_id": entry.entry_id,
        "devices": [_device_item(hass, entry, s) for s in of_type(SUBENTRY_DEVICE)],
        "persons": [_person_item(s) for s in of_type(SUBENTRY_PERSON)],
        "speakers": [_speaker_item(hass, s) for s in of_type(SUBENTRY_SPEAKER)],
    }


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/overview"})
@callback
def _ws_overview(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Liest direkt aus dem Eintrag (funktioniert auch, während er neu lädt)."""
    entries = hass.config_entries.async_entries(DOMAIN)
    if not entries:
        connection.send_error(msg["id"], "not_found", "Smart Notify ist nicht eingerichtet")
        return
    connection.send_result(msg["id"], build_overview(hass, entries[0]))


@callback
def async_setup_websocket(hass: HomeAssistant) -> None:
    if not hass.data.get(_WS_FLAG):
        websocket_api.async_register_command(hass, _ws_overview)
        hass.data[_WS_FLAG] = True


async def async_register_panel(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Seite in die Seitenleiste hängen (nur für Administratoren)."""
    if not hass.data.get(_STATIC_FLAG):
        await hass.http.async_register_static_paths(
            [StaticPathConfig(STATIC_URL, str(_FRONTEND_DIR), cache_headers=False)]
        )
        hass.data[_STATIC_FLAG] = True

    async_remove_panel(hass)
    # Änderungszeit als Version: nach Updates lädt der Browser die neue Datei
    version = int(_JS_FILE.stat().st_mtime)
    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL,
        webcomponent_name=PANEL_ELEMENT,
        sidebar_title="Smart Notify",
        sidebar_icon="mdi:bell-ring-outline",
        module_url=f"{STATIC_URL}/smart-notify-panel.js?v={version}",
        config={"entry_id": entry.entry_id},
        require_admin=True,
    )


@callback
def async_remove_panel(hass: HomeAssistant) -> None:
    if PANEL_URL in hass.data.get(frontend.DATA_PANELS, {}):
        frontend.async_remove_panel(hass, PANEL_URL)
