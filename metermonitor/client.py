from __future__ import annotations

import logging
from typing import Callable

from pymodbus.client import ModbusSerialClient

from .config import RuntimeConfig


class MeterModbusClient:
    def __init__(self, config: RuntimeConfig, packet_logger: logging.Logger):
        self._config = config
        self._packet_logger = packet_logger
        self._client = self._build_client()

    def _build_client(self) -> ModbusSerialClient:
        def trace_packet(is_receive: bool, packet: bytes) -> bytes:
            direction = "RX" if is_receive else "TX"
            self._packet_logger.info("%s %s", direction, packet.hex(" ").upper())
            return packet

        return ModbusSerialClient(
            port=self._config.port,
            framer="rtu",
            baudrate=self._config.baudrate,
            bytesize=8,
            parity="E",
            stopbits=1,
            timeout=self._config.timeout,
            retries=self._config.retries,
            reconnect_delay=self._config.reconnect_delay,
            reconnect_delay_max=self._config.reconnect_delay_max,
            trace_packet=trace_packet,
        )

    def connect(self) -> bool:
        return self._client.connect()

    def close(self) -> None:
        self._client.close()

    def read_input_registers(self, start_address: int, count: int, device_id: int) -> list[int]:
        response = self._client.read_input_registers(
            start_address,
            count=count,
            device_id=device_id,
        )
        if response.isError():
            raise RuntimeError(str(response))
        return response.registers

