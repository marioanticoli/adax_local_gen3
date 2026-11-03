import logging
from typing import Any

from . import adax_local
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_TOKEN,
    CONF_UNIQUE_ID,
)
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    CONF_WIFI_PASSWORD,
    CONF_WIFI_SSID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AdaxGen3ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        schema = vol.Schema({
            vol.Required(CONF_WIFI_SSID): str,
            vol.Required(CONF_WIFI_PASSWORD): TextSelector(
                TextSelectorConfig(
                    type=TextSelectorType.PASSWORD,
                    autocomplete="current-password",
                )
            ),
        })

        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
            )

        configurator = adax_local.AdaxConfig(
            user_input[CONF_WIFI_SSID],
            user_input[CONF_WIFI_PASSWORD].replace(" ", ""),
        )

        try:
            device_configured = await configurator.configure_device()
        except adax_local.HeaterNotAvailable:
            return self.async_abort(reason="heater_not_available")
        except adax_local.HeaterNotFound:
            return self.async_abort(reason="heater_not_found")
        except adax_local.InvalidWifiCred:
            return self.async_abort(reason="invalid_auth")

        if not device_configured:
            return self.async_show_form(
                step_id="user",
                data_schema=schema,
                errors={"base": "cannot_connect"},
            )

        unique_id = str(configurator.mac_id)

        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Adax {unique_id}",
            data={
                CONF_IP_ADDRESS: configurator.device_ip,
                CONF_TOKEN: configurator.access_token,
                CONF_UNIQUE_ID: unique_id,
            },
        )

