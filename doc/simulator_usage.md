# MeterMonitor Simulator 使用说明

## 目的

`metermonitor/simulator.py` 提供了一个基于 `doc/电表协议.tsv` 的输入寄存器模拟器，用于在无物理串口环境（CI/GitHub Actions/Codespaces）中进行协议级验证与测试。

## 覆盖范围

- 电压/电流/功率/功率因数/频率：`0x00 ~ 0x1C`
- 电能累计量（Long, 2 words）：
  - `0x001D` 当前总有功电能
  - `0x0027` 当前正向总有功电能
  - `0x0031` 当前反向总有功电能
  - `0x003B` 当前总无功电能
  - `0x0045` 当前正向总无功电能
  - `0x004F` 当前反向总无功电能

## 基本用法

```python
from metermonitor.simulator import MeterProtocolSimulator

sim = MeterProtocolSimulator()
registers = sim.snapshot_registers()
window = sim.read_input_registers(start_address=0x00, count=29)
sim.advance()  # 推进一个采样周期，模拟值波动和电能累计
```

## 推荐验证命令

```bash
python -m py_compile meter_monitor.py metermonitor/*.py
python -m pytest -q
```

> 注意：在 CI/Codespaces 中不要运行 `meter_monitor.py`（该程序需要物理串口）。

