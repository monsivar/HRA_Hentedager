"""HRA collection calendar."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CALENDAR_NAME, DOMAIN, WASTE_EMOJIS
from .coordinator import HraCoordinator


def _event_summary(waste_type: str) -> str:
    """Return a readable calendar title with a fraction emoji."""
    emoji = WASTE_EMOJIS.get(waste_type, "♻️")
    return f"{emoji} HRA: {waste_type}"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the HRA calendar."""
    async_add_entities([HraCalendar(hass.data[DOMAIN][entry.entry_id])])


class HraCalendar(CoordinatorEntity[HraCoordinator], CalendarEntity):
    """All HRA collections as all-day calendar events."""

    def __init__(self, coordinator: HraCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_name = CALENDAR_NAME
        self._attr_unique_id = f"{coordinator.agreement_guid}_calendar"
        self._attr_device_info = coordinator.collection_days_device_info

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next event shown in the calendar entity state."""
        events = self.coordinator.all_future()
        if not events:
            return None
        waste_type, event_date = events[0]
        return CalendarEvent(
            summary=_event_summary(waste_type),
            start=event_date,
            end=event_date + timedelta(days=1),
        )

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return all HRA events within the requested time range."""
        start = start_date.date()
        end = end_date.date()
        return [
            CalendarEvent(
                summary=_event_summary(waste_type),
                start=collection_date,
                end=collection_date + timedelta(days=1),
                description=self.coordinator.property_data.get("name"),
                location=self.coordinator.property_data.get("name"),
            )
            for waste_type, collection_date in self.coordinator.all_future()
            if start <= collection_date < end
        ]
