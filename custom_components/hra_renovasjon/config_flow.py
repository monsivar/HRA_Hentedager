"""Config flow for HRA renovasjon."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import selector

from .api import HraApi, HraApiError, HraProperty
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


def _interval_schema(default: int = DEFAULT_SCAN_INTERVAL) -> vol.Schema:
    """Build the shared update interval schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_SCAN_INTERVAL, default=default
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL,
                    max=MAX_SCAN_INTERVAL,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="timer.hours",
                )
            )
        }
    )


class HraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle HRA setup through the Home Assistant UI."""

    VERSION = 1

    def __init__(self) -> None:
        self._properties: list[HraProperty] = []
        self._address: str = ""
        self._scan_interval: int = DEFAULT_SCAN_INTERVAL

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for an address and search HRA."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._address = user_input[CONF_ADDRESS].strip()
            self._scan_interval = int(user_input[CONF_SCAN_INTERVAL])
            if not self._address:
                errors[CONF_ADDRESS] = "invalid_address"
            else:
                try:
                    self._properties = await HraApi(
                        async_get_clientsession(self.hass)
                    ).search_address(self._address)
                except HraApiError:
                    errors["base"] = "cannot_connect"
                else:
                    if not self._properties:
                        errors[CONF_ADDRESS] = "address_not_found"
                    elif len(self._properties) == 1:
                        return await self._async_create_entry(self._properties[0])
                    else:
                        return await self.async_step_select_address()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): str,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                            step=1,
                            mode=selector.NumberSelectorMode.BOX,
                            unit_of_measurement="timer.hours",
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_select_address(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Let the user disambiguate several HRA address matches."""
        if user_input is not None:
            selected = self._properties[int(user_input["property"])]
            return await self._async_create_entry(selected)

        options = {
            str(index): property_.display_name
            for index, property_ in enumerate(self._properties)
        }
        return self.async_show_form(
            step_id="select_address",
            data_schema=vol.Schema(
                {
                    vol.Required("property"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=value, label=label)
                                for value, label in options.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def _async_create_entry(self, property_: HraProperty) -> ConfigFlowResult:
        """Create the selected HRA config entry."""
        await self.async_set_unique_id(property_.agreement_guid)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"HRA – {property_.name}",
            data={
                "agreement_guid": property_.agreement_guid,
                "property": property_.as_dict(),
                CONF_ADDRESS: self._address,
                CONF_SCAN_INTERVAL: self._scan_interval,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Return the options flow."""
        return HraOptionsFlow()


class HraOptionsFlow(config_entries.OptionsFlow):
    """Allow the update interval to be changed after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init", data_schema=_interval_schema(int(current))
        )
