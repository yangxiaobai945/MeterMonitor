from __future__ import annotations

import pytest

from metermonitor.parser import parse_registers
from metermonitor.protocol import REGISTER_SPECS
from metermonitor.simulator import (
    SimulatorProfile,
    build_input_register_words,
    build_pymodbus_sim_device,
)


def test_build_input_register_words_covers_protocol_specs() -> None:
    raw_registers = build_input_register_words()

    for spec in REGISTER_SPECS:
        assert spec.address in raw_registers
        if spec.words == 2:
            assert spec.address + 1 in raw_registers


def test_build_input_register_words_can_be_parsed_to_engineering_values() -> None:
    parsed = parse_registers(build_input_register_words())

    for spec in REGISTER_SPECS:
        assert spec.key in parsed.values
    assert parsed.values["Ua"] > 0
    assert parsed.values["Ia"] > 0
    assert parsed.values["E_total"] >= 0
    assert 0 <= parsed.values["PF_total"] <= 1.2


def test_build_input_register_words_supports_custom_profile() -> None:
    profile = SimulatorProfile(ua_raw=2215, ia_raw=180, e_total_raw=9999)
    parsed = parse_registers(build_input_register_words(profile))

    assert parsed.values["Ua"] == 221.5
    assert parsed.values["Ia"] == 1.8
    assert parsed.values["E_total"] == pytest.approx(99.99)


def test_build_pymodbus_sim_device_populates_input_register_block() -> None:
    device = build_pymodbus_sim_device(device_id=3)
    registers = device.build_device()

    assert registers[0] == 0
    assert len(registers[1]) > 0
    assert registers[1][0] > 0
