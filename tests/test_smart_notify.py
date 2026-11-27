"""Tests für Smart Notify (Untereinträge für Personen und Geräte)."""

from datetime import timedelta

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.smart_notify.const import DOMAIN

TOM = "person.thomas_kurz"
SUSI = "person.susi"

WASHER = {
    "title": "Waschmaschine",
    "type": "device",
    "data": {
        "trigger": "state",
        "entity_id": "sensor.waschmaschine",
        "from_state": "running",
        "to_state": "finished",
        "for_minutes": 0,
        "message": "Waschmaschine ist fertig",
        "recipients": [],
        "mode": "home_now",
    },
}

POWER = {
    "title": "Trockner",
    "type": "device",
    "data": {
        "trigger": "power",
        "entity_id": "sensor.trockner_power",
        "power_above": 20.0,
        "power_below": 5.0,
        "for_minutes": 3,
        "message": "Trockner ist fertig",
        "recipients": [],
        "mode": "home_now",
    },
}


def _subentries(devices):
    items = [
        ConfigSubentryData(
            data={"person": TOM, "notify_service": "notify.mobile_app_thomas_kurz"},
            subentry_type="person",
            title="Tom",
            unique_id=TOM,
        ),
        ConfigSubentryData(
            data={"person": SUSI, "notify_service": "notify.mobile_app_susi_iphone"},
            subentry_type="person",
            title="Susi",
            unique_id=SUSI,
        ),
    ]
    for dev in devices or []:
        items.append(
            ConfigSubentryData(
                data=dev["data"], subentry_type=dev["type"], title=dev["title"], unique_id=None
            )
        )
    return items


async def _setup(hass, devices=None):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={"arrival_delay": 10},
        version=4,
        subentries_data=_subentries(devices),
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_flow_asks_first_person(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home", {"device_trackers": ["device_tracker.thomas_kurz"]})
    async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "user"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {"person": TOM})
    assert result["step_id"] == "notify"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"notify_services": ["notify.mobile_app_thomas_kurz"]}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["options"]["arrival_delay"] == 60
    subs = list(result["result"].subentries.values())
    assert [s.subentry_type for s in subs] == ["person"]
    assert subs[0].data["notify_services"] == ["notify.mobile_app_thomas_kurz"]


async def test_add_person_and_device_subentries(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home", {"device_trackers": ["device_tracker.thomas_kurz"]})
    async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    entry = await _setup(hass)
    entry_id = entry.entry_id
    # vorhandene Personen entfernen, damit „hinzufügen“ getestet wird
    for sub_id in list(entry.subentries):
        hass.config_entries.async_remove_subentry(entry, sub_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_init(
        (entry_id, "person"), context={"source": "user"}
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"person": TOM}
    )
    assert result["step_id"] == "notify"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"notify_services": ["notify.mobile_app_thomas_kurz", "notify.telegram_tom"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert [s.subentry_type for s in entry.subentries.values()] == ["person"]
    person = next(iter(entry.subentries.values()))
    assert person.data["notify_services"] == [
        "notify.mobile_app_thomas_kurz",
        "notify.telegram_tom",
    ]

    # Watt-Gerät: Grenzen werden geprüft
    result = await hass.config_entries.subentries.async_init(
        (entry_id, "device"), context={"source": "user"}
    )
    # erst die Art wählen: nach Zustand oder nach Watt
    assert result["type"] is FlowResultType.MENU and result["menu_options"] == ["state", "power"]
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "power"}
    )
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "power"
    data = {
        "name": "Trockner",
        "entity_id": "sensor.trockner_power",
        "power_above": 50,
        "power_below": 60,
        "for_minutes": 2,
        "message": "",
        "recipients": [TOM],
        "mode": "home_now",
    }
    bad = await hass.config_entries.subentries.async_configure(result["flow_id"], data)
    assert bad["errors"]["base"] == "power_thresholds"
    # ohne Empfänger geht es nicht mehr
    bad = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**data, "power_below": 10, "recipients": []}
    )
    assert bad["errors"] == {"recipients": "no_recipients"}
    # Nachricht ist freier Text: Klammern jeder Art werden nicht abgelehnt oder umgebaut
    free = "[Die Waschmaschine] ist {{ fertig, [Name]"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {**data, "power_below": 10, "message": free}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    device = next(s for s in entry.subentries.values() if s.subentry_type == "device")
    assert device.title == "Trockner"
    assert device.data["power_below"] == 10.0
    assert device.data["trigger"] == "power"
    assert device.data["message"] == free
    assert device.data["recipients"] == [TOM]


async def test_message_is_free_text(hass: HomeAssistant) -> None:
    """Der Text kommt genau so an; leer = Gerätename + „ist fertig“."""
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    hass.states.async_set("sensor.spueler", "running")
    hass.states.async_set("sensor.trockner", "running")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    async_mock_service(hass, "notify", "mobile_app_susi_iphone")
    washer = {**WASHER, "data": {**WASHER["data"], "message": "Die [name] ist {{ fertig, bitte ausräumen"}}
    plain = {
        **WASHER,
        "title": "Spüler",
        "data": {**WASHER["data"], "entity_id": "sensor.spueler", "message": "Geschirr ist sauber"},
    }
    empty = {
        **WASHER,
        "title": "Trockner",
        "data": {**WASHER["data"], "entity_id": "sensor.trockner", "message": ""},
    }
    await _setup(hass, [washer, plain, empty])

    for entity in ("sensor.waschmaschine", "sensor.spueler", "sensor.trockner"):
        hass.states.async_set(entity, "finished")
    await hass.async_block_till_done()

    messages = sorted(call.data["message"] for call in tom)
    assert messages == [
        "Die [name] ist {{ fertig, bitte ausräumen",
        "Geschirr ist sauber",
        "Trockner ist fertig",
    ]


async def test_reconfigure_shows_stored_message(hass: HomeAssistant) -> None:
    entry = await _setup(hass, [WASHER])
    sub = next(s for s in entry.subentries.values() if s.subentry_type == "device")
    result = await hass.config_entries.subentries.async_init(
        (entry.entry_id, "device"),
        context={"source": "reconfigure", "subentry_id": sub.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM and result["step_id"] == "state"
    field = next(k for k in result["data_schema"].schema if k == "message")
    assert field.description["suggested_value"] == "Waschmaschine ist fertig"


async def test_sends_to_whoever_is_home(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    susi = async_mock_service(hass, "notify", "mobile_app_susi_iphone")
    await _setup(hass, [WASHER])

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()

    assert len(tom) == 1
    assert tom[0].data["message"] == "Waschmaschine ist fertig"
    assert len(susi) == 0


async def test_queue_and_deliver_on_arrival(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "not_home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    entry = await _setup(hass, [WASHER])
    coordinator = entry.runtime_data

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(tom) == 0
    assert len(coordinator.queue.items) == 1

    hass.states.async_set(TOM, "home")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=11))
    await hass.async_block_till_done()

    assert len(tom) == 1
    assert coordinator.queue.items == []


async def test_delay_cancelled(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "home")
    hass.states.async_set("sensor.waschmaschine", "running")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    async_mock_service(hass, "notify", "mobile_app_susi_iphone")
    await _setup(hass, [{**WASHER, "data": {**WASHER["data"], "for_minutes": 5}}])

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.waschmaschine", "running")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=6))
    await hass.async_block_till_done()
    assert len(tom) == 0

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=12))
    await hass.async_block_till_done()
    assert len(tom) == 1


async def test_service_send_and_queue_sensor(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "not_home")
    hass.states.async_set(SUSI, "not_home")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    await _setup(hass)

    await hass.services.async_call(
        DOMAIN, "send", {"message": "Test", "mode": "always", "recipients": [TOM]}, blocking=True
    )
    assert len(tom) == 1

    await hass.services.async_call(DOMAIN, "send", {"message": "Später"}, blocking=True)
    await hass.async_block_till_done()
    queue_states = [
        s for s in hass.states.async_all("sensor") if s.entity_id.startswith("sensor.smart_notify")
    ]
    assert queue_states and queue_states[0].state == "1"


async def test_power_trigger(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.trockner_power", "0")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    await _setup(hass, [POWER])

    # Nie aktiv gewesen -> nichts
    hass.states.async_set("sensor.trockner_power", "2")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    assert len(tom) == 0

    # Aktiv, kurzer Einbruch, wieder aktiv -> Wartezeit abgebrochen
    hass.states.async_set("sensor.trockner_power", "800")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.trockner_power", "1")
    await hass.async_block_till_done()
    hass.states.async_set("sensor.trockner_power", "300")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    assert len(tom) == 0

    # Dauerhaft unter 5 W -> genau eine Nachricht
    hass.states.async_set("sensor.trockner_power", "1")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=4))
    await hass.async_block_till_done()
    assert len(tom) == 1
    assert tom[0].data["message"] == "Trockner ist fertig"

    # Nicht erneut ohne neue Aktivität
    hass.states.async_set("sensor.trockner_power", "0")
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=8))
    await hass.async_block_till_done()
    assert len(tom) == 1


async def test_migration_from_version_1(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        version=1,
        options={
            "persons": [{"person": TOM, "notify_service": "notify.mobile_app_thomas_kurz"}],
            "devices": [
                {
                    "id": "abc",
                    "name": "Waschmaschine",
                    "entity_id": "sensor.waschmaschine",
                    "from_state": "running",
                    "to_state": "finished",
                    "for_minutes": 0,
                    "title": "",
                    "message": "fertig",
                    "recipients": [],
                    "mode": "home_now",
                },
                {
                    "id": "def",
                    "trigger": "power",
                    "name": "Trockner",
                    "entity_id": "sensor.trockner_power",
                    "power_above": 20.0,
                    "power_below": 5.0,
                    "for_minutes": 3,
                    "message": "fertig",
                    "recipients": [],
                    "mode": "home_now",
                },
            ],
            "arrival_delay": 30,
        },
    )
    entry.add_to_hass(hass)
    hass.states.async_set(TOM, "home")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 4
    assert entry.options == {"arrival_delay": 30}
    kinds = sorted(s.subentry_type for s in entry.subentries.values())
    assert kinds == ["device", "device", "person"]
    triggers = {
        s.title: s.data["trigger"]
        for s in entry.subentries.values()
        if s.subentry_type == "device"
    }
    assert triggers == {"Waschmaschine": "state", "Trockner": "power"}
    titles = {s.title for s in entry.subentries.values()}
    assert {"Waschmaschine", "Trockner"} <= titles


async def test_migration_from_newer_version_fails(hass: HomeAssistant) -> None:
    """Ein Eintrag einer neueren Version wird nicht angefasst."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, version=5, options={"arrival_delay": 10})
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.MIGRATION_ERROR
    assert entry.version == 5
    assert entry.options == {"arrival_delay": 10}


async def test_migration_from_action_intermediate(hass: HomeAssistant) -> None:
    """Zwischenstand mit dem Typ „action“ wird zum Typ „device“."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        version=2,
        options={"arrival_delay": 10},
        subentries_data=[
            ConfigSubentryData(
                data={"person": TOM, "notify_services": ["notify.mobile_app_thomas_kurz"]},
                subentry_type="person",
                title="Tom",
                unique_id=TOM,
            ),
            ConfigSubentryData(
                data=WASHER["data"], subentry_type="action", title="Waschmaschine", unique_id=None
            ),
            ConfigSubentryData(
                data=POWER["data"], subentry_type="action", title="Trockner", unique_id=None
            ),
        ],
    )
    entry.add_to_hass(hass)
    hass.states.async_set(TOM, "home")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 4
    types = {s.title: (s.subentry_type, s.data.get("trigger")) for s in entry.subentries.values()}
    assert types == {
        "Tom": ("person", None),
        "Waschmaschine": ("device", "state"),
        "Trockner": ("device", "power"),
    }


async def test_migration_from_version_3_merges_devices(hass: HomeAssistant) -> None:
    """Gerät und Gerät (Watt) aus Version 3 landen im gemeinsamen Abschnitt „Gerät“."""
    old_state = {k: v for k, v in WASHER["data"].items() if k != "trigger"}
    old_power = {**POWER["data"], "speakers": ["speaker-id"]}
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        version=3,
        options={"arrival_delay": 10},
        subentries_data=[
            *_subentries(None),
            ConfigSubentryData(
                data=old_state, subentry_type="state_device", title="Waschmaschine", unique_id=None
            ),
            ConfigSubentryData(
                data=old_power, subentry_type="power_device", title="Trockner", unique_id=None
            ),
        ],
    )
    entry.add_to_hass(hass)
    hass.states.async_set(TOM, "home")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.version == 4
    devices = {s.title: s.data for s in entry.subentries.values() if s.subentry_type == "device"}
    assert set(devices) == {"Waschmaschine", "Trockner"}
    assert devices["Waschmaschine"]["trigger"] == "state"
    assert devices["Trockner"]["trigger"] == "power"
    assert devices["Trockner"]["speakers"] == ["speaker-id"]  # Einstellungen bleiben
    assert devices["Trockner"]["power_below"] == 5.0
    assert not [s for s in entry.subentries.values() if s.subentry_type in ("state_device", "power_device")]


ALEXA = ConfigSubentryData(
    data={"kind": "alexa", "notify_service": "notify.alexa_media_echo", "only_home": True},
    subentry_type="speaker",
    title="Echo",
    unique_id=None,
)


async def _setup_with_speaker(hass, speaker, only_action_speaker=True):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={"arrival_delay": 10},
        version=4,
        subentries_data=[*_subentries(None), speaker],
    )
    entry.add_to_hass(hass)
    # Aktion nachträglich mit der Lautsprecher-ID anlegen
    speaker_id = next(s.subentry_id for s in entry.subentries.values() if s.subentry_type == "speaker")
    from homeassistant.config_entries import ConfigSubentry
    from types import MappingProxyType

    hass.config_entries.async_add_subentry(
        entry,
        ConfigSubentry(
            data=MappingProxyType(
                {**WASHER["data"], "speakers": [speaker_id] if only_action_speaker else []}
            ),
            subentry_type="device",
            title="Waschmaschine",
            unique_id=None,
        ),
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_speaker_announces_when_home(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    echo = async_mock_service(hass, "notify", "alexa_media_echo")
    await _setup_with_speaker(hass, ALEXA)

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(echo) == 1
    assert echo[0].data["message"] == "Waschmaschine ist fertig"


async def test_speaker_silent_when_nobody_home(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "not_home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    echo = async_mock_service(hass, "notify", "alexa_media_echo")
    await _setup_with_speaker(hass, ALEXA)

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(echo) == 0


async def test_speaker_quiet_time_and_tts_player(hass: HomeAssistant) -> None:
    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    hass.states.async_set("sensor.waschmaschine", "running")
    async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    speak = async_mock_service(hass, "tts", "speak")
    tablet = ConfigSubentryData(
        data={
            "kind": "tts",
            "tts_entity": "tts.piper",
            "media_player": "media_player.friday_tablet",
            "only_home": True,
            "quiet_from": "00:00:00",
            "quiet_to": "23:59:59",
        },
        subentry_type="speaker",
        title="Friday-Tablet",
        unique_id=None,
    )
    await _setup_with_speaker(hass, tablet)
    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(speak) == 0  # ganztägige Ruhezeit

    # Ohne Ruhezeit spricht der Player über tts.speak
    hass.states.async_set("sensor.waschmaschine", "running")
    await hass.async_block_till_done()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    sub = next(s for s in entry.subentries.values() if s.subentry_type == "speaker")
    hass.config_entries.async_update_subentry(
        entry, sub, data={k: v for k, v in sub.data.items() if not k.startswith("quiet")}
    )
    await hass.async_block_till_done()
    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(speak) == 1
    assert speak[0].data["media_player_entity_id"] == "media_player.friday_tablet"


async def test_person_with_several_channels(hass: HomeAssistant) -> None:
    """Jeder gewählte Weg einer Person bekommt die Nachricht."""
    hass.states.async_set(TOM, "home")
    hass.states.async_set("sensor.waschmaschine", "running")
    phone = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    telegram = async_mock_service(hass, "notify", "telegram_tom")
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={"arrival_delay": 10},
        version=4,
        subentries_data=[
            ConfigSubentryData(
                data={
                    "person": TOM,
                    "notify_services": ["notify.mobile_app_thomas_kurz", "notify.telegram_tom"],
                },
                subentry_type="person",
                title="Tom",
                unique_id=TOM,
            ),
            ConfigSubentryData(
                data=WASHER["data"], subentry_type="device", title="Waschmaschine", unique_id=None
            ),
        ],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(phone) == 1 and len(telegram) == 1


async def test_section_order(hass: HomeAssistant) -> None:
    """Abschnitte auf der Integrationsseite: Personen, Lautsprecher, Geräte."""
    from custom_components.smart_notify.config_flow import SmartNotifyConfigFlow

    entry = await _setup(hass)
    assert list(SmartNotifyConfigFlow.async_get_supported_subentry_types(entry)) == [
        "person",
        "speaker",
        "device",
    ]


async def test_manifest_keys_sorted() -> None:
    """hassfest verlangt: domain, name, dann alphabetisch."""
    import json
    from pathlib import Path

    path = Path(__file__).parent.parent / "custom_components" / "smart_notify" / "manifest.json"
    keys = list(json.loads(path.read_text(encoding="utf-8")))
    assert keys[:2] == ["domain", "name"]
    assert keys[2:] == sorted(keys[2:])


async def test_unavailable_to_target_does_not_fire(hass: HomeAssistant) -> None:
    """Ein WLAN-Aussetzer (unavailable -> Ziel-Zustand) ist kein „fertig“."""
    hass.states.async_set(TOM, "home")
    hass.states.async_set("sensor.waschmaschine", "unavailable")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    await _setup(hass, [WASHER])

    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(tom) == 0

    hass.states.async_set("sensor.waschmaschine", "running")
    hass.states.async_set("sensor.waschmaschine", "finished")
    await hass.async_block_till_done()
    assert len(tom) == 1


async def test_deliver_queue_never_sends_twice(hass: HomeAssistant) -> None:
    """Ankunfts-Timer und Knopf gleichzeitig: jede Nachricht geht nur einmal raus."""
    import asyncio

    hass.states.async_set(TOM, "home")
    hass.states.async_set(SUSI, "not_home")
    tom = async_mock_service(hass, "notify", "mobile_app_thomas_kurz")
    entry = await _setup(hass)
    coordinator = entry.runtime_data
    await coordinator.queue.async_add({"title": None, "message": "Hallo", "recipients": [TOM]})

    await asyncio.gather(coordinator.async_deliver_queue(), coordinator.async_deliver_queue())
    assert [call.data["message"] for call in tom] == ["Hallo"]
    assert coordinator.queue.items == []
