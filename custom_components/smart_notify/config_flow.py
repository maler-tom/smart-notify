"""Einrichtung von Smart Notify.

Die Integration selbst wird mit einem Klick angelegt. Personen und Geräte sind
„Untereinträge“: Sie stehen als eigene Zeilen unter Smart Notify und lassen
sich dort einzeln hinzufügen, bearbeiten und löschen.
"""

from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigSubentryData,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    SOURCE_RECONFIGURE,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template import Template
from homeassistant.helpers.selector import (
    BooleanSelector,
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TimeSelector,
)

from .const import (
    CONF_ABOVE,
    CONF_ARRIVAL_DELAY,
    CONF_BELOW,
    CONF_ENTITY,
    CONF_FOR,
    CONF_KIND,
    CONF_ONLY_HOME,
    CONF_SHOW_PANEL,
    DEFAULT_SHOW_PANEL,
    CONF_PLAYER,
    CONF_QUIET_FROM,
    CONF_QUIET_TO,
    CONF_SPEAKERS,
    CONF_TRIGGER,
    CONF_TTS_ENTITY,
    KIND_ALEXA,
    KIND_TTS,
    TRIGGER_POWER,
    TRIGGER_STATE,
    CONF_FROM,
    CONF_MESSAGE,
    CONF_MODE,
    CONF_NOTIFY,
    CONF_NOTIFY_SERVICES,
    person_services,
    CONF_PERSON,
    CONF_RECIPIENTS,
    CONF_TO,
    DEFAULT_ARRIVAL_DELAY,
    DEFAULT_MESSAGE,
    PLACEHOLDER_NAME,
    fill_name,
    is_template,
    DEFAULT_POWER_ABOVE,
    DEFAULT_POWER_BELOW,
    DOMAIN,
    MODE_HOME,
    MODES,
    SUBENTRY_DEVICE,
    SUBENTRY_PERSON,
    SUBENTRY_SPEAKER,
)


# ----------------------------------------------------------------------
# Hilfen
# ----------------------------------------------------------------------
def _notify_services(hass: HomeAssistant) -> list[str]:
    services = hass.services.async_services().get("notify", {})
    skip = {"notify", "send_message", "persistent_notification"}
    return sorted(f"notify.{name}" for name in services if name not in skip)


def _guess_notify(hass: HomeAssistant, person: str) -> str | None:
    """Passenden mobile_app-Dienst zu einer Person erraten."""
    services = set(_notify_services(hass))
    state = hass.states.get(person)
    candidates: list[str] = []
    if state is not None:
        for tracker in state.attributes.get("device_trackers", []) or []:
            candidates.append(tracker.split(".", 1)[1])
    candidates.append(person.split(".", 1)[1])
    for name in candidates:
        if (service := f"notify.mobile_app_{name}") in services:
            return service
    return None


def _person_label(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    return state.name if state else entity_id


def _person_options(hass: HomeAssistant, entry: ConfigEntry) -> list[SelectOptionDict]:
    return [
        SelectOptionDict(
            value=sub.data[CONF_PERSON],
            label=_person_label(hass, sub.data[CONF_PERSON]),
        )
        for sub in entry.subentries.values()
        if sub.subentry_type == SUBENTRY_PERSON
    ]


def _notify_selector(hass: HomeAssistant) -> SelectSelector:
    """Mehrfachauswahl: Handy, Tablet, Telegram, ... beliebig kombinierbar."""
    return SelectSelector(
        SelectSelectorConfig(
            options=_notify_services(hass),
            mode=SelectSelectorMode.DROPDOWN,
            multiple=True,
            custom_value=True,
        )
    )


def _speaker_options(entry: ConfigEntry) -> list[SelectOptionDict]:
    return [
        SelectOptionDict(value=sub.subentry_id, label=sub.title)
        for sub in entry.subentries.values()
        if sub.subentry_type == SUBENTRY_SPEAKER
    ]


def _common_fields(hass: HomeAssistant, entry: ConfigEntry) -> dict[Any, Any]:
    """Nachricht, Empfänger, Lautsprecher, Zustellmodus: für alle Geräte gleich.

    Empfänger sind Pflicht, die übrigen Felder haben Vorgaben.
    """
    speakers = _speaker_options(entry)
    extra: dict[Any, Any] = {}
    if speakers:
        extra[vol.Optional(CONF_SPEAKERS, default=[])] = SelectSelector(
            SelectSelectorConfig(options=speakers, multiple=True, mode=SelectSelectorMode.LIST)
        )
    return {
        **extra,
        vol.Optional(CONF_MESSAGE, default=DEFAULT_MESSAGE): TextSelector(
            TextSelectorConfig(multiline=True)
        ),
        # Pflichtfeld: mindestens eine Person muss gewählt werden (kein „leer = alle“ mehr)
        vol.Required(CONF_RECIPIENTS): SelectSelector(
            SelectSelectorConfig(
                options=_person_options(hass, entry),
                multiple=True,
                mode=SelectSelectorMode.LIST,
            )
        ),
        vol.Required(CONF_MODE, default=MODE_HOME): SelectSelector(
            SelectSelectorConfig(
                options=MODES,
                mode=SelectSelectorMode.LIST,
                translation_key="mode",
            )
        ),
    }


def _minutes(default: int) -> tuple[Any, Any]:
    return (
        vol.Required(CONF_FOR, default=default),
        NumberSelector(
            NumberSelectorConfig(
                min=0, max=240, step=1, unit_of_measurement="min",
                mode=NumberSelectorMode.BOX,
            )
        ),
    )


def _watt() -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=0, max=10000, step=1, unit_of_measurement="W",
            mode=NumberSelectorMode.BOX,
        )
    )


def _state_schema(hass: HomeAssistant, entry: ConfigEntry) -> vol.Schema:
    key, selector = _minutes(0)
    return vol.Schema(
        {
            vol.Required("name"): TextSelector(),
            vol.Required(CONF_ENTITY): EntitySelector(),
            vol.Optional(CONF_FROM, default=""): TextSelector(),
            vol.Required(CONF_TO): TextSelector(),
            key: selector,
            **_common_fields(hass, entry),
        }
    )


def _power_schema(hass: HomeAssistant, entry: ConfigEntry) -> vol.Schema:
    key, selector = _minutes(3)
    return vol.Schema(
        {
            vol.Required("name"): TextSelector(),
            vol.Required(CONF_ENTITY): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required(CONF_ABOVE, default=DEFAULT_POWER_ABOVE): _watt(),
            vol.Required(CONF_BELOW, default=DEFAULT_POWER_BELOW): _watt(),
            key: selector,
            **_common_fields(hass, entry),
        }
    )


_LEGACY_NAME = re.compile(r"\{\{\s*device_name\s*\}\}")


_OTHER_BRACKETS = re.compile(r"\[[^\]]*\]")


def _message_error(hass: HomeAssistant, message: str | None, name: str) -> str | None:
    """Prüft die Nachricht, bevor sie gespeichert wird; gibt den Fehler-Schlüssel zurück.

    Normaler Text und „[Name]“ sind immer in Ordnung. Andere eckige Klammern
    (z. B. „[Die Waschmaschine]“) würden wörtlich ankommen und gelten als Fehler.
    Bei {{ }} oder {% %} wird probeweise ausgewertet; unbekannte Namen in den
    Klammern (z. B. „{{ Die Waschmaschine }}“) gelten ebenfalls als Fehler.
    """
    text = fill_name((message or "").strip(), name)
    if _OTHER_BRACKETS.search(PLACEHOLDER_NAME.sub("", (message or ""))):
        return "unknown_placeholder"
    if not is_template(text):
        return None
    try:
        Template(text, hass).async_render(
            {"device_name": name}, parse_result=False, strict=True
        )
    except TemplateError:
        return "invalid_message"
    return None


def _clean_device(user_input: dict[str, Any]) -> dict[str, Any]:
    """Eingabe in das gespeicherte Format bringen (ohne den Namen, der ist der Titel)."""
    data = {k: v for k, v in user_input.items() if k != "name"}
    if CONF_FROM in data:
        data[CONF_FROM] = (data[CONF_FROM] or "").strip()
    if CONF_TO in data:
        data[CONF_TO] = data[CONF_TO].strip()
    data[CONF_FOR] = int(data.get(CONF_FOR) or 0)
    if CONF_ABOVE in data:
        data[CONF_ABOVE] = float(data[CONF_ABOVE])
        data[CONF_BELOW] = float(data[CONF_BELOW])
    data[CONF_MESSAGE] = (data.get(CONF_MESSAGE) or "").strip() or DEFAULT_MESSAGE
    data[CONF_RECIPIENTS] = data.get(CONF_RECIPIENTS) or []
    return data


# ----------------------------------------------------------------------
# Hauptflow: ein Klick
# ----------------------------------------------------------------------
class SmartNotifyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Ersteinrichtung: gleich die erste Person mit ihren Benachrichtigungswegen."""

    VERSION = 4

    def __init__(self) -> None:
        self._person: str = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            self._person = user_input[CONF_PERSON]
            return await self.async_step_notify()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_PERSON): EntitySelector(EntitySelectorConfig(domain="person"))}
            ),
        )

    async def async_step_notify(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title="Smart Notify",
                data={},
                options={CONF_ARRIVAL_DELAY: DEFAULT_ARRIVAL_DELAY},
                subentries=[
                    ConfigSubentryData(
                        subentry_type=SUBENTRY_PERSON,
                        title=_person_label(self.hass, self._person),
                        unique_id=self._person,
                        data={
                            CONF_PERSON: self._person,
                            CONF_NOTIFY_SERVICES: user_input[CONF_NOTIFY_SERVICES],
                        },
                    )
                ],
            )
        guess = _guess_notify(self.hass, self._person)
        key = (
            vol.Required(CONF_NOTIFY_SERVICES, default=[guess])
            if guess
            else vol.Required(CONF_NOTIFY_SERVICES)
        )
        return self.async_show_form(
            step_id="notify",
            data_schema=vol.Schema({key: _notify_selector(self.hass)}),
            description_placeholders={"person": _person_label(self.hass, self._person)},
        )

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        # Reihenfolge = Reihenfolge der Abschnitte auf der Integrationsseite
        return {
            SUBENTRY_PERSON: PersonSubentryFlow,
            SUBENTRY_SPEAKER: SpeakerSubentryFlow,
            SUBENTRY_DEVICE: DeviceSubentryFlow,
        }

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return SmartNotifyOptionsFlow()


class SmartNotifyOptionsFlow(OptionsFlow):
    """Zahnrad der Integration: allgemeine Einstellungen."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data={
                    **self.config_entry.options,
                    CONF_ARRIVAL_DELAY: int(user_input[CONF_ARRIVAL_DELAY]),
                    CONF_SHOW_PANEL: bool(user_input[CONF_SHOW_PANEL]),
                }
            )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_ARRIVAL_DELAY,
                        default=self.config_entry.options.get(
                            CONF_ARRIVAL_DELAY, DEFAULT_ARRIVAL_DELAY
                        ),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0, max=1800, step=5, unit_of_measurement="s",
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(
                        CONF_SHOW_PANEL,
                        default=self.config_entry.options.get(
                            CONF_SHOW_PANEL, DEFAULT_SHOW_PANEL
                        ),
                    ): BooleanSelector(),
                }
            ),
        )


# ----------------------------------------------------------------------
# Untereintrag: Person
# ----------------------------------------------------------------------
class PersonSubentryFlow(ConfigSubentryFlow):
    """Person hinzufügen: erst die Person wählen, das Handy wird vorgeschlagen."""

    def __init__(self) -> None:
        self._person: str = ""

    def _taken(self) -> set[str]:
        return {
            sub.data[CONF_PERSON]
            for sub in self._get_entry().subentries.values()
            if sub.subentry_type == SUBENTRY_PERSON
        }

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            if user_input[CONF_PERSON] in self._taken():
                errors[CONF_PERSON] = "person_exists"
            else:
                self._person = user_input[CONF_PERSON]
                return await self.async_step_notify()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_PERSON): EntitySelector(EntitySelectorConfig(domain="person"))}
            ),
            errors=errors,
        )

    async def async_step_notify(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=_person_label(self.hass, self._person),
                data={
                    CONF_PERSON: self._person,
                    CONF_NOTIFY_SERVICES: user_input[CONF_NOTIFY_SERVICES],
                },
                unique_id=self._person,
            )
        guess = _guess_notify(self.hass, self._person)
        key = (
            vol.Required(CONF_NOTIFY_SERVICES, default=[guess])
            if guess
            else vol.Required(CONF_NOTIFY_SERVICES)
        )
        return self.async_show_form(
            step_id="notify",
            data_schema=vol.Schema({key: _notify_selector(self.hass)}),
            description_placeholders={"person": _person_label(self.hass, self._person)},
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        entry = self._get_entry()
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            data = {k: v for k, v in subentry.data.items() if k != CONF_NOTIFY}
            data[CONF_NOTIFY_SERVICES] = user_input[CONF_NOTIFY_SERVICES]
            return self.async_update_and_abort(entry, subentry, data=data)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema({vol.Required(CONF_NOTIFY_SERVICES): _notify_selector(self.hass)}),
                {CONF_NOTIFY_SERVICES: person_services(subentry.data)},
            ),
            description_placeholders={"person": subentry.title},
        )


# ----------------------------------------------------------------------
# Untereintrag: Gerät (nach Zustand oder nach Watt)
# ----------------------------------------------------------------------
class DeviceSubentryFlow(ConfigSubentryFlow):
    """Ein Abschnitt „Geräte“: beim Hinzufügen erst wählen, ob nach Zustand oder Watt.

    Hinzufügen und Bearbeiten nutzen dieselben Formulare (step_id „state“ / „power“).
    """

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_show_menu(step_id="user", menu_options=[TRIGGER_STATE, TRIGGER_POWER])

    async def async_step_state(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_form(TRIGGER_STATE, user_input)

    async def async_step_power(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_form(TRIGGER_POWER, user_input)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        sub = self._get_reconfigure_subentry()
        return await self._async_form(sub.data.get(CONF_TRIGGER, TRIGGER_STATE), user_input)

    async def _async_form(self, trigger: str, user_input: dict[str, Any] | None) -> SubentryFlowResult:
        entry = self._get_entry()
        reconfigure = self.source == SOURCE_RECONFIGURE
        power = trigger == TRIGGER_POWER
        schema = (_power_schema if power else _state_schema)(self.hass, entry)
        errors: dict[str, str] = {}
        if user_input is not None:
            if power and user_input[CONF_BELOW] >= user_input[CONF_ABOVE]:
                errors["base"] = "power_thresholds"
            elif not user_input.get(CONF_RECIPIENTS):
                errors[CONF_RECIPIENTS] = "no_recipients"
            elif msg_error := _message_error(
                self.hass, user_input.get(CONF_MESSAGE), user_input["name"].strip()
            ):
                errors[CONF_MESSAGE] = msg_error
            else:
                data = _clean_device(user_input)
                data[CONF_TRIGGER] = trigger
                title = user_input["name"].strip()
                if reconfigure:
                    return self.async_update_and_abort(
                        entry, self._get_reconfigure_subentry(), title=title, data=data
                    )
                return self.async_create_entry(title=title, data=data)

        suggested = user_input
        if suggested is None and reconfigure:
            sub = self._get_reconfigure_subentry()
            suggested = {**sub.data, "name": sub.title}
            if isinstance(msg := suggested.get(CONF_MESSAGE), str):
                # alte Schreibweise lesbar anzeigen; beim Speichern bleibt es gleichwertig
                suggested[CONF_MESSAGE] = _LEGACY_NAME.sub("[Name]", msg)
        return self.async_show_form(
            step_id=trigger,
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
            errors=errors,
        )


# ----------------------------------------------------------------------
# Untereintrag: Lautsprecher (Alexa oder TTS-Player)
# ----------------------------------------------------------------------
def _speaker_extras() -> dict[Any, Any]:
    return {
        vol.Required(CONF_ONLY_HOME, default=True): BooleanSelector(),
        vol.Optional(CONF_QUIET_FROM): TimeSelector(),
        vol.Optional(CONF_QUIET_TO): TimeSelector(),
    }


def _alexa_schema(hass: HomeAssistant) -> vol.Schema:
    options = [s for s in _notify_services(hass) if "alexa" in s]
    return vol.Schema(
        {
            vol.Required("name"): TextSelector(),
            vol.Required(CONF_NOTIFY): SelectSelector(
                SelectSelectorConfig(
                    options=options, mode=SelectSelectorMode.DROPDOWN, custom_value=True
                )
            ),
            **_speaker_extras(),
        }
    )


def _tts_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name"): TextSelector(),
            vol.Required(CONF_TTS_ENTITY): EntitySelector(EntitySelectorConfig(domain="tts")),
            vol.Required(CONF_PLAYER): EntitySelector(EntitySelectorConfig(domain="media_player")),
            **_speaker_extras(),
        }
    )


class SpeakerSubentryFlow(ConfigSubentryFlow):
    """Lautsprecher hinzufügen: Alexa-Gerät oder beliebiger Player mit TTS."""

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return self.async_show_menu(step_id="user", menu_options=[KIND_ALEXA, KIND_TTS])

    async def async_step_alexa(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_form(KIND_ALEXA, user_input)

    async def async_step_tts(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        return await self._async_form(KIND_TTS, user_input)

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None) -> SubentryFlowResult:
        sub = self._get_reconfigure_subentry()
        return await self._async_form(sub.data.get(CONF_KIND, KIND_ALEXA), user_input)

    async def _async_form(self, kind: str, user_input: dict[str, Any] | None) -> SubentryFlowResult:
        entry = self._get_entry()
        reconfigure = self.source == SOURCE_RECONFIGURE
        schema = _tts_schema() if kind == KIND_TTS else _alexa_schema(self.hass)
        if user_input is not None:
            data = {k: v for k, v in user_input.items() if k != "name" and v not in (None, "")}
            data[CONF_KIND] = kind
            title = user_input["name"].strip()
            if reconfigure:
                return self.async_update_and_abort(
                    entry, self._get_reconfigure_subentry(), title=title, data=data
                )
            return self.async_create_entry(title=title, data=data)

        suggested = None
        if reconfigure:
            sub = self._get_reconfigure_subentry()
            suggested = {**sub.data, "name": sub.title}
        return self.async_show_form(
            step_id=kind,
            data_schema=self.add_suggested_values_to_schema(schema, suggested),
        )
