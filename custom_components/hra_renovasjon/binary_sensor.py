"""Binary sensor for HRA collection days."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import HraCoordinator, days_label

_ATTRIBUTE_KEYS = {
    "Restavfall": "rest",
    "Matavfall": "mat",
    "Papir, papp og kartong": "papir",
    "Glass- og metallemballasje": "glass",
    "Plastemballasje": "plast",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HRA collection-day binary sensor."""
    async_add_entities(
        [HraCollectionDaySensor(hass.data[DOMAIN][entry.entry_id])]
    )


class HraCollectionDaySensor(
    CoordinatorEntity[HraCoordinator], BinarySensorEntity
):
    """Be on when one or more HRA fractions are collected today."""

    _attr_name = "HRA hentedag"
    _attr_icon = "mdi:calendar-check-outline"

    def __init__(self, coordinator: HraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.agreement_guid}_collection_day"
        self._attr_device_info = coordinator.collection_days_device_info

    @property
    def is_on(self) -> bool:
        """Return true when at least one fraction is collected today."""
        today = dt_util.now().date()
        return any(
            collection_date == today
            for _name, collection_date in self.coordinator.all_future()
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the next collection label for each automation-friendly key."""
        attributes: dict[str, Any] = {}
        today = dt_util.now().date()
        for category, attribute_key in _ATTRIBUTE_KEYS.items():
            upcoming = self.coordinator.next_for(category)
            if upcoming:
                attributes[attribute_key] = days_label((upcoming[0] - today).days)
        return attributes
