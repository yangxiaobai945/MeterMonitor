from __future__ import annotations

from dataclasses import dataclass

from .client import MeterModbusClient
from .config import RuntimeConfig
from .parser import ParsedData, parse_registers
from .protocol import READ_BLOCKS


@dataclass(frozen=True)
class PollSnapshot:
    ok: bool
    message: str
    parsed: ParsedData | None


class MeterPoller:
    def __init__(self, client: MeterModbusClient, config: RuntimeConfig):
        self._client = client
        self._config = config

    def poll_once(self) -> PollSnapshot:
        if not self._client.connect():
            return PollSnapshot(ok=False, message="串口连接失败", parsed=None)

        try:
            raw_registers: dict[int, int] = {}
            for block in READ_BLOCKS:
                words = self._client.read_input_registers(
                    start_address=block.start,
                    count=block.count,
                    device_id=self._config.device_id,
                )
                for idx, word in enumerate(words):
                    raw_registers[block.start + idx] = word
            parsed = parse_registers(raw_registers)
            return PollSnapshot(ok=True, message="通讯正常", parsed=parsed)
        except Exception as exc:
            return PollSnapshot(ok=False, message=f"采集失败: {exc}", parsed=None)

