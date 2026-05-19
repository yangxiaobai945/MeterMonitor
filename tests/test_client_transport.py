from __future__ import annotations

import logging
from pathlib import Path

from pymodbus.client import ModbusSerialClient, ModbusTcpClient

from metermonitor.client import MeterModbusClient
from metermonitor.config import RuntimeConfig


def _base_config(transport: str) -> RuntimeConfig:
    return RuntimeConfig(
        transport=transport,
        port="/dev/ttyUSB0",
        host="127.0.0.1",
        tcp_port=5020,
        baudrate=9600,
        device_id=1,
        timeout=0.5,
        retries=2,
        reconnect_delay=0.5,
        reconnect_delay_max=5.0,
        poll_interval=5.0,
        log_dir=Path("logs"),
    )


def test_build_client_tcp_transport() -> None:
    client = MeterModbusClient(_base_config("tcp"), logging.getLogger("test.packet.tcp"))
    assert isinstance(client._client, ModbusTcpClient)


def test_build_client_serial_transport() -> None:
    client = MeterModbusClient(_base_config("serial"), logging.getLogger("test.packet.serial"))
    assert isinstance(client._client, ModbusSerialClient)

