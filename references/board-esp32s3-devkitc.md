# ESP32-S3-DevKitC-1 v1.1 板卡硬件参考（N32R16V）

> 板卡: Espressif ESP32-S3-DevKitC-1 v1.1（ESP32-S3-WROOM-2-N32R16V 模组）
> 设备树源: `/home/hero/zephyrproject/zephyr/boards/espressif/esp32s3_devkitc/`
> SoC 源: `/home/hero/zephyrproject/zephyr/dts/xtensa/espressif/esp32s3/`
> 构建目标: `esp32s3_devkitc/esp32s3/procpu`（★ 默认主核，普通应用用这个）

---

## 1. 模组规格（ESP32-S3-WROOM-2-N32R16V）

| 参数 | 值 |
|------|-----|
| 芯片 | ESP32-S3（Xtensa LX7 双核 @ 240MHz） |
| Flash | **32MB Octal SPI @ 1.8V** |
| PSRAM | **16MB Octal SPI @ 1.8V** |
| SPI 电压 | **1.8V**（与 WROOM-1 系列 3.3V 不兼容） |
| Wi-Fi | 2.4GHz 802.11 b/g/n |
| BLE | Bluetooth 5.0 LE |
| GPIO 总数 | 45 个（但 GPIO35/36/37 被 Flash/PSRAM 占用） |

> ★ **Zephyr 板级默认是 `esp32s3_wroom_n8.dtsi`（8MB Flash、无 PSRAM）**。
> 使用 N32R16V 模组必须用 overlay 切换到 `esp32s3_wroom_n32r16.dtsi`（见第 6 节）。

## 2. 关键引脚速查

| 引脚 | 功能 | 备注 |
|------|------|------|
| GPIO43 / GPIO44 | UART0 TX / RX | ★ 板载 USB 转 UART（CP2102），默认控制台/Shell 串口 |
| GPIO1 / GPIO2 | I2C0 SDA / SCL | I2C 默认引脚 |
| GPIO4 / GPIO5 | I2C1 SDA / SCL | I2C1 默认引脚 |
| GPIO17 / GPIO18 | UART1 TX / RX | UART1 默认引脚 |
| GPIO10/11/12/13 | SPI2 CS0/MOSI/SCLK/MISO | SPI2 默认引脚（注意避开 35-38） |
| GPIO0 | Boot 按钮 | Strapping pin（低电平=下载模式），勿作他用 |
| GPIO38 | **RGB LED (WS2812)** | v1.1 版本，与 SPIM3 CSEL 复用 |
| GPIO39/40/41/42 | JTAG TCK/TDO/TDI/TMS | 也可用 |
| GPIO19/20 | USB D- / D+ | USB OTG 占用时不可复用 |
| GPIO35/36/37 | ⛔ **绝对禁止使用** | Octal SPI Flash/PSRAM 内部占用 |

> ⛔ **禁用引脚**：GPIO35（SPIIO6）、GPIO36（SPIIO7）、GPIO37（SPIDQS）用于模组内部 Octal SPI 通信，外部使用会导致 Flash/PSRAM 读写失败、系统崩溃。Zephyr pinctrl 驱动也没有这些引脚的 GPIO 定义。

## 3. 板上组件映射

| 组件 | 连接引脚 | 设备树节点 | 备注 |
|------|----------|-----------|------|
| RGB LED (WS2812) | GPIO38 | `&led_strip`（需自定义/按驱动配置） | v1.1 版本 |
| Boot 按钮 | GPIO0 | `&button0` | 低电平触发，内部上拉 |
| USB 转 UART | TX=GPIO43, RX=GPIO44 | `&uart0` | 默认控制台 |
| USB OTG (Type-C) | D-=GPIO19, D+=GPIO20 | `&usb_otg` | ESP32-S3 原生 USB |

## 4. 构建目标（变体）

| 目标 | 说明 |
|------|------|
| `esp32s3_devkitc/esp32s3/procpu` | ★ 默认主核，普通应用用这个 |
| `esp32s3_devkitc/esp32s3/appcpu` | 副核，双核开发用（较复杂，多数应用不需要） |

## 5. 构建/烧录/串口（Linux bash）

```bash
# 构建（N32R16V 项目必须先建好 overlay，见第 6 节）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b esp32s3_devkitc/esp32s3/procpu ./my_app

# MCUboot 多镜像编译（prj.conf 含 CONFIG_BOOTLOADER_MCUBOOT=y 时 ★必须）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b esp32s3_devkitc/esp32s3/procpu --sysbuild ./my_app

# 烧录（runner = esptool，★必须指定串口设备；WSL2 下通常 /dev/ttyUSB0）
west flash --esp-device /dev/ttyUSB0

# 串口监视（espressif 专用监视器）
west espressif monitor -p /dev/ttyUSB0

# 或用通用工具
python -m serial.tools.miniterm /dev/ttyUSB0 115200
```

> 烧录失败时的手动下载模式：① 按住 **Boot** 按钮 → ② 按一下 **Reset** → ③ 松开 Reset → ④ 等 1 秒 → ⑤ 松开 Boot → ⑥ 重新 `west flash`。

## 6. ★ N32R16V 模组 overlay（32MB Flash + 16MB PSRAM）

Zephyr 板级默认使用 WROOM-N8（8MB Flash 无 PSRAM），**N32R16V 必须在应用 overlay 中切换**：

`boards/esp32s3_devkitc_esp32s3_procpu.overlay`:

```dts
/*
 * [设备树覆盖] ESP32-S3-DevKitC-1 (N32R16V 模组)
 *
 * 默认板级 = esp32s3_wroom_n8.dtsi (8MB Flash, 无 PSRAM)
 * ★ 必须切换到 esp32s3_wroom_n32r16.dtsi (32MB Flash + 16MB PSRAM)
 */

/* [模组配置] 切换到 N32R16V：32MB Octal Flash + 16MB Octal PSRAM */
#include <espressif/esp32s3/esp32s3_wroom_n32r16.dtsi>

/* [别名] 供代码 DT_ALIAS(led0) 引用 */
/ {
	aliases {
		/* 板载 RGB LED 在 GPIO38；未用 WS2812 时可做普通 GPIO */
		/* led0 = &led_strip; */
	};
};
```

prj.conf 补充（使用 PSRAM 时）：

```ini
# [PSRAM] 启用 ESP32-S3 外部 PSRAM（N32R16V 模组 16MB）
CONFIG_ESP32_SPIRAM=y
```

### ⚠️ blinky 示例不能直接编译（实测验证）

Zephyr 板级 `esp32s3_devkitc` 的 dts **没有定义任何 GPIO LED 节点，也没有 `led0` 别名**（板载是 WS2812 RGB LED，不是普通 GPIO LED）。直接 `west build ... ./zephyr/samples/basic/blinky` 会报：

```
error: '__device_dts_ord_DT_N_ALIAS_led0_P_gpios_IDX_0_PH_ORD' undeclared
```

**解决**：验证环境用 `hello_world` 示例；必须跑 blinky 时加 overlay 定义 led0（任选一个空闲 GPIO，如 GPIO2）：

```dts
/* boards/esp32s3_devkitc_esp32s3_procpu.overlay */
/ {
	leds {
		compatible = "gpio-leds";
		led0: led_0 {
			gpios = <&gpio0 2 GPIO_ACTIVE_HIGH>;  /* 任选空闲 GPIO */
			label = "User LED";
		};
	};
	aliases {
		led0 = &led0;
	};
};
```

> 若想点亮板载 WS2812 RGB LED，需按 `led-strip` 驱动配置（GPIO38），不能用 blinky 的普通 GPIO 方式。

## 7. WiFi / BLE 配置

### WiFi（STA 模式）

```ini
# prj.conf
CONFIG_WIFI=y
CONFIG_WIFI_ESP32=y
CONFIG_NETWORKING=y
CONFIG_NET_L2_ETHERNET=y
```

代码示例参考 `samples/net/wifi/` 目录。

### BLE

```ini
# prj.conf
CONFIG_BT=y
CONFIG_BT_HCI_ESP32=y
```

> 板级 dts 中 `chosen { zephyr,bt-hci = &esp32_bt_hci; };` 已配好，无需额外 overlay。

## 8. MCUboot / 分区

- ESP32 分区由 Espressif 分区文件定义（默认板级包含 `<espressif/partitions_0x0_amp.dtsi>`）
- 用 MCUboot 时：overlay 中包含 32M Flash 的分区文件，例如：
  ```dts
  #include <espressif/partitions_0x0_amp_32M.dtsi>
  ```
- 编译必须加 `--sysbuild`（见 SKILL.md 的 MCUboot 章节，三厂商通用）
- 可用 `west flash --esp-device /dev/ttyUSB0` 烧录（烧录器经 USB 转 UART，不经 MCUboot 也可）

## 9. 常见错误

| 错误 | 原因 | 解决 |
|------|------|------|
| blinky 编译报 `__device_dts_ord_..._led0...` undeclared | 板级无 `led0` 别名（板载是 WS2812） | 加 overlay 定义 led0（见第 6 节），或改用 hello_world |
| `error: 'GPIO35' undeclared` | 用了禁用引脚 | 换可用引脚，避开 GPIO35/36/37 |
| `section '.dram0.bss' will not fit` | 内部 SRAM 不足 | 减小静态缓冲区 / 大缓冲放 PSRAM（CONFIG_ESP32_SPIRAM=y + shared_multi_heap） |
| `esp32_spiram: SPIRAM not initialized` | PSRAM 配置不正确 | prj.conf 加 `CONFIG_ESP32_SPIRAM=y` + overlay 包含 `esp32s3_wroom_n32r16.dtsi` |
| `Board esp32s3_devkitc not found` | 板名拼写错误 | `west boards \| grep esp32s3` 确认 |
| 烧录失败/无响应 | 自动下载模式失灵 | 手动进入下载模式（Boot+Reset 组合，见第 5 节） |
| 串口无输出 | 连接错端口 | 确认接 **Micro-USB（UART）口** 而不是 Type-C（OTG）口 |

## 10. 快速参考

```bash
# 构建
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b esp32s3_devkitc/esp32s3/procpu ./my_app

# 烧录
west flash --esp-device /dev/ttyUSB0

# 串口
west espressif monitor -p /dev/ttyUSB0

# 查看板级设备树（默认 8MB Flash 配置）
cat /home/hero/zephyrproject/zephyr/boards/espressif/esp32s3_devkitc/esp32s3_devkitc_procpu.dts

# 查看模组变体
ls /home/hero/zephyrproject/zephyr/dts/xtensa/espressif/esp32s3/esp32s3_wroom_*.dtsi
```
