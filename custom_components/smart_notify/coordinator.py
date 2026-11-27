"""Kern von Smart Notify: Auslöser beobachten, Anwesenheit prüfen, zustellen."""

from __future__ import annotations

from collections.abc import Callable
from datetime import time
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_HOME
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ABOVE,
    CONF_ARRIVAL_DELAY,
    CONF_BELOW,
    CONF_TRIGGER,
    DEFAULT_POWER_ABOVE,
    DEFAULT_POWER_BELOW,
    CONF_KIND,
    CONF_ONLY_HOME,
    CONF_PLAYER,
    CONF_QUIET_FROM,
    CONF_QUIET_TO,
    CONF_SPEAKERS,
    CONF_TTS_ENTITY,
    KIND_TTS,
    SUBENTRY_DEVICE,
    SUBENTRY_PERSON,
    SUBENTRY_SPEAKER,
    TRIGGER_POWER,
    TRIGGER_STATE,
    CONF_DEVICE_ID,
    CONF_DEVICES,
    CONF_ENTITY,
    CONF_FOR,
    CONF_FROM,
    CONF_MESSAGE,
    CONF_MODE,
    CONF_NAME,
    CONF_NOTIFY,
    person_services,
    CONF_PERSON,
    CONF_PERSONS,
    CONF_RECIPIENTS,
    CONF_TITLE,
    CONF_TO,
    DEFAULT_ARRIVAL_DELAY,
    DEFAULT_TITLE,
    MODE_ALWAYS,
    MODE_ARRIVAL,
    MODE_HOME,
)
from .queue import NotificationQueue

_LOGGER = logging.getLogger(__name__)


class SmartNotifyCoordinator:
    """Hält Konfiguration, Listener und die Warteschlange einer Instanz."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        # person.xyz -> notify.mobile_app_xyz
        self.persons: dict[str, list[str]] = {}
        self.devices: list[dict[str, Any]] = []
        self.speakers: dict[str, dict[str, Any]] = {}
        for sub in entry.subentries.values():
            if sub.subentry_type == SUBENTRY_PERSON:
                self.persons[sub.data[CONF_PERSON]] = person_services(sub.data)
            elif sub.subentry_type == SUBENTRY_DEVICE:
                self.devices.append(
                    {
                        **sub.data,
                        CONF_DEVICE_ID: sub.subentry_id,
                        CONF_NAME: sub.title,
                        CONF_TRIGGER: sub.data.get(CONF_TRIGGER, TRIGGER_STATE),
                    }
                )
            elif sub.subentry_type == SUBENTRY_SPEAKER:
                self.speakers[sub.subentry_id] = {**sub.data, CONF_NAME: sub.title}
        self.arrival_delay: int = int(
            entry.options.get(CONF_ARRIVAL_DELAY, DEFAULT_ARRIVAL_DELAY)
        )
        self.queue = NotificationQueue(hass, entry.entry_id)

        self._unsubs: list[Callable[[], None]] = []
        self._device_timers: dict[str, Callable[[], None]] = {}
        self._arrival_timer: Callable[[], None] | None = None
        # Watt-Geräte, die über der oberen Grenze waren (bereit zum Auslösen)
        self._power_armed: set[str] = set()

    # ------------------------------------------------------------------
    # Start / Stopp
    # ------------------------------------------------------------------
    async def async_start(self) -> None:
        await self.queue.async_load()

        device_entities = {d[CONF_ENTITY] for d in self.devices}
        if device_entities:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, list(device_entities), self._handle_device_change
                )
            )
        if self.persons:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass, list(self.persons), self._handle_person_change
                )
            )

        # Läuft ein Gerät schon über der oberen Grenze, ist es sofort scharf.
        for device in self.devices:
            if device.get(CONF_TRIGGER) != TRIGGER_POWER:
                continue
            state = self.hass.states.get(device[CONF_ENTITY])
            value = self._power_value(state.state) if state else None
            if value is not None and value >= self._above(device):
                self._power_armed.add(device[CONF_DEVICE_ID])

        # Nach einem Neustart: liegt etwas in der Warteschlange und ist schon
        # jemand zuhause, wird es zugestellt.
        if self.queue.items and self.anyone_home():
            self._schedule_queue_delivery()

    @callback
    def async_stop(self) -> None:
        for unsub in self._unsubs:
            unsub()
        self._unsubs.clear()
        for cancel in self._device_timers.values():
            cancel()
        self._device_timers.clear()
        self._power_armed.clear()
        if self._arrival_timer:
            self._arrival_timer()
            self._arrival_timer = None

    # ------------------------------------------------------------------
    # Anwesenheit
    # ------------------------------------------------------------------
    def is_home(self, person: str) -> bool:
        state = self.hass.states.get(person)
        return state is not None and state.state == STATE_HOME

    def anyone_home(self) -> bool:
        return any(self.is_home(p) for p in self.persons)

    @callback
    def _handle_person_change(self, event: Event[EventStateChangedData]) -> None:
        old = event.data["old_state"]
        new = event.data["new_state"]
        if new is None or new.state != STATE_HOME:
            return
        if old is not None and old.state == STATE_HOME:
            return
        _LOGGER.debug("%s ist heimgekommen", event.data["entity_id"])
        if self.queue.items:
            self._schedule_queue_delivery()

    @callback
    def _schedule_queue_delivery(self) -> None:
        if self._arrival_timer:
            self._arrival_timer()

        async def _deliver(_now: Any) -> None:
            self._arrival_timer = None
            await self.async_deliver_queue()

        self._arrival_timer = async_call_later(self.hass, self.arrival_delay, _deliver)

    async def async_deliver_queue(self) -> None:
        """Stellt offene Nachrichten an alle Empfänger zu, die jetzt zuhause sind."""
        delivered: list[dict[str, Any]] = []
        for item in list(self.queue.items):
            recipients = self._valid_recipients(item.get(CONF_RECIPIENTS))
            at_home = [p for p in recipients if self.is_home(p)]
            if not at_home:
                continue
            await self._async_send(item.get(CONF_TITLE), item[CONF_MESSAGE], at_home)
            delivered.append(item)
        await self.queue.async_remove(delivered)

    # ------------------------------------------------------------------
    # Geräte-Auslöser
    # ------------------------------------------------------------------
    @callback
    def _handle_device_change(self, event: Event[EventStateChangedData]) -> None:
        entity_id = event.data["entity_id"]
        old = event.data["old_state"]
        new = event.data["new_state"]
        if new is None:
            return

        for device in self.devices:
            if device[CONF_ENTITY] != entity_id:
                continue
            device_id = device[CONF_DEVICE_ID]
            if device.get(CONF_TRIGGER) == TRIGGER_POWER:
                self._handle_power_change(device, new.state)
                continue
            to_state = device[CONF_TO]

            # Zustand verlässt das Ziel wieder -> laufende Verzögerung abbrechen
            if new.state != to_state:
                if cancel := self._device_timers.pop(device_id, None):
                    cancel()
                continue

            if old is None or old.state == new.state:
                continue
            from_state = device.get(CONF_FROM) or ""
            if from_state and old.state != from_state:
                continue

            delay = int(float(device.get(CONF_FOR) or 0) * 60)
            if delay <= 0:
                self.hass.async_create_task(self._async_fire_device(device))
                continue

            if cancel := self._device_timers.pop(device_id, None):
                cancel()
            self._device_timers[device_id] = async_call_later(
                self.hass, delay, self._make_delayed_fire(device)
            )

    # --- Watt-Auslöser ---------------------------------------------------
    @staticmethod
    def _power_value(state: str) -> float | None:
        try:
            return float(state)
        except (TypeError, ValueError):
            return None  # unavailable / unknown: ignorieren

    @staticmethod
    def _above(device: dict[str, Any]) -> float:
        return float(device.get(CONF_ABOVE, DEFAULT_POWER_ABOVE))

    @staticmethod
    def _below(device: dict[str, Any]) -> float:
        return float(device.get(CONF_BELOW, DEFAULT_POWER_BELOW))

    def _handle_power_change(self, device: dict[str, Any], state: str) -> None:
        """Erst über „above“ (scharf), dann für die Dauer unter „below“ -> auslösen."""
        value = self._power_value(state)
        if value is None:
            return
        device_id = device[CONF_DEVICE_ID]

        if value >= self._above(device):
            self._power_armed.add(device_id)

        if value < self._below(device) and device_id in self._power_armed:
            if device_id in self._device_timers:
                return  # Wartezeit läuft schon
            delay = int(float(device.get(CONF_FOR) or 0) * 60)
            if delay <= 0:
                self._power_armed.discard(device_id)
                self.hass.async_create_task(self._async_fire_device(device))
                return
            self._device_timers[device_id] = async_call_later(
                self.hass, delay, self._make_power_fire(device)
            )
            return

        # Wieder über „below“: laufende Wartezeit abbrechen (bleibt scharf)
        if cancel := self._device_timers.pop(device_id, None):
            cancel()

    def _make_power_fire(self, device: dict[str, Any]):
        async def _fire(_now: Any) -> None:
            device_id = device[CONF_DEVICE_ID]
            self._device_timers.pop(device_id, None)
            state = self.hass.states.get(device[CONF_ENTITY])
            value = self._power_value(state.state) if state else None
            if value is not None and value < self._below(device):
                self._power_armed.discard(device_id)
                await self._async_fire_device(device)

        return _fire

    def _make_delayed_fire(self, device: dict[str, Any]):
        async def _fire(_now: Any) -> None:
            self._device_timers.pop(device[CONF_DEVICE_ID], None)
            state = self.hass.states.get(device[CONF_ENTITY])
            if state is not None and state.state == device[CONF_TO]:
                await self._async_fire_device(device)

        return _fire

    async def _async_fire_device(self, device: dict[str, Any]) -> None:
        name = device.get(CONF_NAME, "")
        title = device.get(CONF_TITLE) or DEFAULT_TITLE
        # freier Text, genau wie gespeichert; leer = „<Gerätename> ist fertig“
        message = (device.get(CONF_MESSAGE) or "").strip() or f"{name} ist fertig"
        _LOGGER.debug("Gerät %s ausgelöst: %s", device.get(CONF_NAME), message)
        await self.async_notify(
            message=message,
            title=title,
            recipients=device.get(CONF_RECIPIENTS),
            mode=device.get(CONF_MODE, MODE_HOME),
            speakers=device.get(CONF_SPEAKERS),
        )

    # ------------------------------------------------------------------
    # Zustellung
    # ------------------------------------------------------------------
    def _valid_recipients(self, recipients: list[str] | None) -> list[str]:
        chosen = [p for p in (recipients or []) if p in self.persons]
        return chosen or list(self.persons)

    async def async_notify(
        self,
        message: str,
        title: str | None = None,
        recipients: list[str] | None = None,
        mode: str = MODE_HOME,
        speakers: list[str] | None = None,
    ) -> None:
        """Nachricht je nach Modus zustellen oder in die Warteschlange legen."""
        if speakers and mode != MODE_ARRIVAL:
            await self._async_speak(message, speakers)
        recipients = self._valid_recipients(recipients)
        if not recipients:
            _LOGGER.warning("Keine Empfänger eingerichtet, Nachricht verworfen")
            return

        if mode == MODE_ALWAYS:
            await self._async_send(title, message, recipients)
            return

        if mode == MODE_HOME:
            at_home = [p for p in recipients if self.is_home(p)]
            if at_home:
                await self._async_send(title, message, at_home)
                return

        # MODE_ARRIVAL oder niemand der Empfänger zuhause
        await self.queue.async_add(
            {
                CONF_TITLE: title,
                CONF_MESSAGE: message,
                CONF_RECIPIENTS: recipients,
                "created": dt_util.utcnow().isoformat(),
            }
        )
        if mode == MODE_ARRIVAL:
            return
        _LOGGER.debug("Niemand zuhause, Nachricht gespeichert: %s", message)

    # --- Lautsprecher (Alexa / TTS) -------------------------------------
    def _in_quiet_time(self, speaker: dict[str, Any]) -> bool:
        start, end = speaker.get(CONF_QUIET_FROM), speaker.get(CONF_QUIET_TO)
        if not start or not end:
            return False
        try:
            now = dt_util.now().time()
            t_from, t_to = time.fromisoformat(start), time.fromisoformat(end)
        except ValueError:
            return False
        if t_from <= t_to:
            return t_from <= now < t_to
        return now >= t_from or now < t_to  # über Mitternacht, z. B. 22:00-07:00

    async def _async_speak(self, message: str, speaker_ids: list[str]) -> None:
        for speaker_id in speaker_ids:
            speaker = self.speakers.get(speaker_id)
            if not speaker:
                continue
            if speaker.get(CONF_ONLY_HOME, True) and not self.anyone_home():
                continue
            if self._in_quiet_time(speaker):
                continue
            try:
                if speaker.get(CONF_KIND) == KIND_TTS:
                    await self.hass.services.async_call(
                        "tts",
                        "speak",
                        {
                            "entity_id": speaker[CONF_TTS_ENTITY],
                            "media_player_entity_id": speaker[CONF_PLAYER],
                            "message": message,
                        },
                        blocking=True,
                    )
                else:
                    domain, _, name = speaker[CONF_NOTIFY].partition(".")
                    await self.hass.services.async_call(
                        domain, name, {"message": message}, blocking=True
                    )
            except Exception:  # noqa: BLE001 - ein Lautsprecher darf die anderen nicht blockieren
                _LOGGER.exception("Ansage über %s fehlgeschlagen", speaker.get(CONF_NAME))

    async def _async_send(
        self, title: str | None, message: str, persons: list[str]
    ) -> None:
        for person in persons:
            for service in self.persons.get(person, []):
                domain, _, name = service.partition(".")
                if not name:
                    domain, name = "notify", service
                data: dict[str, Any] = {"message": message}
                if title and not name.startswith("alexa"):
                    data["title"] = title
                try:
                    await self.hass.services.async_call(domain, name, data, blocking=True)
                except Exception:  # noqa: BLE001 - ein Weg darf die anderen nicht blockieren
                    _LOGGER.exception(
                        "Zustellung an %s über %s fehlgeschlagen", person, service
                    )
