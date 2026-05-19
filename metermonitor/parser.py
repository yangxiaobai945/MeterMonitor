from __future__ import annotations

from dataclasses import dataclass

from .protocol import REGISTER_SPECS, RegisterSpec


@dataclass(frozen=True)
class ParsedData:
    values: dict[str, float]
    raw_registers: dict[int, int]


def _to_signed_16(word: int) -> int:
    return word - 0x10000 if word & 0x8000 else word


def _to_signed_32(high: int, low: int) -> int:
    merged = (high << 16) | low
    return merged - 0x100000000 if merged & 0x80000000 else merged


def parse_registers(raw_registers: dict[int, int]) -> ParsedData:
    values: dict[str, float] = {}
    for spec in REGISTER_SPECS:
        raw_value = _extract_raw_value(spec, raw_registers)
        if raw_value is None:
            continue
        values[spec.key] = raw_value * spec.scale
    return ParsedData(values=values, raw_registers=raw_registers)


def _extract_raw_value(spec: RegisterSpec, raw_registers: dict[int, int]) -> int | None:
    if spec.words == 1:
        word = raw_registers.get(spec.address)
        if word is None:
            return None
        return _to_signed_16(word)

    high = raw_registers.get(spec.address)
    low = raw_registers.get(spec.address + 1)
    if high is None or low is None:
        return None
    return _to_signed_32(high, low)

