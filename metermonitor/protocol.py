from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterSpec:
    key: str
    address: int
    words: int
    scale: float
    unit: str
    description: str


@dataclass(frozen=True)
class ReadBlock:
    start: int
    count: int


REGISTER_SPECS: tuple[RegisterSpec, ...] = (
    RegisterSpec("Ua", 0x00, 1, 0.1, "V", "A相电压"),
    RegisterSpec("Ub", 0x01, 1, 0.1, "V", "B相电压"),
    RegisterSpec("Uc", 0x02, 1, 0.1, "V", "C相电压"),
    RegisterSpec("Ia", 0x03, 1, 0.01, "A", "A相电流"),
    RegisterSpec("Ib", 0x04, 1, 0.01, "A", "B相电流"),
    RegisterSpec("Ic", 0x05, 1, 0.01, "A", "C相电流"),
    RegisterSpec("P_total", 0x07, 1, 1.0, "W", "总有功功率"),
    RegisterSpec("Pa", 0x08, 1, 1.0, "W", "A相有功功率"),
    RegisterSpec("Pb", 0x09, 1, 1.0, "W", "B相有功功率"),
    RegisterSpec("Pc", 0x0A, 1, 1.0, "W", "C相有功功率"),
    RegisterSpec("Q_total", 0x0B, 1, 1.0, "Var", "总无功功率"),
    RegisterSpec("Qa", 0x0C, 1, 1.0, "Var", "A相无功功率"),
    RegisterSpec("Qb", 0x0D, 1, 1.0, "Var", "B相无功功率"),
    RegisterSpec("Qc", 0x0E, 1, 1.0, "Var", "C相无功功率"),
    RegisterSpec("S_total", 0x0F, 1, 1.0, "VA", "总视在功率"),
    RegisterSpec("Sa", 0x10, 1, 1.0, "VA", "A相视在功率"),
    RegisterSpec("Sb", 0x11, 1, 1.0, "VA", "B相视在功率"),
    RegisterSpec("Sc", 0x12, 1, 1.0, "VA", "C相视在功率"),
    RegisterSpec("PF_total", 0x13, 1, 0.001, "", "总功率因数"),
    RegisterSpec("PF_a", 0x14, 1, 0.001, "", "A相功率因数"),
    RegisterSpec("PF_b", 0x15, 1, 0.001, "", "B相功率因数"),
    RegisterSpec("PF_c", 0x16, 1, 0.001, "", "C相功率因数"),
    RegisterSpec("FRa", 0x1A, 1, 0.01, "Hz", "A相电压频率"),
    RegisterSpec("FRb", 0x1B, 1, 0.01, "Hz", "B相电压频率"),
    RegisterSpec("FRc", 0x1C, 1, 0.01, "Hz", "C相电压频率"),
    RegisterSpec("E_total", 0x1D, 2, 0.01, "kWh", "当前总有功电能"),
    RegisterSpec("E_import_total", 0x0027, 2, 0.01, "kWh", "当前正向总有功电能"),
    RegisterSpec("E_export_total", 0x0031, 2, 0.01, "kWh", "当前反向总有功电能"),
    RegisterSpec("EQ_total", 0x003B, 2, 0.01, "kVarh", "当前总无功电能"),
    RegisterSpec("EQ_import_total", 0x0045, 2, 0.01, "kVarh", "当前正向总无功电能"),
    RegisterSpec("EQ_export_total", 0x004F, 2, 0.01, "kVarh", "当前反向总无功电能"),
)

READ_BLOCKS: tuple[ReadBlock, ...] = (
    ReadBlock(0x00, 29),  # 地址 0x00~0x1C（十进制 0~28），共 29 个寄存器
    ReadBlock(0x1D, 2),
    ReadBlock(0x0027, 2),
    ReadBlock(0x0031, 2),
    ReadBlock(0x003B, 2),
    ReadBlock(0x0045, 2),
    ReadBlock(0x004F, 2),
)
