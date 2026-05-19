import time
import sys
import random
import struct

# ==========================================
# 寄存器配置表 (严格依据协议文档)
# ==========================================
# 电力参数基地址：0x00，均为 1 Word (Int) 
# 电能参数基地址：0x001D，为 2 Words (Long) 
REG_CONFIG = {
    "Ua": {"addr": 0x00, "type": "Int", "scale": 0.1, "unit": "V", "desc": "A相电压"}, # 
    "Ub": {"addr": 0x01, "type": "Int", "scale": 0.1, "unit": "V", "desc": "B相电压"}, # 
    "Uc": {"addr": 0x02, "type": "Int", "scale": 0.1, "unit": "V", "desc": "C相电压"}, # 
    "Ia": {"addr": 0x03, "type": "Int", "scale": 0.01, "unit": "A", "desc": "A相电流"}, # 
    "Ib": {"addr": 0x04, "type": "Int", "scale": 0.01, "unit": "A", "desc": "B相电流"}, # 
    "Ic": {"addr": 0x05, "type": "Int", "scale": 0.01, "unit": "A", "desc": "C相电流"}, # 
    "P_total": {"addr": 0x07, "type": "Int", "scale": 1.0, "unit": "W", "desc": "总有功功率"}, # 
    "Pa": {"addr": 0x08, "type": "Int", "scale": 1.0, "unit": "W", "desc": "A相有功功率"}, # 
    "Pb": {"addr": 0x09, "type": "Int", "scale": 1.0, "unit": "W", "desc": "B相有功功率"}, # 
    "Pc": {"addr": 0x0A, "type": "Int", "scale": 1.0, "unit": "W", "desc": "C相有功功率"}, # 
    "PF_total": {"addr": 0x13, "type": "Int", "scale": 0.001, "unit": "", "desc": "总功率因数"}, # 
    "E_total": {"addr": 0x001D, "type": "Long", "scale": 0.01, "unit": "kWh", "desc": "当前总有功电能"} # 
}

class ModbusParser:
    @staticmethod
    def crc16(data: bytes) -> bytes:
        """计算 Modbus CRC16 校验码 [cite: 29]"""
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

    @classmethod
    def parse_response(cls, raw_hex: str, start_reg: int, reg_types: list) -> dict:
        """
        解析通过功能码 03/04 返回的 Modbus-RTU 原始报文 [cite: 29, 67]
        格式: 地址(1B) + 功能码(1B) + 字节数(1B) + 数据(NB) + CRC(2B) [cite: 29, 35]
        """
        try:
            raw_bytes = bytes.fromhex(raw_hex.replace(" ", ""))
            if len(raw_bytes) < 5:
                return {"error": "报文长度过短"}

            # 验证 CRC 校验
            payload, received_crc = raw_bytes[:-2], raw_bytes[-2:]
            if cls.crc16(payload) != received_crc:
                return {"error": "CRC 校验失败"}

            byte_count = payload[2]
            data_bytes = payload[3:]
            if byte_count != len(data_bytes):
                return {"error": "数据字节数不匹配"}

            result = {}
            byte_idx = 0
            curr_reg = start_reg

            for r_type in reg_types:
                if r_type == "Int":
                    # 1个Word (2字节) 符号整型 
                    val = struct.unpack(">h", data_bytes[byte_idx:byte_idx+2])[0]
                    result[curr_reg] = val
                    byte_idx += 2
                    curr_reg += 1
                elif r_type == "Long":
                    # 2个Word (4字节) 长整型 
                    val = struct.unpack(">i", data_bytes[byte_idx:byte_idx+4])[0]
                    result[curr_reg] = val
                    byte_idx += 4
                    curr_reg += 2
            return result
        except Exception as e:
            return {"error": f"解析异常: {str(e)}"}

# ==========================================
# TUI 动态监视界面实现
# ==========================================
def generate_mock_bytes():
    """模拟电表通过 RS485 返回的真实数据 """
    # 模拟基础电力参数数据块 (0x00 - 0x13, 共20个寄存器=40字节) 
    ua, ub, uc = random.randint(2180, 2350), random.randint(2180, 2350), random.randint(2180, 2350) # 0.1V 
    ia, ib, ic = random.randint(150, 500), random.randint(150, 500), random.randint(150, 500)     # 0.01A 
    pa, pb, pc = int(ua*0.1 * ia*0.01 * 0.92), int(ub*0.1 * ib*0.01 * 0.91), int(uc*0.1 * ic*0.01 * 0.93) # W 
    p_total = pa + pb + pc # W 
    pf_total = random.randint(910, 950) # 0~1.000 
    
    # 构建 0x00 到 0x13 连续寄存器字节流 (补充 0x06 空寄存器) 
    block1_data = (
        struct.pack(">hhh", ua, ub, uc) +      # 0x00 - 0x02 
        struct.pack(">hhh", ia, ib, ic) +      # 0x03 - 0x05 
        struct.pack(">h", 0) +                 # 0x06 (空) 
        struct.pack(">hhhh", p_total, pa, pb, pc) + # 0x07 - 0x0A 
        struct.pack(">hhhhhhhh", 0,0,0,0,0,0,0,0) + # 0x0B - 0x12 占位
        struct.pack(">h", pf_total)            # 0x13 
    )
    block1_frame = b"\x01\x04" + bytes([len(block1_data)]) + block1_data
    block1_hex = (block1_frame + ModbusParser.crc16(block1_frame)).hex()

    # 模拟电能数据块 (0x001D, Long) 
    global _mock_energy
    _mock_energy += random.randint(1, 3) # 电能持续累加
    block2_data = struct.pack(">i", _mock_energy) # 
    block2_frame = b"\x01\x04\x04" + block2_data
    block2_hex = (block2_frame + ModbusParser.crc16(block2_frame)).hex()

    return block1_hex, block2_hex

_mock_energy = 4600  # 对应屏幕初始 46.00 kWh [cite: 4, 84]

def draw_ui(parsed_data):
    """渲染终端 UI，使用将光标移至顶部的控制码实现无换行原地刷新"""
    # \033[H 将光标移至左上角第一行第一列位置
    sys.stdout.write("\033[H")
    
    out = []
    out.append("=" * 55)
    out.append(f" 📑 三相多功能电能表数据实时监控工具 (MODBUS-RTU) ")
    out.append("=" * 55)
    
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
    out.append(" 提示: 正在实时解析串口报文数据... 按 Ctrl+C 退出程序 ")
    
    # 清理并打印每行，增加 \033[K 确保清除当前行残留字符
    sys.stdout.write("\n".join([line + "\033[K" for line in out]) + "\n")
    sys.stdout.flush()

def main():
    # 初始化终端，清屏并隐藏光标
    sys.stdout.write("\033[2J\033[?25l")
    sys.stdout.flush()
    
    try:
        while True:
            # 1. 模拟串口接收到的两段 Hex 报文数据
            hex_block1, hex_block2 = generate_mock_bytes()
            
            # 2. 调用协议解析器提取原始整型数据 [cite: 29, 67]
            # 基础参数数据块：自 0x00 开始，包含 19 个 Int, 1 个空 
            types_b1 = ["Int"]*6 + ["Int"] + ["Int"]*4 + ["Int"]*8 + ["Int"] 
            raw_vals_b1 = ModbusParser.parse_response(hex_block1, start_reg=0x00, reg_types=types_b1)
            
            # 电能数据块：自 0x001D 开始，包含 1 个 Long 
            raw_vals_b2 = ModbusParser.parse_response(hex_block2, start_reg=0x001D, reg_types=["Long"])
            
            # 3. 数据规整化与工程量单位换算 
            final_data = {}
            for key, cfg in REG_CONFIG.items():
                addr = cfg["addr"]
                if addr in raw_vals_b1:
                    final_data[key] = raw_vals_b1[addr] * cfg["scale"]
                elif addr in raw_vals_b2:
                    final_data[key] = raw_vals_b2[addr] * cfg["scale"]
            
            # 4. 刷新终端 UI 界面
            draw_ui(final_data)
            
            # 5. 设定刷新频率（1秒）
            time.sleep(1)
            
    except KeyboardInterrupt:
        # 退出时恢复光标显示
        sys.stdout.write("\033[?25h\n [INFO] 监视工具已安全退出。\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()