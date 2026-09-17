"""Small async client for the public HRA API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aiohttp import ClientSession

from .const import API_BASE_URL


class HraApiError(Exception):
    """Raised when HRA returns an invalid or unsuccessful response."""


@dataclass(frozen=True)
class HraProperty:
    """An address/property returned by HRA's address search."""

    property_guid: str
    agreement_guid: str
    name: str
    municipality: str | None = None
    postal_number: int | None = None
    postal_place: str | None = None
    gnr_bnr_fnr_snr: str | None = None

    @property
    def display_name(self) -> str:
        """Return the address as it should be shown to the user."""
        return self.name

    def as_dict(self) -> dict[str, Any]:
        """Serialize the property for config-entry storage."""
        return {
            "property_guid": self.property_guid,
            "agreement_guid": self.agreement_guid,
            "name": self.name,
            "municipality": self.municipality,
            "postal_number": self.postal_number,
            "postal_place": self.postal_place,
            "gnr_bnr_fnr_snr": self.gnr_bnr_fnr_snr,
        }


@dataclass(frozen=True)
class HraCollection:
    """A single upcoming collection."""

    name: str
    date: str
    raw: dict[str, Any]


class HraApi:
    """API client kept deliberately narrow so it is easy to test."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get_json(self, path: str) -> Any:
        try:
            async with self._session.get(
                f"{API_BASE_URL}/{path.lstrip('/')}",
                headers={"Accept": "application/json"},
            ) as response:
                if response.status >= 400:
                    raise HraApiError(f"HRA returned HTTP {response.status}")
                return await response.json(content_type=None)
        except HraApiError:
            raise
        except Exception as err:
            raise HraApiError("Could not reach HRA") from err

    async def search_address(self, query: str) -> list[HraProperty]:
        """Search HRA properties by free-text address."""
        # aiohttp handles query encoding and avoids hand-built URL bugs.
        try:
            async with self._session.get(
                f"{API_BASE_URL}/search/address",
                params={"query": query},
                headers={"Accept": "application/json"},
            ) as response:
                if response.status >= 400:
                    raise HraApiError(f"HRA returned HTTP {response.status}")
                payload = await response.json(content_type=None)
        except HraApiError:
            raise
        except Exception as err:
            raise HraApiError("Could not search HRA addresses") from err

        if not isinstance(payload, list):
            raise HraApiError("HRA returned an unexpected address response")

        properties: list[HraProperty] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            property_guid = item.get("propertyGuid")
            agreement_guid = item.get("agreementGuid")
            name = item.get("name") or item.get("propertyName")
            if not property_guid or not agreement_guid or not name:
                continue
            properties.append(
                HraProperty(
                    property_guid=str(property_guid),
                    agreement_guid=str(agreement_guid),
                    name=str(name),
                    municipality=item.get("municipality"),
                    postal_number=item.get("postalNumber"),
                    postal_place=item.get("postalPlace"),
                    gnr_bnr_fnr_snr=item.get("gnrBnrFnrSnr"),
                )
            )
        return properties

    async def upcoming_collections(self, agreement_guid: str) -> list[HraCollection]:
        """Fetch upcoming collections for an HRA agreement."""
        payload = await self._get_json(
            f"Renovation/UpcomingGarbageDisposals/{agreement_guid}"
        )
        if not isinstance(payload, list):
            raise HraApiError("HRA returned an unexpected collection response")

        collections: list[HraCollection] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            date = item.get("date")
            if name and date:
                collections.append(
                    HraCollection(str(name), str(date), dict(item))
                )
        return collections
