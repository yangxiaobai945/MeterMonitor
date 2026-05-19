# MeterMonitor `pymodbus` Simulator 使用说明

## 目的

`metermonitor/simulator.py` 基于 `pymodbus.simulator`（`SimData/SimDevice`）构造协议寄存器模型，配套 `metermonitor/simulator_main.py` 可直接启动 TCP Simulator，用于在无物理串口环境（CI/GitHub Actions/Codespaces）中调试 TUI。

## 覆盖范围

- 电压/电流/功率/功率因数/频率：`0x00 ~ 0x1C`
- 电能累计量（Long, 2 words）：
  - `0x001D` 当前总有功电能
  - `0x0027` 当前正向总有功电能
  - `0x0031` 当前反向总有功电能
  - `0x003B` 当前总无功电能
  - `0x0045` 当前正向总无功电能
  - `0x004F` 当前反向总无功电能

## 启动 Simulator

```bash
cd /home/runner/work/MeterMonitor/MeterMonitor
python -m metermonitor.simulator_main --host 127.0.0.1 --port 5020 --device-id 1
```

## 连接 TUI 到 Simulator

```bash
cd /home/runner/work/MeterMonitor/MeterMonitor
python meter_monitor.py --transport tcp --host 127.0.0.1 --tcp-port 5020 --device-id 1
```

## Python 侧构建设备（高级用法）

```python
from metermonitor.simulator import build_pymodbus_sim_device

device = build_pymodbus_sim_device(device_id=1)
```

## 推荐验证命令

```bash
cd /home/runner/work/MeterMonitor/MeterMonitor
python -m py_compile meter_monitor.py metermonitor/*.py
python -m pytest -q
```

> 注意：CI/Codespaces 中不要用串口模式运行 `meter_monitor.py`；如需联调请使用 `--transport tcp` + `pymodbus simulator`。
