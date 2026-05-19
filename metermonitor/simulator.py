from __future__ import annotations

from dataclasses import dataclass, field

from .protocol import REGISTER_SPECS


def _encode_signed_16(value: int) -> int:
    return value & 0xFFFF


def _encode_signed_32_words(value: int) -> tuple[int, int]:
    encoded = value & 0xFFFFFFFF
    return ((encoded >> 16) & 0xFFFF, encoded & 0xFFFF)


@dataclass
class MeterProtocolSimulator:
    """
    基于 doc/电表协议.tsv 的寄存器模拟器（输入寄存器，功能码 0x04）。
    对外提供与客户端一致的 read_input_registers 读取能力，便于测试与联调。
    """

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
    _tick: int = field(default=0, init=False, repr=False)

    def snapshot_registers(self) -> dict[int, int]:
        p_total = self.pa_raw + self.pb_raw + self.pc_raw
        q_total = self.qa_raw + self.qb_raw + self.qc_raw
        s_total = self.sa_raw + self.sb_raw + self.sc_raw

        raw_values_by_key: dict[str, int] = {
            "Ua": self.ua_raw,
            "Ub": self.ub_raw,
            "Uc": self.uc_raw,
            "Ia": self.ia_raw,
            "Ib": self.ib_raw,
            "Ic": self.ic_raw,
            "P_total": p_total,
            "Pa": self.pa_raw,
            "Pb": self.pb_raw,
            "Pc": self.pc_raw,
            "Q_total": q_total,
            "Qa": self.qa_raw,
            "Qb": self.qb_raw,
            "Qc": self.qc_raw,
            "S_total": s_total,
            "Sa": self.sa_raw,
            "Sb": self.sb_raw,
            "Sc": self.sc_raw,
            "PF_total": self.pf_total_raw,
            "PF_a": self.pf_a_raw,
            "PF_b": self.pf_b_raw,
            "PF_c": self.pf_c_raw,
            "FRa": self.fra_raw,
            "FRb": self.frb_raw,
            "FRc": self.frc_raw,
            "E_total": self.e_total_raw,
            "E_import_total": self.e_import_total_raw,
            "E_export_total": self.e_export_total_raw,
            "EQ_total": self.eq_total_raw,
            "EQ_import_total": self.eq_import_total_raw,
            "EQ_export_total": self.eq_export_total_raw,
        }

        registers: dict[int, int] = {addr: 0 for addr in range(0x00, 0x1D)}
        for spec in REGISTER_SPECS:
            raw_value = raw_values_by_key[spec.key]
            if spec.words == 1:
                registers[spec.address] = _encode_signed_16(raw_value)
                continue
            high, low = _encode_signed_32_words(raw_value)
            registers[spec.address] = high
            registers[spec.address + 1] = low
        return registers

    def read_input_registers(self, start_address: int, count: int) -> list[int]:
        if count <= 0:
            raise ValueError("count must be > 0")
        registers = self.snapshot_registers()
        return [registers.get(start_address + idx, 0) for idx in range(count)]

    def advance(self) -> None:
        """
        推进一个采样周期，模拟轻微波动与电能累计增长。
        """
        self._tick += 1
        voltage_delta = (-2, -1, 0, 1, 2)[self._tick % 5]
        current_delta = (-3, -1, 0, 1, 3)[self._tick % 5]

        self.ua_raw = min(2400, max(2100, self.ua_raw + voltage_delta))
        self.ub_raw = min(2400, max(2100, self.ub_raw - voltage_delta))
        self.uc_raw = min(2400, max(2100, self.uc_raw + (1 if self._tick % 2 else -1)))

        self.ia_raw = min(800, max(10, self.ia_raw + current_delta))
        self.ib_raw = min(800, max(10, self.ib_raw + (0 - current_delta)))
        self.ic_raw = min(800, max(10, self.ic_raw + (1 if self._tick % 2 else -1)))

        self.pa_raw = max(0, int(self.ua_raw * self.ia_raw * 0.0009))
        self.pb_raw = max(0, int(self.ub_raw * self.ib_raw * 0.0009))
        self.pc_raw = max(0, int(self.uc_raw * self.ic_raw * 0.0009))
        self.sa_raw = self.pa_raw + 20
        self.sb_raw = self.pb_raw + 20
        self.sc_raw = self.pc_raw + 20
        self.qa_raw = max(0, int(self.pa_raw * 0.18))
        self.qb_raw = max(0, int(self.pb_raw * 0.18))
        self.qc_raw = max(0, int(self.pc_raw * 0.18))

        self.fra_raw = 5000 + (self._tick % 3) - 1
        self.frb_raw = 5000 + ((self._tick + 1) % 3) - 1
        self.frc_raw = 5000 + ((self._tick + 2) % 3) - 1

        self.pf_total_raw = 920 + (self._tick % 8)
        self.pf_a_raw = 915 + (self._tick % 9)
        self.pf_b_raw = 910 + (self._tick % 10)
        self.pf_c_raw = 918 + (self._tick % 7)

        self.e_total_raw += 1
        self.e_import_total_raw += 1
        self.eq_total_raw += 1
        self.eq_import_total_raw += 1

