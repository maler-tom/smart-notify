"""Buttons: Warteschlange leeren oder sofort zustellen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import SmartNotifyEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator = entry.runtime_data
    async_add_entities([ClearQueueButton(coordinator), DeliverQueueButton(coordinator)])


class ClearQueueButton(SmartNotifyEntity, ButtonEntity):
    _attr_icon = "mdi:playlist-remove"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "clear_queue")

    async def async_press(self) -> None:
        await self.coordinator.queue.async_clear()


class DeliverQueueButton(SmartNotifyEntity, ButtonEntity):
    """Stellt offene Nachrichten an alle zu, die gerade zuhause sind (zum Testen)."""

    _attr_icon = "mdi:send"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "deliver_queue")

    async def async_press(self) -> None:
        await self.coordinator.async_deliver_queue()
