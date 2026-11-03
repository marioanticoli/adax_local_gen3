import logging
from typing import Any, cast

from adax_local import Adax as AdaxLocal

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_IP_ADDRESS, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class AdaxGen3Coordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name="Adax Gen 3",
            update_interval=SCAN_INTERVAL,
            config_entry=entry,
        )

        self.adax_data_handler = AdaxLocal(
            entry.data[CONF_IP_ADDRESS],
            entry.data[CONF_TOKEN],
            websession=async_get_clientsession(
                hass, verify_ssl=False
            ),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            result = await self.adax_data_handler.get_status()
        except Exception as err:
            raise UpdateFailed(
                f"Error communicating with Adax heater: {err}"
            ) from err

        if result:
            return cast(dict[str, Any], result)

        raise UpdateFailed("Got invalid status from device")

