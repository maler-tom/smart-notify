"""Sensor: Anzahl offener Nachrichten in der Warteschlange."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import signal_queue_updated
from .entity import SmartNotifyEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([QueueSensor(entry.runtime_data)])


class QueueSensor(SmartNotifyEntity, SensorEntity):
    _attr_icon = "mdi:format-list-group"
    # Die Liste kann lang werden: nicht in die Datenbank schreiben (16-KB-Grenze je Attribut).
    _unrecorded_attributes = frozenset({"items"})

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "queue")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.queue.items)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"items": self.coordinator.queue.items}

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                signal_queue_updated(self.coordinator.entry.entry_id),
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
