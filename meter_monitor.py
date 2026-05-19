from __future__ import annotations

import json
import os
import sys
import time

from rich.console import Console
from rich.live import Live

from metermonitor.client import MeterModbusClient
from metermonitor.config import parse_args
from metermonitor.logging_utils import setup_logging
from metermonitor.poller import MeterPoller, PollSnapshot
from metermonitor.tui import build_renderable


def _blocked_runtime_reason() -> str | None:
    checks = (
        ("GITHUB_ACTIONS", "GitHub Actions"),
        ("CODESPACES", "GitHub Codespaces"),
        ("CI", "CI"),
    )
    for env_key, label in checks:
        value = os.getenv(env_key, "").strip().lower()
        if value and value not in {"0", "false", "no"}:
            return f"{label} ({env_key}={os.getenv(env_key)})"
    return None


def _ensure_hardware_runtime_allowed() -> None:
    reason = _blocked_runtime_reason()
    if reason is None:
        return
    Console(stderr=True).print(
        "[red]检测到受限环境：[/red]"
        f"{reason}\n"
        "[yellow]当前环境无法连接物理串口，程序将退出。[/yellow]\n"
        "请改为运行测试、pymodbus simulator/mock 或静态校验。"
    )
    raise SystemExit(2)


def main() -> None:
    _ensure_hardware_runtime_allowed()
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
