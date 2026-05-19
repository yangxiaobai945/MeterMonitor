from __future__ import annotations

import argparse

from .simulator import run_pymodbus_simulator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run pymodbus TCP simulator for MeterMonitor")
    parser.add_argument("--host", default="127.0.0.1", help="Simulator bind host")
    parser.add_argument("--port", type=int, default=5020, help="Simulator bind port")
    parser.add_argument("--device-id", type=int, default=1, help="Simulator device id")
    args = parser.parse_args()
    run_pymodbus_simulator(host=args.host, port=args.port, device_id=args.device_id)


if __name__ == "__main__":
    main()

