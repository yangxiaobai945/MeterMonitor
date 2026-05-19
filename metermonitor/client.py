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
        def trace_packet(*args: object) -> bytes:
            if len(args) != 2:
                return b""

            is_receive: bool
            packet: bytes
            if isinstance(args[0], bool) and isinstance(args[1], (bytes, bytearray)):
                is_receive = args[0]
                packet = bytes(args[1])
            elif isinstance(args[1], bool) and isinstance(args[0], (bytes, bytearray)):
                is_receive = args[1]
                packet = bytes(args[0])
            else:
                return b""

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
            raise RuntimeError(
                f"read_input_registers failed: device_id={device_id}, start=0x{start_address:04X}, "
                f"count={count}, error={response}"
            )
        return response.registers
