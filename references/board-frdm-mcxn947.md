# FRDM-MCXN947 板卡硬件参考

> 板卡: NXP FRDM-MCXN947（MCX-N94x 系列）
> 设备树源: `/home/hero/zephyrproject/zephyr/boards/nxp/frdm_mcxn947/`
> SoC 源: `/home/hero/zephyrproject/zephyr/soc/nxp/mcx/mcxn94x/`

---

## 1. 主控 MCU

| 参数 | 值 |
|------|-----|
| SoC | MCX-N947（N94x 系列） |
| CPU | 双 Arm Cortex-M33 @ 150MHz（CPU0 主核 / CPU1 副核） |
| Flash | 2MB 双 bank 片上 Flash |
| RAM | 512KB（srama 320KB + sramg 64KB + sramh 32KB） |
| 外部存储 | Quad SPI NOR Flash（FlexSPI 接口） |
| 外设 | 10x Flexcomm（可配 UART/SPI/I2C）、2x FlexCAN FD、2x I3C、2x SAI、Ethernet QoS、USB HS |
| 调试器 | 板载 MCU-Link（CMSIS-DAP），Linkserver 为默认 runner |

## 2. 内存布局

| 区域 | 大小 | 说明 |
|------|------|------|
| srama | 320KB @ 0x20000000 | CPU0 主 RAM（`zephyr,sram = &sram0`） |
| sramg | 64KB | CPU1 RAM |
| sramh | 32KB | CPU0/CPU1 共享内存（IPC 用） |
| flash | 2MB @ 0x0 | 双 bank（`zephyr,flash = &flash`） |

> CPU0 访问全部 Flash；CPU1 被限制在 slot1_partition 区域。双核通信参考
> `samples/subsys/ipc/ipc_service/static_vrings`、`samples/subsys/ipc/openamp`。

## 3. 构建目标（变体）

| 目标 | 说明 |
|------|------|
| `frdm_mcxn947/mcxn947/cpu0` | 默认，主核独立运行（★ 普通应用用这个） |
| `frdm_mcxn947/mcxn947/cpu1` | 副核，必须由 CPU0 + `CONFIG_SECOND_CORE_MCUX=y` + sysbuild 启动 |
| `frdm_mcxn947/mcxn947/cpu0_ns` | 非安全模式变体 |
| `frdm_mcxn947/mcxn947/cpu0_qspi` | 外部 QSPI Flash 启动变体 |

## 4. 串口与引脚（板级默认配置）

| 功能 | Flexcomm | 引脚 | 说明 |
|------|----------|------|------|
| 控制台 UART | Flexcomm4 (LPUART4) | P1_8 RX / P1_9 TX | `zephyr,console` + `zephyr,shell-uart`，115200 |
| CPU1 UART | — | P4_3 RX / P4_2 TX | 副核串口 |

> 其他 Flexcomm 外设节点与 pinctrl 节点名以板级文件为准：
> `frdm_mcxn947.dtsi`（外设节点）、`frdm_mcxn947-pinctrl.dtsi`（pinctrl 节点）。
> 查找方法：`grep -n "flexcomm" /home/hero/zephyrproject/zephyr/boards/nxp/frdm_mcxn947/frdm_mcxn947.dtsi`

## 5. 板载器件（设备树节点）

| 器件 | 节点标签 | 说明 |
|------|----------|------|
| 绿色 LED | `green_led` | 板载 GPIO LED |
| 红色 LED | `red_led` | 板载 GPIO LED |
| 用户按键 | `user_button_2` | 板载按键 |
| 控制台 UART | `flexcomm4_lpuart4` | LPUART4，115200 |

> 完整的板上器件/别名列表读取：
> `cat /home/hero/zephyrproject/zephyr/boards/nxp/frdm_mcxn947/frdm_mcxn947_mcxn947_cpu0.dtsi`

## 6. 时钟

- PLL0 运行 150MHz，作为系统时钟源。

## 7. 烧录与调试

| 项目 | 值 |
|------|-----|
| 调试器 | 板载 MCU-Link（CMSIS-DAP） |
| 默认 runner | Linkserver（`west flash` 直接使用） |
| 备用 runner | pyocd / jlink |
| USB 接口 | Type-C（MCU-Link 调试口） |
| 虚拟串口 | ★ `/dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947*`（实测有效，`-if02` 接口为虚拟 COM 口；也可用 `/dev/ttyACM0`） |

## 8. 支持的 Shields

- `lcd_par_s035` — 显示接口（MIPI_DBI，接 FlexIO）
- `dvp_20pin_ov7670` — SmartDMA 视频接口

## 9. 快速参考

```bash
# 构建
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b frdm_mcxn947/mcxn947/cpu0 ./my_app

# 烧录
west flash

# 串口（★ 已验证 SOP：by-id 通配符 + grabserial，-e 5 = 抓 5 秒退出）
grabserial -d /dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947* -b 115200 -e 5
# ⚠️ 中文/UTF-8 输出用技能自带工具 tools/serial_monitor.py（grabserial 平替，字节透明）
/home/hero/zephyrproject/.venv/bin/python3 ~/.claude/skills/zephyr-skill/tools/serial_monitor.py \
    -d /dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947* -b 115200 -e 5
# 备选：交互式监视
python -m serial.tools.miniterm /dev/ttyACM0 115200

# 查看板级设备树
cat /home/hero/zephyrproject/zephyr/boards/nxp/frdm_mcxn947/frdm_mcxn947_mcxn947_cpu0.dtsi
```
