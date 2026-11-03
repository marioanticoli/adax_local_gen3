from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_UNIQUE_ID,
    PRECISION_WHOLE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import (
    AddConfigEntryEntitiesCallback,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import AdaxGen3Coordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([
        AdaxGen3Climate(
            coordinator,
            entry.data[CONF_UNIQUE_ID],
        )
    ])


class AdaxGen3Climate(
    CoordinatorEntity[AdaxGen3Coordinator],
    ClimateEntity,
):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_hvac_mode = HVACMode.OFF
    _attr_icon = "mdi:radiator-off"
    _attr_max_temp = 35
    _attr_min_temp = 5
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_target_temperature_step = PRECISION_WHOLE
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(
        self,
        coordinator: AdaxGen3Coordinator,
        unique_id: str,
    ) -> None:
        super().__init__(coordinator)

        self.adax = coordinator.adax_data_handler
        self._attr_unique_id = unique_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer="Adax",
        )

    async def async_set_hvac_mode(
        self, hvac_mode: HVACMode
    ) -> None:
        if hvac_mode == HVACMode.HEAT:
            temperature = (
                self._attr_native_target_temperature
                or self._attr_min_temp
            )
            await self.adax.set_target_temperature(temperature)
        elif hvac_mode == HVACMode.OFF:
            await self.adax.set_target_temperature(0)
        else:
            return

        self._attr_hvac_mode = hvac_mode
        await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        if self._attr_hvac_mode == HVACMode.HEAT:
            await self.adax.set_target_temperature(temperature)

        self._attr_native_target_temperature = temperature
        self.async_write_ha_state()

    def _update_hvac_attributes(self) -> None:
        if not self.coordinator.data:
            return

        data = self.coordinator.data
        self._attr_native_current_temperature = data[
            "current_temperature"
        ]

        target = data["target_temperature"]

        if target == 0:
            self._attr_hvac_mode = HVACMode.OFF
            self._attr_icon = "mdi:radiator-off"
            if self._attr_native_target_temperature is None:
                self._attr_native_target_temperature = self._attr_min_temp
        else:
            self._attr_hvac_mode = HVACMode.HEAT
            self._attr_icon = "mdi:radiator"
            self._attr_native_target_temperature = target

    @callback
    def _handle_coordinator_update(self) -> None:
        self._update_hvac_attributes()
        super()._handle_coordinator_update()

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._update_hvac_attributes()

