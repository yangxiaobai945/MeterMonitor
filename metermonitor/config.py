from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    port: str
    baudrate: int
    device_id: int
    timeout: float
    retries: int
    reconnect_delay: float
    reconnect_delay_max: float
    poll_interval: float
    log_dir: Path


def default_port() -> str:
    return "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"


def parse_args() -> RuntimeConfig:
    parser = argparse.ArgumentParser(description="Modbus RTU meter monitor")
    parser.add_argument("--port", default=default_port(), help="Serial port")
    parser.add_argument("--baudrate", type=int, default=9600, help="Baudrate")
    parser.add_argument("--device-id", type=int, default=1, help="Modbus slave id")
    parser.add_argument("--timeout", type=float, default=0.5, help="Request timeout (s)")
    parser.add_argument("--retries", type=int, default=2, help="Retries per request")
    parser.add_argument("--reconnect-delay", type=float, default=0.5, help="Reconnect delay (s)")
    parser.add_argument("--reconnect-delay-max", type=float, default=5.0, help="Max reconnect delay (s)")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Polling interval (s)")
    parser.add_argument("--log-dir", default="logs", help="Log directory")
    args = parser.parse_args()

    return RuntimeConfig(
        port=args.port,
        baudrate=args.baudrate,
        device_id=args.device_id,
        timeout=args.timeout,
        retries=args.retries,
        reconnect_delay=args.reconnect_delay,
        reconnect_delay_max=args.reconnect_delay_max,
        poll_interval=args.poll_interval,
        log_dir=Path(args.log_dir),
    )

