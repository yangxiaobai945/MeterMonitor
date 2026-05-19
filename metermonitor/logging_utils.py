from __future__ import annotations

import logging
from pathlib import Path


def setup_logging(log_dir: Path) -> tuple[logging.Logger, logging.Logger]:
    log_dir.mkdir(parents=True, exist_ok=True)

    packet_logger = logging.getLogger("metermonitor.packet")
    packet_logger.setLevel(logging.INFO)
    packet_logger.handlers.clear()
    packet_handler = logging.FileHandler(log_dir / "packet.log", encoding="utf-8")
    packet_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    packet_logger.addHandler(packet_handler)
    packet_logger.propagate = False

    result_logger = logging.getLogger("metermonitor.result")
    result_logger.setLevel(logging.INFO)
    result_logger.handlers.clear()
    result_handler = logging.FileHandler(log_dir / "result.log", encoding="utf-8")
    result_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    result_logger.addHandler(result_handler)
    result_logger.propagate = False

    return packet_logger, result_logger

