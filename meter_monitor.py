from __future__ import annotations

import json
import time

from rich.console import Console
from rich.live import Live

from metermonitor.client import MeterModbusClient
from metermonitor.config import parse_args
from metermonitor.logging_utils import setup_logging
from metermonitor.poller import MeterPoller, PollSnapshot
from metermonitor.tui import build_renderable


def main() -> None:
    config = parse_args()
    packet_logger, result_logger = setup_logging(config.log_dir)

    client = MeterModbusClient(config, packet_logger)
    poller = MeterPoller(client, config)
    console = Console()
    snapshot = PollSnapshot(ok=False, message="初始化中...", parsed=None)

    try:
        with Live(build_renderable(snapshot), console=console, refresh_per_second=4) as live:
            while True:
                snapshot = poller.poll_once()
                live.update(build_renderable(snapshot))

                if snapshot.parsed:
                    result_logger.info(
                        json.dumps(
                            {
                                "ok": snapshot.ok,
                                "message": snapshot.message,
                                "values": snapshot.parsed.values,
                            },
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                    )
                else:
                    result_logger.info(
                        json.dumps({"ok": snapshot.ok, "message": snapshot.message}, ensure_ascii=False)
                    )

                time.sleep(config.poll_interval)
    except KeyboardInterrupt:
        console.print("\n[cyan]已退出采集程序[/cyan]")
    finally:
        client.close()


if __name__ == "__main__":
    main()
