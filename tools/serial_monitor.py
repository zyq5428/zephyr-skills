#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# serial_monitor.py — grabserial 平替串口监视工具（字节透明，UTF-8 中文无损）
#
# 为什么需要它:
#   grabserial 逐字节 sd.read(1) + x.decode("utf8", "ignore")，会静默丢弃所有
#   非 ASCII 字节（中文日志"消失"）。本工具原始字节透传，任何编码都不丢字节。
#
# 用法示例:
#   python3 serial_monitor.py -d /dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947* -b 115200 -e 5
#   python3 serial_monitor.py -d /dev/ttyACM0 -b 115200            # 手动 Ctrl-C 退出
#   python3 serial_monitor.py -d /dev/ttyUSB0 -b 115200 -o raw.log # 同时存原始日志
#
# 依赖: pyserial（Zephyr venv 内已安装）
#   /home/hero/zephyrproject/.venv/bin/python3 serial_monitor.py ...

import argparse
import glob
import sys
import time

try:
    import serial
except ImportError:
    print("错误: 缺少 pyserial，请安装: pip install pyserial", file=sys.stderr)
    sys.exit(1)


def resolve_device(device):
    """[解析] 展开设备路径通配符，返回实际设备（by-id 路径无需记完整序列号）"""
    if glob.has_magic(device):  # [检查] 路径含 * ? [ 通配符
        matches = glob.glob(device)
        if not matches:
            print(f"错误: 未找到匹配设备: {device}", file=sys.stderr)
            sys.exit(1)
        return matches[0]  # [返回] 取第一个匹配
    return device


def main():
    parser = argparse.ArgumentParser(
        description="grabserial 平替：字节透明的串口监视工具（UTF-8 无损）")
    parser.add_argument("-d", "--device", required=True,
                        help="串口设备（支持通配符，如 /dev/serial/by-id/usb-NXP_*）")
    parser.add_argument("-b", "--baud", type=int, default=115200,
                        help="波特率（默认 115200）")
    parser.add_argument("-e", "--exit-after", type=float, default=None,
                        help="抓取 N 秒后自动退出（对齐 grabserial -e 语义）")
    parser.add_argument("-o", "--output",
                        help="同时把原始字节写入文件（排障用）")
    args = parser.parse_args()

    device = resolve_device(args.device)
    try:
        # [初始化] 打开串口，0.1s 读取超时（非阻塞轮询）
        ser = serial.Serial(device, args.baud, timeout=0.1)
    except serial.SerialException as e:
        print(f"错误: 无法打开串口 {device}: {e}", file=sys.stderr)
        sys.exit(1)

    outfile = None
    if args.output:
        outfile = open(args.output, "wb")  # [文件] 原始字节日志

    t0 = time.time()
    try:
        while True:
            # [退出条件] 到达 -e 指定时长后自动退出
            if args.exit_after is not None and time.time() - t0 >= args.exit_after:
                break
            data = ser.read(4096)  # [读取] 一次性读出已到达的字节
            if data:
                # [输出] 原始字节透传 stdout（不解码不过滤，UTF-8 中文无损）
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
                if outfile:
                    outfile.write(data)
    except KeyboardInterrupt:
        pass  # [退出] Ctrl-C 手动结束
    finally:
        ser.close()
        if outfile:
            outfile.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
