# Copilot Agent Instructions

## 运行约束（强制）

- 在 **Copilot code agent** 与 **CI/GitHub Actions** 环境中，禁止运行 `meter_monitor.py`（或误写为 `meter_motion.py`）：
  - 不允许执行：`python meter_monitor.py`、`python -m meter_monitor` 等会访问物理串口的命令。
- 这些环境无法连接物理串口，验证方式仅限：
  - 自动化测试用例
  - `pymodbus` simulator / mock 场景
  - 语法检查、静态检查、构建检查

## 推荐验证命令

- `python -m py_compile meter_monitor.py metermonitor/*.py`
- `python -m pytest -q`（若仓库存在测试）
- 基于 `pymodbus` simulator 的集成验证（如有）

