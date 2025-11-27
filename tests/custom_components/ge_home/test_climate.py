import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[3]))

from custom_components.ge_home.climate import (
    AC_TO_HVAC_MODE,
    HVAC_MODE_TO_AC,
    FakeApplianceProtocol,
    GeHomeClimate,
    HVACMode,
    build_hvac_modes,
)
from gehomesdk.erd.erd_codes import ErdCode
from gehomesdk.erd.values.ac.common_enums import ErdAcAvailableModes, ErdAcOperationMode


class FakeAppliance(FakeApplianceProtocol):
    def __init__(self):
        self.erd_values = {}
        self.calls = []

    def get_erd_value(self, erd_code: ErdCode):
        return self.erd_values.get(erd_code)

    async def async_set_erd_value(self, erd_code: ErdCode, value):
        self.calls.append((erd_code, value))
        self.erd_values[erd_code] = value


def test_operation_mode_maps_heat_correctly():
    assert AC_TO_HVAC_MODE[ErdAcOperationMode.HEAT] == HVACMode.HEAT
    assert HVAC_MODE_TO_AC[HVACMode.HEAT] == ErdAcOperationMode.HEAT


def test_heat_only_included_when_available():
    available_with_heat = ErdAcAvailableModes(
        has_heat=True,
        has_dry=False,
        has_eco=False,
        has_turbo_cool=False,
        has_silent=False,
        has_auto=False,
        has_cool=True,
        has_fan=True,
        raw_value="0x7b00",
    )
    available_without_heat = ErdAcAvailableModes(
        has_heat=False,
        has_dry=False,
        has_eco=False,
        has_turbo_cool=False,
        has_silent=False,
        has_auto=False,
        has_cool=True,
        has_fan=True,
        raw_value="0x7b00",
    )

    assert HVACMode.HEAT in build_hvac_modes(available_with_heat)
    assert HVACMode.HEAT not in build_hvac_modes(available_without_heat)


@pytest.mark.asyncio
async def test_set_hvac_mode_heat_writes_operation_and_heating_target():
    appliance = FakeAppliance()
    appliance.erd_values[ErdCode.AC_AVAILABLE_MODES] = ErdAcAvailableModes(
        has_heat=True,
        has_dry=False,
        has_eco=False,
        has_turbo_cool=False,
        has_silent=False,
        has_auto=False,
        has_cool=True,
        has_fan=True,
        raw_value="0x7b00",
    )
    appliance.erd_values[ErdCode.AC_OPERATION_MODE] = ErdAcOperationMode.COOL
    climate = GeHomeClimate(appliance)

    await climate.async_set_hvac_mode(HVACMode.HEAT)
    await climate.async_set_temperature(temperature=21)

    assert appliance.calls[0] == (ErdCode.AC_OPERATION_MODE, ErdAcOperationMode.HEAT)
    assert appliance.calls[1] == (ErdCode.AC_TARGET_HEATING_TEMPERATURE, 21)
