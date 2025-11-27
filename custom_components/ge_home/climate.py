"""Entidad de clima para aires acondicionados GE Home.

Esta implementación mínima mantiene los mapeos entre ERD y modos HVAC,
permitiendo pruebas fuera de Home Assistant mientras se preservan las
traducciones necesarias para operar el modo calor.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from gehomesdk.erd.erd_codes import ErdCode
from gehomesdk.erd.values.ac.common_enums import (
    ErdAcAvailableModes,
    ErdAcOperationMode,
)


class HVACMode(str, Enum):
    """Equivalente simplificado de ``homeassistant.components.climate.HVACMode``."""

    AUTO = "auto"
    COOL = "cool"
    DRY = "dry"
    FAN_ONLY = "fan_only"
    HEAT = "heat"


AC_TO_HVAC_MODE = {
    ErdAcOperationMode.AUTO: HVACMode.AUTO,
    ErdAcOperationMode.COOL: HVACMode.COOL,
    ErdAcOperationMode.DRY: HVACMode.DRY,
    ErdAcOperationMode.ENERGY_SAVER: HVACMode.COOL,
    ErdAcOperationMode.FAN_ONLY: HVACMode.FAN_ONLY,
    ErdAcOperationMode.HEAT: HVACMode.HEAT,
}

HVAC_MODE_TO_AC = {
    HVACMode.AUTO: ErdAcOperationMode.AUTO,
    HVACMode.COOL: ErdAcOperationMode.COOL,
    HVACMode.DRY: ErdAcOperationMode.DRY,
    HVACMode.FAN_ONLY: ErdAcOperationMode.FAN_ONLY,
    HVACMode.HEAT: ErdAcOperationMode.HEAT,
}


@dataclass
class GeHomeClimate:
    """Entidad de clima simplificada basada en ERD.

    Se utiliza principalmente para validar la traducción de modos y setpoints
    en pruebas, sin depender de la instalación completa de Home Assistant.
    """

    appliance: "FakeApplianceProtocol"

    @property
    def hvac_mode(self) -> HVACMode:
        ac_mode = self.appliance.get_erd_value(ErdCode.AC_OPERATION_MODE)
        return AC_TO_HVAC_MODE.get(ac_mode, HVACMode.AUTO)

    @property
    def hvac_modes(self) -> List[HVACMode]:
        available = self.appliance.get_erd_value(ErdCode.AC_AVAILABLE_MODES)
        return build_hvac_modes(available)

    @property
    def target_temperature_code(self) -> ErdCode:
        if self.hvac_mode == HVACMode.HEAT:
            return ErdCode.AC_TARGET_HEATING_TEMPERATURE
        return ErdCode.AC_TARGET_TEMPERATURE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        ac_mode = HVAC_MODE_TO_AC.get(hvac_mode)
        if ac_mode is None:
            raise ValueError(f"Modo HVAC no soportado: {hvac_mode}")

        await self.appliance.async_set_erd_value(ErdCode.AC_OPERATION_MODE, ac_mode)

    async def async_set_temperature(self, *, temperature: float) -> None:
        target_code = self.target_temperature_code
        await self.appliance.async_set_erd_value(target_code, temperature)


def build_hvac_modes(available: Optional[ErdAcAvailableModes]) -> List[HVACMode]:
    """Construye la lista de modos HVAC según los modos disponibles ERD."""

    if available is None:
        return [HVACMode.COOL, HVACMode.FAN_ONLY]

    hvac_modes: List[HVACMode] = []

    if available.has_auto:
        hvac_modes.append(HVACMode.AUTO)
    if available.has_cool:
        hvac_modes.append(HVACMode.COOL)
    if available.has_dry:
        hvac_modes.append(HVACMode.DRY)
    if available.has_fan:
        hvac_modes.append(HVACMode.FAN_ONLY)
    if available.has_heat:
        hvac_modes.append(HVACMode.HEAT)

    return hvac_modes


class FakeApplianceProtocol:
    """Protocolo mínimo para las pruebas de clima."""

    def get_erd_value(self, erd_code: ErdCode):
        raise NotImplementedError

    async def async_set_erd_value(self, erd_code: ErdCode, value):
        raise NotImplementedError
