"""Tests für die Seite „Smart Notify“ (Seitenleiste)."""

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant

from custom_components.smart_notify.const import DOMAIN
from custom_components.smart_notify.panel import PANEL_URL

from .test_smart_notify import POWER, WASHER, _setup

SPEAKER = {
    "title": "Küche",
    "type": "speaker",
    "data": {"kind": "alexa", "notify_service": "notify.alexa_media_kueche", "only_home": True},
}


async def test_panel_registered_and_removed(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    panel = hass.data[frontend.DATA_PANELS][PANEL_URL]
    assert panel.require_admin is True
    assert panel.config["_panel_custom"]["name"] == "smart-notify-panel"
    assert panel.config["_panel_custom"]["module_url"].startswith(
        "/smart_notify_panel/smart-notify-panel.js"
    )
    assert panel.config["entry_id"] == entry.entry_id

    # Neu laden darf nicht an einer doppelten Seite scheitern
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert PANEL_URL in hass.data[frontend.DATA_PANELS]

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert PANEL_URL not in hass.data[frontend.DATA_PANELS]


async def test_overview_lists_three_sections(hass: HomeAssistant, hass_ws_client) -> None:
    hass.states.async_set("sensor.waschmaschine", "idle", {"friendly_name": "Waschmaschine (Sonoff)"})
    washer = {**WASHER, "data": {**WASHER["data"], "recipients": ["person.thomas_kurz"], "speakers": []}}
    entry = await _setup(hass, [washer, POWER, SPEAKER])

    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/overview"})
    reply = await client.receive_json()
    assert reply["success"]
    data = reply["result"]

    assert data["entry_id"] == entry.entry_id
    assert [d["title"] for d in data["devices"]] == ["Trockner", "Waschmaschine"]
    assert [p["title"] for p in data["persons"]] == ["Susi", "Tom"]
    assert [s["title"] for s in data["speakers"]] == ["Küche"]

    trockner, waschmaschine = data["devices"]
    assert "über 20 W" in trockner["lines"][0] and "3 min unter 5 W" in trockner["lines"][0]
    assert "running → finished" in waschmaschine["lines"][0]
    assert waschmaschine["lines"][0].startswith("Waschmaschine (Sonoff)")
    assert waschmaschine["lines"][1] == "An: Tom"
    assert data["persons"][1]["lines"] == ["notify.mobile_app_thomas_kurz"]
    assert data["speakers"][0]["lines"][0] == "Alexa: kueche"  # kein Player bekannt → lesbarer Dienstname
    assert all("id" in item for key in ("devices", "persons", "speakers") for item in data[key])


async def test_subentry_flow_api_used_by_panel(hass: HomeAssistant, hass_client) -> None:
    """Die Seite startet Dialoge über diese REST-Schnittstelle; Form und Menü müssen passen."""
    entry = await _setup(hass, [WASHER])
    client = await hass_client()
    url = "/api/config/config_entries/subentries/flow"

    resp = await client.post(url, json={"handler": [entry.entry_id, "device"]})
    assert resp.status == 200
    menu = await resp.json()
    assert menu["type"] == "menu" and menu["menu_options"] == ["state", "power"]

    resp = await client.post(f"{url}/{menu['flow_id']}", json={"next_step_id": "power"})
    form = await resp.json()
    assert form["type"] == "form" and form["step_id"] == "power"
    names = [item["name"] for item in form["data_schema"]]
    assert {"name", "entity_id", "power_above", "recipients", "mode"} <= set(names)

    # Bearbeiten: Vorgaben kommen als suggested_value
    sub_id = next(s.subentry_id for s in entry.subentries.values() if s.title == "Waschmaschine")
    resp = await client.post(url, json={"handler": [entry.entry_id, "device"], "subentry_id": sub_id})
    form = await resp.json()
    assert form["type"] == "form" and form["step_id"] == "state"
    name_item = next(i for i in form["data_schema"] if i["name"] == "name")
    assert name_item["description"]["suggested_value"] == "Waschmaschine"


async def test_sidebar_checkbox_in_options(hass: HomeAssistant) -> None:
    entry = await _setup(hass)
    assert PANEL_URL in hass.data[frontend.DATA_PANELS]  # Vorgabe: angezeigt

    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema_keys = [str(k) for k in result["data_schema"].schema]
    assert "show_panel" in schema_keys
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"arrival_delay": 10, "show_panel": False}
    )
    await hass.async_block_till_done()
    assert entry.options["show_panel"] is False
    assert PANEL_URL not in hass.data[frontend.DATA_PANELS]

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"arrival_delay": 10, "show_panel": True}
    )
    await hass.async_block_till_done()
    assert PANEL_URL in hass.data[frontend.DATA_PANELS]


async def test_alexa_speaker_uses_player_name(hass: HomeAssistant, hass_ws_client) -> None:
    hass.states.async_set("media_player.kueche", "idle", {"friendly_name": "Küche Echo"})
    all_alexa = {**SPEAKER, "title": "Alle", "data": {**SPEAKER["data"], "notify_service": "notify.alexa_media"}}
    await _setup(hass, [SPEAKER, all_alexa])
    client = await hass_ws_client(hass)
    await client.send_json({"id": 1, "type": f"{DOMAIN}/overview"})
    speakers = {s["title"]: s["lines"][0] for s in (await client.receive_json())["result"]["speakers"]}
    assert speakers == {"Küche": "Alexa: Küche Echo", "Alle": "Alexa: alle Alexa-Geräte"}
