"""Gemeinsame Basis für alle Smart-Notify-Entitäten."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import SmartNotifyCoordinator


class SmartNotifyEntity(Entity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: SmartNotifyCoordinator, key: str) -> None:
        self.coordinator = coordinator
        entry_id = coordinator.entry.entry_id
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Smart Notify",
            manufacturer="Smart Home Tom",
            entry_type=DeviceEntryType.SERVICE,
        )
