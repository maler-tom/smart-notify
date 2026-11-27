"""Smart Notify – anwesenheitsbasierte Benachrichtigungen für Home Assistant."""

from __future__ import annotations

import logging
from types import MappingProxyType

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_MESSAGE,
    CONF_MODE,
    CONF_NAME,
    CONF_NOTIFY,
    CONF_PERSON,
    CONF_PERSONS,
    CONF_RECIPIENTS,
    CONF_SHOW_PANEL,
    DEFAULT_SHOW_PANEL,
    CONF_TITLE,
    CONF_TRIGGER,
    DOMAIN,
    MODE_HOME,
    MODES,
    SERVICE_CLEAR_QUEUE,
    SERVICE_SEND,
    OLD_DEVICE_TYPES,
    SUBENTRY_ACTION,
    SUBENTRY_DEVICE,
    SUBENTRY_PERSON,
    SUBENTRY_POWER,
    TRIGGER_POWER,
    TRIGGER_STATE,
)
from .coordinator import SmartNotifyCoordinator
from .panel import async_register_panel, async_remove_panel, async_setup_websocket

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

type SmartNotifyConfigEntry = ConfigEntry[SmartNotifyCoordinator]

SEND_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MESSAGE): cv.string,
        vol.Optional(CONF_TITLE): cv.string,
        vol.Optional(CONF_RECIPIENTS): cv.entity_ids,
        vol.Optional(CONF_MODE, default=MODE_HOME): vol.In(MODES),
    }
)


def _coordinators(hass: HomeAssistant) -> list[SmartNotifyCoordinator]:
    return [
        entry.runtime_data
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.state is ConfigEntryState.LOADED
    ]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Services einmalig registrieren."""

    async def _send(call: ServiceCall) -> None:
        for coordinator in _coordinators(hass):
            await coordinator.async_notify(
                message=call.data[CONF_MESSAGE],
                title=call.data.get(CONF_TITLE),
                recipients=call.data.get(CONF_RECIPIENTS),
                mode=call.data[CONF_MODE],
            )

    async def _clear(call: ServiceCall) -> None:
        for coordinator in _coordinators(hass):
            await coordinator.queue.async_clear()

    hass.services.async_register(DOMAIN, SERVICE_SEND, _send, schema=SEND_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_QUEUE, _clear)
    async_setup_websocket(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: SmartNotifyConfigEntry) -> bool:
    coordinator = SmartNotifyCoordinator(hass, entry)
    await coordinator.async_start()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    if entry.options.get(CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL):
        try:
            await async_register_panel(hass, entry)
        except Exception:  # noqa: BLE001 - die Oberfläche darf die Funktion nicht stoppen
            _LOGGER.warning("Seite „Smart Notify“ konnte nicht angelegt werden", exc_info=True)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SmartNotifyConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        entry.runtime_data.async_stop()
        async_remove_panel(hass)
    return unloaded


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Ältere Stände übernehmen.

    Version 1: Personen und Geräte lagen in den Optionen.
    Version 2/3: Geräte waren getrennte Untereinträge (state_device / power_device,
    kurzzeitig auch „action“).
    Version 4: alle Geräte sind Untereinträge vom Typ „device“; ob nach Zustand
    oder Watt, steht in CONF_TRIGGER.
    """
    if entry.version > 4:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="newer_version",
            translation_placeholders={"version": str(entry.version)},
        )

    if entry.version == 1:
        options = dict(entry.options)
        for person in options.pop(CONF_PERSONS, []):
            hass.config_entries.async_add_subentry(
                entry,
                ConfigSubentry(
                    data=MappingProxyType(
                        {CONF_PERSON: person[CONF_PERSON], CONF_NOTIFY: person[CONF_NOTIFY]}
                    ),
                    subentry_type=SUBENTRY_PERSON,
                    title=_person_title(hass, person[CONF_PERSON]),
                    unique_id=person[CONF_PERSON],
                ),
            )
        for device in options.pop(CONF_DEVICES, []):
            is_power = device.get(CONF_TRIGGER) == TRIGGER_POWER
            data = {
                k: v
                for k, v in device.items()
                if k not in (CONF_DEVICE_ID, CONF_NAME, CONF_TRIGGER, CONF_TITLE)
            }
            data[CONF_TRIGGER] = TRIGGER_POWER if is_power else TRIGGER_STATE
            hass.config_entries.async_add_subentry(
                entry,
                ConfigSubentry(
                    data=MappingProxyType(data),
                    subentry_type=SUBENTRY_DEVICE,
                    title=device.get(CONF_NAME) or "Gerät",
                    unique_id=None,
                ),
            )
        hass.config_entries.async_update_entry(entry, options=options, version=4)
        return True

    for sub in list(entry.subentries.values()):
        if sub.subentry_type not in OLD_DEVICE_TYPES:
            continue
        if sub.subentry_type == SUBENTRY_ACTION:
            is_power = sub.data.get(CONF_TRIGGER) == TRIGGER_POWER
        else:
            is_power = sub.subentry_type == SUBENTRY_POWER
        data = {**sub.data, CONF_TRIGGER: TRIGGER_POWER if is_power else TRIGGER_STATE}
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(data),
                subentry_type=SUBENTRY_DEVICE,
                title=sub.title,
                unique_id=None,
            ),
        )
        hass.config_entries.async_remove_subentry(entry, sub.subentry_id)
    if entry.version != 4:
        hass.config_entries.async_update_entry(entry, version=4)
    return True


def _person_title(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state else entity_id


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Gespeicherte Warteschlange beim Entfernen löschen."""
    from .queue import NotificationQueue

    await NotificationQueue(hass, entry.entry_id).async_delete_store()


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
