from __future__ import annotations

from dataclasses import dataclass

from pymodbus.server import StartTcpServer
from pymodbus.simulator import DataType, SimData, SimDevice

from .protocol import REGISTER_SPECS


@dataclass(frozen=True)
class SimulatorProfile:
    ua_raw: int = 2300
    ub_raw: int = 2296
    uc_raw: int = 2304
    ia_raw: int = 320
    ib_raw: int = 305
    ic_raw: int = 315
    pa_raw: int = 740
    pb_raw: int = 700
    pc_raw: int = 720
    qa_raw: int = 130
    qb_raw: int = 120
    qc_raw: int = 125
    sa_raw: int = 760
    sb_raw: int = 720
    sc_raw: int = 742
    pf_total_raw: int = 930
    pf_a_raw: int = 925
    pf_b_raw: int = 920
    pf_c_raw: int = 928
    fra_raw: int = 5000
    frb_raw: int = 5001
    frc_raw: int = 4999
    e_total_raw: int = 4600
    e_import_total_raw: int = 4600
    e_export_total_raw: int = 100
    eq_total_raw: int = 860
    eq_import_total_raw: int = 850
    eq_export_total_raw: int = 10


def _encode_signed_16(value: int) -> int:
    return value & 0xFFFF


def _encode_signed_32_words(value: int) -> tuple[int, int]:
    encoded = value & 0xFFFFFFFF
    return ((encoded >> 16) & 0xFFFF, encoded & 0xFFFF)


def _raw_values_by_key(profile: SimulatorProfile) -> dict[str, int]:
    p_total = profile.pa_raw + profile.pb_raw + profile.pc_raw
    q_total = profile.qa_raw + profile.qb_raw + profile.qc_raw
    s_total = profile.sa_raw + profile.sb_raw + profile.sc_raw
    return {
        "Ua": profile.ua_raw,
        "Ub": profile.ub_raw,
        "Uc": profile.uc_raw,
        "Ia": profile.ia_raw,
        "Ib": profile.ib_raw,
        "Ic": profile.ic_raw,
        "P_total": p_total,
        "Pa": profile.pa_raw,
        "Pb": profile.pb_raw,
        "Pc": profile.pc_raw,
        "Q_total": q_total,
        "Qa": profile.qa_raw,
        "Qb": profile.qb_raw,
        "Qc": profile.qc_raw,
        "S_total": s_total,
        "Sa": profile.sa_raw,
        "Sb": profile.sb_raw,
        "Sc": profile.sc_raw,
        "PF_total": profile.pf_total_raw,
        "PF_a": profile.pf_a_raw,
        "PF_b": profile.pf_b_raw,
        "PF_c": profile.pf_c_raw,
        "FRa": profile.fra_raw,
        "FRb": profile.frb_raw,
        "FRc": profile.frc_raw,
        "E_total": profile.e_total_raw,
        "E_import_total": profile.e_import_total_raw,
        "E_export_total": profile.e_export_total_raw,
        "EQ_total": profile.eq_total_raw,
        "EQ_import_total": profile.eq_import_total_raw,
        "EQ_export_total": profile.eq_export_total_raw,
    }


def build_input_register_words(profile: SimulatorProfile | None = None) -> dict[int, int]:
    active_profile = profile or SimulatorProfile()
    raw_values = _raw_values_by_key(active_profile)
    max_address = max(spec.address + spec.words - 1 for spec in REGISTER_SPECS)
    registers: dict[int, int] = {addr: 0 for addr in range(0x00, max_address + 1)}
    for spec in REGISTER_SPECS:
        raw_value = raw_values[spec.key]
        if spec.words == 1:
            registers[spec.address] = _encode_signed_16(raw_value)
            continue
        high, low = _encode_signed_32_words(raw_value)
        registers[spec.address] = high
        registers[spec.address + 1] = low
    return registers


def build_pymodbus_sim_device(device_id: int = 1, profile: SimulatorProfile | None = None) -> SimDevice:
    words = build_input_register_words(profile)
    max_address = max(words)
    values = [words.get(addr, 0) for addr in range(max_address + 1)]
    return SimDevice(
        id=device_id,
        simdata=[SimData(address=0, values=values, datatype=DataType.REGISTERS)],
    )


def run_pymodbus_simulator(host: str = "127.0.0.1", port: int = 5020, device_id: int = 1) -> None:
    """Run a foreground TCP simulator process for local TUI debugging.

    This call is intentionally blocking (StartTcpServer) and should be run in
    a dedicated terminal/session.
    """
    device = build_pymodbus_sim_device(device_id=device_id)
    StartTcpServer(device, address=(host, port))
