"""Warteschlange für Nachrichten, die auf eine Ankunft warten.

Wird mit dem HA-Store gespeichert und übersteht damit einen Neustart.
"""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store

from .const import DOMAIN, STORAGE_VERSION, signal_queue_updated


class NotificationQueue:
    """Persistente Liste offener Nachrichten."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._hass = hass
        self._entry_id = entry_id
        self._store: Store[dict[str, Any]] = Store(
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.queue"
        )
        self.items: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        data = await self._store.async_load()
        self.items = list((data or {}).get("items", []))

    async def async_add(self, item: dict[str, Any]) -> None:
        self.items.append(item)
        await self._async_save()

    async def async_remove(self, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        self.items = [i for i in self.items if i not in items]
        await self._async_save()

    async def async_clear(self) -> None:
        self.items = []
        await self._async_save()

    async def async_delete_store(self) -> None:
        await self._store.async_remove()

    async def _async_save(self) -> None:
        await self._store.async_save({"items": self.items})
        async_dispatcher_send(self._hass, signal_queue_updated(self._entry_id))
