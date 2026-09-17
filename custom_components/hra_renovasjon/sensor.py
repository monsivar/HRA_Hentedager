"""HRA waste collection sensors."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ASSET_BASE_URL,
    ASSET_FILES,
    ATTR_ADDRESS,
    ATTR_AGREEMENT_GUID,
    ATTR_DAYS_UNTIL,
    ATTR_NEXT_COLLECTION,
    ATTR_UPCOMING,
    ATTR_WASTE_TYPE,
    DOMAIN,
    FALLBACK_ICONS,
    ICON,
)
from .coordinator import HraCoordinator, days_until


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the summary and one sensor per waste fraction."""
    coordinator: HraCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [HraSummarySensor(coordinator)]
    entities.extend(
        HraFractionSensor(coordinator, category) for category in coordinator.categories()
    )
    async_add_entities(entities)


class HraSensorBase(CoordinatorEntity[HraCoordinator], SensorEntity):
    """Shared device and update behavior."""

    _attr_icon = ICON
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: HraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info


class HraFractionSensor(HraSensorBase):
    """Next collection sensor for one HRA waste fraction."""

    def __init__(self, coordinator: HraCoordinator, category: str) -> None:
        super().__init__(coordinator)
        self.category = category
        self._attr_name = f"HRA {category}"
        self._attr_unique_id = f"{coordinator.agreement_guid}_{coordinator.category_id(category)}"
        self._attr_icon = FALLBACK_ICONS.get(category, ICON)
        asset = ASSET_FILES.get(category)
        if asset:
            self._attr_entity_picture = f"{ASSET_BASE_URL}/{asset}"

    @property
    def native_value(self) -> date | None:
        """Return the next collection date."""
        upcoming = self.coordinator.next_for(self.category)
        return upcoming[0] if upcoming else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose useful dates without forcing date formatting in automations."""
        upcoming = self.coordinator.next_for(self.category)
        if not upcoming:
            return {ATTR_WASTE_TYPE: self.category}
        next_date, following = upcoming
        return {
            ATTR_WASTE_TYPE: self.category,
            ATTR_NEXT_COLLECTION: next_date.isoformat(),
            ATTR_DAYS_UNTIL: days_until(next_date),
            ATTR_UPCOMING: [next_date.isoformat(), *(item.isoformat() for item in following[:5])],
        }


class HraSummarySensor(HraSensorBase):
    """Summary sensor for the next collection of any fraction."""

    def __init__(self, coordinator: HraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = "HRA neste henting"
        self._attr_unique_id = f"{coordinator.agreement_guid}_next_collection"

    @property
    def native_value(self) -> date | None:
        """Return the earliest upcoming date."""
        events = self.coordinator.all_future()
        return events[0][1] if events else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose address and the next type for automations and dashboards."""
        events = self.coordinator.all_future()
        first = events[0] if events else None
        return {
            ATTR_ADDRESS: self.coordinator.property_data.get("name"),
            ATTR_AGREEMENT_GUID: self.coordinator.agreement_guid,
            ATTR_WASTE_TYPE: first[0] if first else None,
            ATTR_NEXT_COLLECTION: first[1].isoformat() if first else None,
            ATTR_DAYS_UNTIL: days_until(first[1]) if first else None,
            ATTR_UPCOMING: [
                {"waste_type": waste_type, "date": item.isoformat()}
                for waste_type, item in events[:15]
            ],
        }
