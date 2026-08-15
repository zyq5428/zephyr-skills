# Zephyr 构建与烧录指南（本机 Linux，三厂商通用）

> 适用于本机（WSL2）Zephyr 工作区 `~/zephyrproject`，覆盖 NXP / Espressif / ST 三厂商板卡。
> 开工前先确定目标板卡厂商（见 SKILL.md「板卡选择机制」）。

---

## 1. 环境激活（每次新终端必须执行）

west 安装在 `~/zephyrproject/.venv` 中，**必须激活虚拟环境**，否则报 `command not found`：

```bash
cd /home/hero/zephyrproject && source .venv/bin/activate
```

验证：

```bash
west --version
# 应输出类似: West version: v1.5.0
```

---

## 2. ★ 板卡 → runner → 命令 速查矩阵

| 厂商 | 代表构建目标 | 烧录 runner | 烧录命令 | 串口监视命令 |
|------|--------------|-------------|----------|--------------|
| NXP | `frdm_mcxn947/mcxn947/cpu0` | linkserver（板载 MCU-Link） | `west flash` | `python -m serial.tools.miniterm /dev/ttyACM0 115200` |
| Espressif | `esp32s3_devkitc/esp32s3/procpu` | esptool | `west flash --esp-device /dev/ttyUSB0` | `west espressif monitor -p /dev/ttyUSB0` |
| ST | `nucleo_f103rb` 等 | ★ pyocd（stm32cubeprogrammer 本机未装） | `west flash --runner pyocd` | `python -m serial.tools.miniterm /dev/ttyACM0 115200` |

> 备选 runner（本机均已具备能力）：NXP `--runner pyocd`；ST `--runner jlink`（需 J-Link 硬件）。

---

## 3. 构建命令（通用形式）

```bash
# 完整清理构建（首次构建或修改 prj.conf/overlay 后）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b <目标板名> ./my_app

# 增量构建（仅修改代码时，更快）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -b <目标板名> ./my_app

# 构建官方示例验证环境
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b <目标板名> ./zephyr/samples/basic/blinky

# 查看可用板卡（按厂商过滤）
west boards | grep -iE "mcxn947|esp32s3|stm32|nucleo|weact"
```

| 参数 | 说明 |
|------|------|
| `-p always` | 完全清理后构建（pristine），删除缓存 |
| `-p auto` | 自动判断（默认） |
| `-b <板名>` | 目标板（单核板直接板名；多核板三段式，如 `frdm_mcxn947/mcxn947/cpu0`、`esp32s3_devkitc/esp32s3/procpu`） |
| `--sysbuild` | ★ 开启 MCUboot 后必须加（否则只编应用不编引导程序） |

### 构建配置工具

```bash
# 文本菜单配置
west build -b <目标板名> -t menuconfig ./my_app

# 图形化配置（需要 X 显示）
west build -b <目标板名> -t guiconfig ./my_app
```

---

## 4. 烧录命令

### NXP — FRDM-MCXN947（linkserver）

板载 **MCU-Link 调试器（CMSIS-DAP）**，默认 runner 为 **Linkserver**：

```bash
west flash                                    # 自动使用 Linkserver
west flash --runner linkserver                # 显式指定
west flash --runner pyocd                     # 备用方案
```

烧录前检查：USB 连接 MCU-Link 口（Type-C）；`ls /dev/ttyACM* /dev/ttyUSB*` 能看到串口；`lsusb` 能看到 NXP 设备（VID 1fc9）。

### Espressif — ESP32-S3（esptool）

```bash
west flash --esp-device /dev/ttyUSB0          # ★ 必须指定串口设备
west flash --esp-device /dev/ttyACM0          # 部分环境枚举为 ACM
```

烧录前检查：数据线连接 **Micro-USB（UART 口）**；`ls /dev/ttyUSB*` 有设备。烧录失败时手动进下载模式（按住 Boot → 按 Reset → 松 Reset → 松 Boot）。

### ST — STM32（pyocd）

```bash
west flash --runner pyocd                     # ★ 本机首选（ST-LINK 兼容）
pyocd list --probes                           # 查看调试器
west flash                                    # 默认 runner 为 stm32cubeprogrammer → 本机未装会失败
```

> STM32CubeProgrammer 安装后可 `west flash` 直用；未装时一律显式 `--runner pyocd`。

---

## 5. 串口监视

```bash
# 通用（NXP / ST）
python -m serial.tools.miniterm /dev/ttyACM0 115200

# ESP32 专用监视器
west espressif monitor -p /dev/ttyUSB0

# 保存日志到文件
script -c "python -m serial.tools.miniterm /dev/ttyACM0 115200" serial.log
```

### 串口输出示例

```
*** Booting Zephyr OS build v4.4.2-xxx ***
[00:00:00.000] <inf> my_app: 应用启动完成, Board: frdm_mcxn947/mcxn947/cpu0
[00:00:00.001] <inf> my_app: [LED] 线程启动
```

---

## 6. 构建产物

`build/zephyr/` 目录关键文件（三厂商通用）：

| 文件 | 说明 |
|------|------|
| `zephyr.elf` | ELF 可执行文件（含调试信息） |
| `zephyr.bin` | 二进制固件 |
| `zephyr.hex` | Intel HEX 格式固件 |
| `zephyr.map` | 内存映射（分析 RAM/Flash 使用） |
| `.config` | 最终 Kconfig 合并配置 |
| `zephyr.dts` | 预处理后的设备树（调试用） |
| `include/generated/zephyr/autoconf.h` | Kconfig 生成的 C 宏 |
| `include/generated/zephyr/devicetree_generated.h` | 设备树生成的 C 宏 |
| `include/generated/zephyr/app_version.h` | VERSION 文件生成的版本宏 |

---

## 7. 清理

```bash
# 清理构建产物（保留配置）
west build -t clean

# 完全删除构建目录
rm -rf build
```

---

## 8. 调试

### 硬件调试（SWD）

```bash
# west debug 会自动启动调试器并连接（NXP 经 MCU-Link / ST 经 ST-LINK）
west debug --runner pyocd

# 或手动：pyocd 启动调试服务器（目标名查 pyocd list --targets）
pyocd gdbserver -t <target>
```

```bash
# GDB 连接（arm 工具链；ESP32 用 xtensa-esp32s3-elf-gdb）
arm-zephyr-eabi-gdb build/zephyr/zephyr.elf
# (gdb) target remote :3333
# (gdb) monitor reset halt
# (gdb) continue
```

### 打印调试

```c
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(my_app, LOG_LEVEL_DBG);
LOG_DBG("调试: x=%d", x);
LOG_INF("运行正常");
LOG_ERR("错误: err=%d", err);
```

---

## 9. 常见错误及解决

| 错误 | 原因 | 解决 |
|------|------|------|
| `west: command not found` | 未激活 venv | `source /home/hero/zephyrproject/.venv/bin/activate` |
| `Board xxx not found` | 板卡名拼写错误 | `west boards \| grep <关键词>` 确认 |
| Kconfig "undefined symbol" | 应用 Kconfig 缺少 `source "Kconfig.zephyr"` | 在 Kconfig 文件的 mainmenu 后添加 |
| `section '.text' will not fit in 'FLASH'` | Flash 空间不足 | 关闭非必要功能，使用 `-Os` 优化 |
| `undefined reference to __device_dts_ord_` | 设备树引用错误 | 检查 overlay 中 status="okay" 和节点名拼写 |
| `k_msleep(K_FOREVER)` 编译错误 | 类型不匹配 | 改为 `k_sleep(K_FOREVER)` |
| 烧录后无串口输出 | 串口设备号不对 | `ls /dev/ttyACM* /dev/ttyUSB*` 确认实际设备号 |
| `stm32cubeprogrammer: command not found` | STM32CubeProgrammer 未安装 | 用 `west flash --runner pyocd` |
| `pyocd: No available probes found` | STM32 调试器未识别 | `pyocd list --probes`；重插 USB；外接 ST-LINK 检查接线 |
| Linkserver 找不到设备（NXP） | 调试器固件问题 | 重新插拔 USB；或换 `--runner pyocd` |
| `west flash` 报串口失败（ESP32） | 串口不对/未在下载模式 | `ls /dev/ttyUSB*`；手动进下载模式 |
| `/dev/ttyACM0` 权限拒绝 | 用户不在 dialout 组 | `sudo usermod -aG dialout $USER` 后重新登录 |

---

## 10. 快速排查清单

1. 已确定目标板卡厂商与板名（NXP / Espressif / ST）
2. USB 已连接正确接口（NXP: MCU-Link 口 / ESP32: Micro-USB UART 口 / ST: ST-LINK 口）
3. `ls /dev/ttyACM* /dev/ttyUSB*` 确认串口设备号
4. 已执行 `source /home/hero/zephyrproject/.venv/bin/activate`
5. prj.conf 启用了所需功能
6. overlay 中对应外设 `status = "okay"`
7. overlay 节点来自目标板实际设备树（不跨板猜节点）
8. 应用 Kconfig 文件中包含 `source "Kconfig.zephyr"`
9. 串口监视波特率 115200
10. 开启 MCUboot 时已加 `--sysbuild`
