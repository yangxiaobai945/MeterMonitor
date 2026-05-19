from __future__ import annotations

from metermonitor.parser import parse_registers
from metermonitor.protocol import REGISTER_SPECS
from metermonitor.simulator import MeterProtocolSimulator


def test_simulator_covers_all_protocol_register_specs() -> None:
    simulator = MeterProtocolSimulator()
    raw_registers = simulator.snapshot_registers()

    for spec in REGISTER_SPECS:
        assert spec.address in raw_registers
        if spec.words == 2:
            assert spec.address + 1 in raw_registers


def test_simulator_registers_can_be_parsed_to_engineering_values() -> None:
    simulator = MeterProtocolSimulator()
    parsed = parse_registers(simulator.snapshot_registers())

    for spec in REGISTER_SPECS:
        assert spec.key in parsed.values
    assert parsed.values["Ua"] > 0
    assert parsed.values["Ia"] > 0
    assert parsed.values["E_total"] >= 0
    assert 0 <= parsed.values["PF_total"] <= 1.2


def test_simulator_advance_increases_energy() -> None:
    simulator = MeterProtocolSimulator()
    before = parse_registers(simulator.snapshot_registers()).values

    simulator.advance()
    after = parse_registers(simulator.snapshot_registers()).values

    assert after["E_total"] > before["E_total"]
    assert after["E_import_total"] > before["E_import_total"]
    assert after["EQ_total"] > before["EQ_total"]


def test_simulator_read_input_registers_matches_snapshot_window() -> None:
    simulator = MeterProtocolSimulator()
    snapshot = simulator.snapshot_registers()

    start = 0x00
    count = 29
    expected = [snapshot[start + i] for i in range(count)]

    assert simulator.read_input_registers(start, count) == expected

