"""Coordinator and date normalization for HRA data."""

from __future__ import annotations

from datetime import date, timedelta
import logging
from typing import Any

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .api import HraApi, HraApiError, HraCollection
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def parse_collection_date(value: str) -> date | None:
    """Parse HRA's ISO date/datetime into a local calendar date."""
    parsed = dt_util.parse_datetime(value)
    if parsed is not None:
        if parsed.tzinfo is None:
            return parsed.date()
        return dt_util.as_local(parsed).date()
    parsed_date = dt_util.parse_date(value[:10])
    return parsed_date


def days_until(target: date, today: date | None = None) -> int:
    """Return the number of local calendar days until target."""
    return (target - (today or dt_util.now().date())).days


def days_label(number: int) -> str:
    """Return the Norwegian label used by the Node-RED sensor."""
    if number == 0:
        return "I dag"
    if number == 1:
        return "I morgen"
    return f"{number} dager"


class HraCoordinator(DataUpdateCoordinator[list[HraCollection]]):
    """Fetch HRA data and share one normalized result with all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        agreement_guid: str,
        property_data: dict[str, Any],
        update_interval: timedelta,
        config_entry_id: str,
    ) -> None:
        self.agreement_guid = agreement_guid
        self.property_data = property_data
        self.config_entry_id = config_entry_id
        self.api = HraApi(async_get_clientsession(hass))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return the shared Home Assistant device description."""
        return {
            "identifiers": {(DOMAIN, self.agreement_guid)},
            "name": "Hentedager av HRA",
            "model": "Custom component basert på åpne data fra monsivar",
            "configuration_url": "https://github.com/monsivar/HRA_Hentedager",
        }

    @property
    def collection_days_device_info(self) -> dict[str, Any]:
        """Return the separate device description for day/calendar entities."""
        device_info: dict[str, Any] = {
            "identifiers": {(DOMAIN, f"{self.agreement_guid}_collection_days")},
            "name": "HRA hentedag og kalender",
            "model": "Custom component basert på åpne data fra monsivar",
            "configuration_url": "https://github.com/monsivar/HRA_Hentedager",
        }
        if parent_device_id := dr.async_get_device_id_by_identifier(
            self.hass,
            (DOMAIN, self.agreement_guid),
            config_entry_id=self.config_entry_id,
        ):
            device_info["via_device_id"] = parent_device_id
        return device_info

    async def _async_update_data(self) -> list[HraCollection]:
        try:
            return await self.api.upcoming_collections(self.agreement_guid)
        except HraApiError as err:
            raise UpdateFailed(str(err)) from err

    def grouped(self) -> dict[str, list[tuple[date, dict[str, Any]]]]:
        """Group valid collections by the waste fraction name."""
        grouped: dict[str, list[tuple[date, dict[str, Any]]]] = {}
        for collection in self.data or []:
            collection_date = parse_collection_date(collection.date)
            if collection_date is None:
                _LOGGER.warning("Ignoring invalid HRA date: %s", collection.date)
                continue
            grouped.setdefault(collection.name, []).append(
                (collection_date, collection.raw)
            )
        for values in grouped.values():
            values.sort(key=lambda item: item[0])
        return grouped

    def categories(self) -> list[str]:
        """Return categories in a stable order, with API additions included."""
        preferred = [
            "Restavfall",
            "Matavfall",
            "Plastemballasje",
            "Papir, papp og kartong",
            "Glass- og metallemballasje",
        ]
        known = set(self.grouped())
        return preferred + sorted(
            known - set(preferred)
        )

    def category_id(self, category: str) -> str:
        """Return a stable entity-id fragment for a category."""
        return slugify(category)

    def next_for(self, category: str) -> tuple[date, list[date]] | None:
        """Return the next date and following dates for a category."""
        values = self.grouped().get(category, [])
        future = [item[0] for item in values if item[0] >= dt_util.now().date()]
        if not future:
            return None
        return future[0], future[1:]

    def all_future(self) -> list[tuple[str, date]]:
        """Return all future collections sorted by date."""
        result = [
            (category, collection_date)
            for category, values in self.grouped().items()
            for collection_date, _raw in values
            if collection_date >= dt_util.now().date()
        ]
        return sorted(result, key=lambda item: (item[1], item[0]))
