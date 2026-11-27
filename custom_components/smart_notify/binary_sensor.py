"""Binärsensor: Ist eine der eingerichteten Personen zuhause?"""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .entity import SmartNotifyEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([AnyoneHomeSensor(entry.runtime_data)])


class AnyoneHomeSensor(SmartNotifyEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PRESENCE

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "anyone_home")

    @property
    def is_on(self) -> bool:
        return self.coordinator.anyone_home()

    @property
    def extra_state_attributes(self) -> dict[str, list[str]]:
        return {
            "at_home": [p for p in self.coordinator.persons if self.coordinator.is_home(p)]
        }

    async def async_added_to_hass(self) -> None:
        if self.coordinator.persons:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass, list(self.coordinator.persons), self._handle_change
                )
            )

    @callback
    def _handle_change(self, _event) -> None:
        self.async_write_ha_state()
