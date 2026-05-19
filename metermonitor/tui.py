from __future__ import annotations

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .poller import PollSnapshot


def build_renderable(snapshot: PollSnapshot) -> Panel:
    status = Text(snapshot.message, style="green" if snapshot.ok else "bold red")

    electrical_table = Table(title="电压/电流", expand=True)
    electrical_table.add_column("项目")
    electrical_table.add_column("值", justify="right")
    electrical_table.add_column("单位", justify="left")

    power_table = Table(title="功率/功率因数", expand=True)
    power_table.add_column("项目")
    power_table.add_column("值", justify="right")
    power_table.add_column("单位", justify="left")

    energy_table = Table(title="电能", expand=True)
    energy_table.add_column("项目")
    energy_table.add_column("值", justify="right")
    energy_table.add_column("单位", justify="left")

    values = snapshot.parsed.values if snapshot.parsed else {}
    _add_table_row(electrical_table, "Ua", values.get("Ua"), "V")
    _add_table_row(electrical_table, "Ub", values.get("Ub"), "V")
    _add_table_row(electrical_table, "Uc", values.get("Uc"), "V")
    _add_table_row(electrical_table, "Ia", values.get("Ia"), "A")
    _add_table_row(electrical_table, "Ib", values.get("Ib"), "A")
    _add_table_row(electrical_table, "Ic", values.get("Ic"), "A")
    _add_table_row(electrical_table, "FRa", values.get("FRa"), "Hz")
    _add_table_row(electrical_table, "FRb", values.get("FRb"), "Hz")
    _add_table_row(electrical_table, "FRc", values.get("FRc"), "Hz")

    _add_table_row(power_table, "P_total", values.get("P_total"), "W")
    _add_table_row(power_table, "Pa", values.get("Pa"), "W")
    _add_table_row(power_table, "Pb", values.get("Pb"), "W")
    _add_table_row(power_table, "Pc", values.get("Pc"), "W")
    _add_table_row(power_table, "Q_total", values.get("Q_total"), "Var")
    _add_table_row(power_table, "S_total", values.get("S_total"), "VA")
    _add_table_row(power_table, "PF_total", values.get("PF_total"), "")

    _add_table_row(energy_table, "E_total", values.get("E_total"), "kWh")
    _add_table_row(energy_table, "E_import_total", values.get("E_import_total"), "kWh")
    _add_table_row(energy_table, "E_export_total", values.get("E_export_total"), "kWh")
    _add_table_row(energy_table, "EQ_total", values.get("EQ_total"), "kVarh")

    content = Group(status, electrical_table, power_table, energy_table)
    return Panel(content, title="三相多功能电能表实时监控", border_style="cyan")


def _add_table_row(table: Table, key: str, value: float | None, unit: str) -> None:
    if value is None:
        table.add_row(key, "-", unit)
    else:
        table.add_row(key, f"{value:.3f}", unit)
