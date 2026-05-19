import time
import sys
import struct
import serial  # 导入真实串口通信库

# ==========================================
# 寄存器配置表 (严格依据协议文档)
# ==========================================
REG_CONFIG = {
    "Ua": {"addr": 0x00, "type": "Int", "scale": 0.1, "unit": "V", "desc": "A相电压"},       # 
    "Ub": {"addr": 0x01, "type": "Int", "scale": 0.1, "unit": "V", "desc": "B相电压"},       # 
    "Uc": {"addr": 0x02, "type": "Int", "scale": 0.1, "unit": "V", "desc": "C相电压"},       # 
    "Ia": {"addr": 0x03, "type": "Int", "scale": 0.01, "unit": "A", "desc": "A相电流"},      # 
    "Ib": {"addr": 0x04, "type": "Int", "scale": 0.01, "unit": "A", "desc": "B相电流"},      # 
    "Ic": {"addr": 0x05, "type": "Int", "scale": 0.01, "unit": "A", "desc": "C相电流"},      # 
    "P_total": {"addr": 0x07, "type": "Int", "scale": 1.0, "unit": "W", "desc": "总有功功率"}, # 
    "Pa": {"addr": 0x08, "type": "Int", "scale": 1.0, "unit": "W", "desc": "A相有功功率"},    # 
    "Pb": {"addr": 0x09, "type": "Int", "scale": 1.0, "unit": "W", "desc": "B相有功功率"},    # 
    "Pc": {"addr": 0x0A, "type": "Int", "scale": 1.0, "unit": "W", "desc": "C相有功功率"},    # 
    "PF_total": {"addr": 0x13, "type": "Int", "scale": 0.001, "unit": "", "desc": "总功率因数"},# 
    "E_total": {"addr": 0x001D, "type": "Long", "scale": 0.01, "unit": "kWh", "desc": "当前总有功电能"} # 
}

class ModbusRTUClient:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, slave_id=1):
        """
        初始化 Modbus 客户端
        根据文档 6.1：默认波特率 9600，数据位 8，停止位 1，偶校验 (EVEN)
        """
        self.slave_id = slave_id
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baudrate,       # [cite: 25]
                bytesize=serial.EIGHTBITS, # [cite: 25]
                parity=serial.PARITY_EVEN, # [cite: 25]
                stopbits=serial.STOPBITS_ONE, # [cite: 25]
                timeout=0.5              # 串口读取超时时间 (秒)
            )
        except Exception as e:
            print(f"❌ 无法打开串口 {port}: {e}")
            sys.exit(1)

    @staticmethod
    def crc16(data: bytes) -> bytes:
        """计算 Modbus CRC16 校验码"""
        crc = 0xFFFF
        for pos in data:
            crc ^= pos
            for _ in range(8):
                if (crc & 1) != 0:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        return struct.pack("<H", crc)

    def send_and_receive(self, function_code: int, start_reg: int, reg_count: int) -> bytes:
        """
        【新增核心逻辑】核心方法：组装报文 -> 发送请求 -> 等待并读取响应 -> 验证
        """
        # 1. 组装请求报文: 地址(1B) + 功能码(1B) + 寄存器起始地址(2B) + 寄存器数量(2B)
        request_payload = struct.pack(">BBHH", self.slave_id, function_code, start_reg, reg_count)
        # ">BBHH" 代表大端字节序：1字节地址 + 1字节功能码 + 2字节起始地址 + 2字节寄存器数量
        # > 代表大端字节序，B 代表无符号 char (1字节)，H 代表无符号 short (2字节) [cite: 29]
        request_frame = request_payload + self.crc16(request_payload) # 

        # 2. 清空串口缓存，防止残留数据干扰
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        # 3. 发送物理报文
        self.ser.write(request_frame)
        self.ser.flush()

        # 4. 先读地址和功能码，区分正常响应与异常响应
        head2 = self.ser.read(2)
        if len(head2) < 2:
            return b""  # 超时未响应

        resp_slave, resp_fc = head2[0], head2[1]
        if resp_slave != self.slave_id:
            return b""  # 非本机地址的帧

        # 异常响应: 功能码最高位为 1，帧格式为 addr + (fc|0x80) + ex_code + crc
        if resp_fc == (function_code | 0x80):
            tail = self.ser.read(3)
            if len(tail) < 3:
                return b""
            full_response = head2 + tail
            payload, received_crc = full_response[:-2], full_response[-2:]
            if self.crc16(payload) != received_crc:
                return b""
            return full_response

        # 正常响应功能码必须与请求一致
        if resp_fc != function_code:
            return b""

        # 5. 正常响应第三字节为数据字节数
        len_byte = self.ser.read(1)
        if len(len_byte) < 1:
            return b""
        data_len = len_byte[0]

        # 对 04 读寄存器，数据长度应为寄存器数 * 2 字节
        expected_len = reg_count * 2
        if data_len != expected_len:
            return b""

        remaining_bytes = self.ser.read(data_len + 2)
        if len(remaining_bytes) < (data_len + 2):
            return b""  # 数据不完整

        full_response = head2 + len_byte + remaining_bytes

        # 6. CRC 验证
        payload, received_crc = full_response[:-2], full_response[-2:]
        if self.crc16(payload) != received_crc:
            return b""  # 校验错误

        return full_response

    def read_registers(self, start_reg: int, reg_count: int, reg_types: list) -> dict:
        """
        封装高层读取逻辑：发送功能码 04 读寄存器并调用转换
        """
        # 功能码统一使用 04 (读输入寄存器)
        response = self.send_and_receive(function_code=0x04, start_reg=start_reg, reg_count=reg_count) # [cite: 67]
        if not response:
            return {"error": "通讯超时或校验失败"}

        # 处理 Modbus 异常帧: [addr][fc|0x80][ex_code][crc_lo][crc_hi]
        if len(response) == 5 and response[1] == 0x84:
            ex_code = response[2]
            ex_map = {
                0x01: "非法功能码",
                0x02: "非法数据地址",
                0x03: "非法数据值",
                0x04: "从站设备故障",
            }
            return {"error": f"设备异常响应: 0x{ex_code:02X} ({ex_map.get(ex_code, '未知异常')})"}

        if len(response) < 5 or response[1] != 0x04:
            return {"error": "响应功能码异常"}

        # 检查类型定义与请求寄存器数量是否一致，避免解析偏移错位
        words_from_types = 0
        for r_type in reg_types:
            if r_type == "Int":
                words_from_types += 1
            elif r_type == "Long":
                words_from_types += 2
            else:
                return {"error": f"未知寄存器类型: {r_type}"}
        if words_from_types != reg_count:
            return {"error": f"类型表长度不匹配: types={words_from_types} words, 请求={reg_count} words"}

        # 跳过地址(1B)、功能码(1B)、数据长度(1B)，直奔数据体 
        data_len = response[2]
        if data_len != reg_count * 2:
            return {"error": f"返回字节数异常: data_len={data_len}, 期望={reg_count * 2}"}

        data_bytes = response[3:-2] 
        if len(data_bytes) != data_len:
            return {"error": "数据体长度异常"}

        result = {}
        byte_idx = 0
        curr_reg = start_reg

        for r_type in reg_types:
            if r_type == "Int":
                if (byte_idx + 2) > len(data_bytes):
                    return {"error": "数据长度不足(Int)"}
                val = struct.unpack(">h", data_bytes[byte_idx:byte_idx+2])[0]
                result[curr_reg] = val
                byte_idx += 2
                curr_reg += 1
            elif r_type == "Long":
                if (byte_idx + 4) > len(data_bytes):
                    return {"error": "数据长度不足(Long)"}
                val = struct.unpack(">i", data_bytes[byte_idx:byte_idx+4])[0]
                result[curr_reg] = val
                byte_idx += 4
                curr_reg += 2
        return result

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

# ==========================================
# TUI 终端渲染界面
# ==========================================
def draw_ui(parsed_data):
    """使用 ANSI 控制码实现就地刷新终端界面"""
    sys.stdout.write("\033[H") # 光标归位到左上角
    
    out = []
    out.append("=" * 55)
    out.append(f" 📑 三相多功能电能表数据实时监控工具 (MODBUS-RTU) ")
    out.append("=" * 55)
    
    # 状态栏判断
    if "error" in parsed_data:
        out.append(f" 状态: \033[1;31m通讯异常 ({parsed_data['error']})\033[0m")
        out.append("-" * 55)
    else:
        out.append(f" 状态: \033[1;32m正常通讯中\033[0m")
        out.append("-" * 55)
    
    # 1. 电压与电流数据
    out.append(f" 【电压参数】                        【电流参数】")
    out.append(f"  A相电压 (Ua): {parsed_data.get('Ua', 0.0):6.1f} {REG_CONFIG['Ua']['unit']}      "
               f"A相电流 (Ia): {parsed_data.get('Ia', 0.0):6.2f} {REG_CONFIG['Ia']['unit']}")
    out.append(f"  B相电压 (Ub): {parsed_data.get('Ub', 0.0):6.1f} {REG_CONFIG['Ub']['unit']}      "
               f"B相电流 (Ib): {parsed_data.get('Ib', 0.0):6.2f} {REG_CONFIG['Ib']['unit']}")
    out.append(f"  C相电压 (Uc): {parsed_data.get('Uc', 0.0):6.1f} {REG_CONFIG['Uc']['unit']}      "
               f"C相电流 (Ic): {parsed_data.get('Ic', 0.0):6.2f} {REG_CONFIG['Ic']['unit']}")
    out.append("-" * 55)
    
    # 2. 功率与因数数据
    out.append(f" 【功率参数】")
    out.append(f"  A相有功功率 (Pa): {parsed_data.get('Pa', 0.0):6.1f} {REG_CONFIG['Pa']['unit']}    "
               f"B相有功功率 (Pb): {parsed_data.get('Pb', 0.0):6.1f} {REG_CONFIG['Pb']['unit']}")
    out.append(f"  C相有功功率 (Pc): {parsed_data.get('Pc', 0.0):6.1f} {REG_CONFIG['Pc']['unit']}    "
               f"总有功功率  (ΣP): {parsed_data.get('P_total', 0.0):6.1f} {REG_CONFIG['P_total']['unit']}")
    out.append(f"  总功率因数 (cosφ): {parsed_data.get('PF_total', 0.0):6.3f}")
    out.append("-" * 55)
    
    # 3. 电能计量数据
    out.append(f" 【电能计量】")
    out.append(f"  当前总有功电能: \033[1;32m{parsed_data.get('E_total', 0.0):10.2f}\033[0m {REG_CONFIG['E_total']['unit']}")
    out.append("=" * 55)
    out.append(" 提示: 正在通过串行接口采集数据... 按 Ctrl+C 退出程序 ")
    
    sys.stdout.write("\n".join([line + "\033[K" for line in out]) + "\n")
    sys.stdout.flush()

def main():
    # 配置您的硬件串口参数（Windows一般为 'COM3', Linux一般为 '/dev/ttyUSB0' 或 '/dev/ttyAMA0'）
    SERIAL_PORT = "COM3" if sys.platform == "win32" else "/dev/ttyUSB0"
    
    # 初始化真实 Modbus 客户端
    client = ModbusRTUClient(port=SERIAL_PORT, baudrate=9600, slave_id=1) # [cite: 25]

    # 初始化 TUI 屏幕
    sys.stdout.write("\033[2J\033[?25l")
    sys.stdout.flush()
    
    try:
        while True:
            merged_data = {}
            
            # --- 第一次发送与接收：读取电力参数数据块 (0x00 至 0x13，共 20 个寄存器) ---
            # 寄存器列表类型映射：0x00~0x05 是 Int，0x06 是空(Int占位)，0x07~0x0A 是有功功率，中间由空占位，0x13 是总因数 
            types_b1 = ["Int"]*6 + ["Int"] + ["Int"]*4 + ["Int"]*8 + ["Int"] 
            res_b1 = client.read_registers(start_reg=0x00, reg_count=20, reg_types=types_b1)
            
            # --- 第二次发送与接收：读取电能数据块 (0x001D，共 2 个寄存器) ---
            res_b2 = client.read_registers(start_reg=0x001D, reg_count=2, reg_types=["Long"]) # 
            
            # 异常处理检查
            if "error" in res_b1:
                merged_data["error"] = res_b1["error"]
            elif "error" in res_b2:
                merged_data["error"] = res_b2["error"]
            else:
                # 均读取成功后，合并原始整型数据并执行比例换算
                for key, cfg in REG_CONFIG.items():
                    addr = cfg["addr"]
                    if addr in res_b1:
                        merged_data[key] = res_b1[addr] * cfg["scale"]
                    elif addr in res_b2:
                        merged_data[key] = res_b2[addr] * cfg["scale"]

            # 刷新页面展示
            draw_ui(merged_data)
            time.sleep(1.0) # 每隔1秒周期性轮询发送一次
            
    except KeyboardInterrupt:
        sys.stdout.write("\033[?25h\n [INFO] 串口采集程序已安全退出。\n")
        sys.stdout.flush()
    finally:
        client.close()

if __name__ == "__main__":
    main()