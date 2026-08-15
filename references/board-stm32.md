# STM32 板卡通用参考（Zephyr）

> 适用范围: ST 全系板卡 — Nucleo 系列、WeAct 核心板、其他 STM32 开发板
> 板卡目录: `/home/hero/zephyrproject/zephyr/boards/st/<板名>/`、`/home/hero/zephyrproject/zephyr/boards/weact/<板名>/`
> 本文档提供**通用方法**（识别板卡、烧录、排查），具体引脚一律查对应板级设备树。

---

## 1. ★ 板卡识别方法（开工前第一步）

用户只说 "STM32" 时，按以下顺序确定具体板名：

```bash
cd /home/hero/zephyrproject && source .venv/bin/activate && west boards | grep -iE "stm32|nucleo|weact|blackpill"
```

- 板名 = 输出列表中的目录名（如 `nucleo_f103rb`、`blackpill_f401cc`）
- 板卡目录下 `board.yml` 描述芯片型号；`board.cmake` 描述烧录 runner 参数
- 若用户报出芯片型号（如 STM32F103C8T6）→ 用 `west boards | grep` 找到对应板（`nucleo_f103rb` = F103RB/RCT6 系列、`blackpill_f401cc` = F401CCU6）
- 找不到精确匹配时询问用户，不猜

## 2. 常见板卡速查

| 板名 | 芯片 | 板载调试器 | 常见场景 |
|------|------|-----------|----------|
| `nucleo_f103rb` | STM32F103RB (M3) | ST-LINK | ★ 最经典入门板 |
| `nucleo_f401re` | STM32F401RE (M4F) | ST-LINK | 入门/教程常用 |
| `nucleo_l476rg` | STM32L476RG (M4F) | ST-LINK | 低功耗 |
| `nucleo_h743zi` | STM32H743ZI (M7) | ST-LINK | 高性能 |
| `nucleo_g474re` | STM32G474RE (M4F) | ST-LINK | 电机控制 |
| `blackpill_f401cc` (weact) | STM32F401CCU6 (M4F) | 无（需外接 ST-LINK） | 低成本核心板 |
| `blackpill_f411ce` (weact) | STM32F411CEU6 (M4F) | 无（需外接 ST-LINK） | 低成本核心板 |
| `stm32f405_core` / `stm32f446_core` (weact) | STM32F405/446 | 无 | 国产核心板 |

> 板级详情: `west boards` 确认板名后，查看
> `zephyr/boards/st/<板名>/<板名>.dtsi`（外设节点/别名）和 `<板名>-pinctrl.dtsi`（引脚复用）。

## 3. 硬件共性（区别于其他厂商）

- **调试器**：Nucleo 板载 ST-LINK（SWD + 虚拟串口 VCP）；WeAct 等核心板无板载调试器，需外接 ST-LINK（杜邦线 SWDIO/SWCLK/GND/3V3）
- **串口**：ST-LINK 虚拟串口 = `/dev/ttyACM0`（与烧录共用 USB 口）
- **电平**：3.3V 逻辑（5V 容忍输入看具体芯片，别默认）
- **LED/按键**：每块板不同 — 经典 nucleo_f103rb 的板载 LED 是 `LD2` 接 PB13（Zephyr 别名 `led0`），Nucleo 板大多有 `led0`/`led1`/`led2` 别名，具体查板级 `.dtsi` 的 `aliases`
- **控制台 UART**：Zephyr 默认输出到板级 chosen 指定的串口（nucleo_f103rb 为 `usart2` → ST-LINK VCP，115200）

## 4. 构建命令

```bash
# 完整构建（板名按实际替换）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b nucleo_f103rb ./my_app

# MCUboot 多镜像编译（prj.conf 含 CONFIG_BOOTLOADER_MCUBOOT=y 时 ★必须）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b nucleo_f103rb --sysbuild ./my_app

# menuconfig
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -b nucleo_f103rb -t menuconfig ./my_app
```

overlay 命名：单核板直接 `boards/nucleo_f103rb.overlay`。

## 5. 烧录 runner 选择（★ 本机关键）

| runner | 说明 | 本机状态 |
|--------|------|----------|
| `stm32cubeprogrammer` | ST 官方 CLI（STM32CubeProgrammer），Nucleo 板默认 runner | ⚠️ **未安装** → `west flash` 直接用它会报 `stm32cubeprogrammer: command not found` |
| `pyocd` | 开源 CMSIS-DAP/ST-Link 兼容烧录器 | ✅ **已安装**（venv 内 pyocd 0.45.1）→ 本机首选 |
| `jlink` | Segger J-Link | pylink 已装，但需要 J-Link 硬件 |

```bash
# ★ 本机推荐: 用 pyocd 烧录（ST-LINK 兼容）
west flash --runner pyocd

# 需要时显式指定设备
pyocd list --probes    # 查看已连接调试器

# 官方默认方式（需先安装 STM32CubeProgrammer CLI 并加入 PATH）
west flash
```

> 注意：`west flash` 不加参数时按板级默认 runner（stm32cubeprogrammer）执行，本机未安装会失败 — **STM32 一律显式 `--runner pyocd`**。

## 6. 串口监视

```bash
# ST-LINK 虚拟串口（Nucleo 板）
python -m serial.tools.miniterm /dev/ttyACM0 115200

# 无板载调试器（WeAct 等外接 ST-LINK）时无 VCP → 需 USB 转 TTL 接 UART 引脚
```

> 权限问题：`ls -l /dev/ttyACM0` 属主不是你的组时执行 `sudo usermod -aG dialout $USER` 后重新登录。

## 7. MCUboot 注意

- STM32 支持 MCUboot，流程与 SKILL.md 的 MCUboot 章节完全一致（`--sysbuild` + 分区 + 签名）
- STM32 内部 Flash 以扇区为粒度，`CONFIG_BOOT_MAX_IMG_SECTORS_AUTO=y` 尤其重要
- 部分板（如 nucleo_h743zi）Flash 较大，分区 offset 按 Flash 大小合理规划

## 8. 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `Board nucleo_xxx not found` | 板名拼写错误 / 板不存在 | `west boards \| grep -i stm32` 确认 |
| `stm32cubeprogrammer: command not found` | STM32CubeProgrammer 未安装 | 用 `--runner pyocd`；或安装 STM32CubeProgrammer 并配置 PATH |
| `pyocd: No available probes found` | 调试器未连接/驱动问题 | 检查 USB 连接；`pyocd list --probes`；`lsusb` 应见 ST-LINK (0483:3748) |
| `Error: unable to find CMSIS-DAP device` | 同上 | 重插 USB；换线；确认外接调试器接线正确 |
| 烧录成功但无串口输出 | 串口设备/权限/波特率问题 | `ls /dev/ttyACM*`；`sudo usermod -aG dialout $USER`；115200 |
| 烧录后程序跑飞/HardFault | 时钟/引脚配置与板不符 | 确认 overlay 节点来自该板 `.dtsi`；对照板级 pinctrl |
| 编译报 `.text` 溢出 | Flash 空间不足 | 关闭非必要 Kconfig 功能 |

## 9. 快速参考

```bash
# 查板卡
cd /home/hero/zephyrproject && source .venv/bin/activate && west boards | grep -i stm32

# 构建（nucleo_f103rb 示例）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b nucleo_f103rb ./my_app

# 烧录（本机用 pyocd）
west flash --runner pyocd

# 串口
python -m serial.tools.miniterm /dev/ttyACM0 115200

# 查看板级设备树（外设节点/别名/引脚）
cat /home/hero/zephyrproject/zephyr/boards/st/nucleo_f103rb/nucleo_f103rb.dtsi
cat /home/hero/zephyrproject/zephyr/boards/st/nucleo_f103rb/nucleo_f103rb-pinctrl.dtsi
```
