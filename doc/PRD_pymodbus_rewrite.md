# MeterMonitor Pymodbus 重构 PRD

## 1. 背景与目标
- 基于最新版本 `pymodbus` 重构串口采集逻辑，替换手工拼包/解包。
- 数据解析严格与 `doc/电表协议.tsv` 保持一致（忽略 `TEST.py`）。
- 将实现拆分为可扩展模块，提升可维护性。

## 2. 功能范围
- 每 5 秒轮询一次设备数据。
- 使用 Modbus RTU（功能码 0x04）读取输入寄存器。
- 支持协议文件中的关键量测：
  - 0x00~0x1C 范围内的电压/电流/功率/功率因数/频率。
  - 0x001D、0x0027、0x0031、0x003B、0x0045、0x004F 的电能累计量（Long）。
- 提供可读性更好的终端 TUI 展示。
- 将原始报文和解析结果写入日志文件。

## 3. 非功能要求
- 优先使用 `pymodbus` 内置超时、重试、重连机制。
- 支持命令行参数配置串口、从站地址、轮询周期、日志目录。
- 代码结构清晰，后续扩展寄存器和展示项无需修改核心通信层。

## 4. 模块划分
- `metermonitor/config.py`：运行配置与参数解析。
- `metermonitor/protocol.py`：协议寄存器定义与分块读配置。
- `metermonitor/client.py`：`pymodbus` 串口客户端封装、报文跟踪日志。
- `metermonitor/parser.py`：寄存器值解析与工程量换算。
- `metermonitor/poller.py`：轮询编排与错误隔离。
- `metermonitor/tui.py`：基于 Rich 的 TUI 渲染。
- `metermonitor/logging_utils.py`：日志初始化。
- `meter_monitor.py`：主入口（启动、循环、退出收尾）。

## 5. 验收标准
- 程序可直接启动并按 5 秒周期刷新。
- 通信异常可记录并在 TUI 可见。
- `logs/packet.log` 有原始请求/响应报文（HEX）。
- `logs/result.log` 有解析后的结构化结果（JSON 行）。
- 主要输出值缩放比例与协议一致。
