# Zephyr 项目模板指南

> 创建新的 Zephyr 项目时，生成以下完整文件。所有文件必须完整，不使用省略号。
> 应用目录放在工作区根目录下，如 `/home/hero/zephyrproject/my_app`。

---

## ★ 核心架构原则（违反则视为错误）

| 规则 | 说明 |
|------|------|
| **main.c 禁止写业务逻辑** | main() 只做两件事：① `LOG_INF("Board: %s", CONFIG_BOARD)` ② `k_sleep(K_FOREVER)` |
| **业务逻辑独立线程化** | 每个功能（LED/按键/传感器/通信）一个独立线程文件（如 `led_thread.c`） |
| **K_THREAD_DEFINE 自启动** | 线程通过 `K_THREAD_DEFINE` 定义并自动启动，main.c 不手动创建线程 |
| **一类功能 = 一个文件** | LED → led_thread.c、按键 → key_thread.c、传感器 → sensor_thread.c |
| **项目必须含 README.md** | 板型号 + 项目目标 + 编译/接线/运行说明 |

> **反面案例（禁止）**：把 LED 的 GPIO 初始化、while(1) 循环直接写在 main() 中。
> **正面案例（必须）**：main.c 仅打印信息后 `k_sleep(K_FOREVER)`，LED 操作全部放在 `led_thread.c` 中。

---

## 文件结构总览

```
<项目名>/
├── CMakeLists.txt          # CMake 构建文件
├── prj.conf                # Kconfig 应用配置
├── Kconfig                 # (可选) 应用级 Kconfig 选项
├── sysbuild.conf           # (可选) 多映像/多固件构建（Sysbuild）的配置文件
├── VERSION                 # Zephyr 生命周期管理
├── README.md               # 项目说明（板型号、项目目标、如何编译、接线和运行）
├── boards/
│   └── <板名>.overlay      # 设备树覆盖文件, 需要用 Zephyr 实际支持的板名替换 ★关键
│                           #   命名规则: 目标板名中的 / 换成 _ (三厂商通用)
│                           #   NXP:     frdm_mcxn947_mcxn947_cpu0.overlay
│                           #   ESP32:   esp32s3_devkitc_esp32s3_procpu.overlay
│                           #   STM32:   nucleo_f103rb.overlay
├── include/
│   └── xxx_thread.h        # (可选) 应用程序头文件
├── src/
│   ├── main.c              # ★ 仅打印板信息+永久休眠，禁止写业务逻辑
│   └── xxx_thread.c        # ★ 一类功能对应一个独立线程 (含详尽中文注释)
└── sysbuild/               # (可选) 二级引导程序配置
    ├── mcuboot.conf        # 为 MCUboot (Bootloader) 准备的配置文件
    └── mcuboot.overlay     # 为 MCUboot (Bootloader) 准备的设备树覆盖文件
```

> **重要**：`VERSION` 是 Zephyr 应用的标准文件。构建后在 `build/zephyr/include/generated/zephyr/app_version.h` 生成 `APP_VERSION_MAJOR/MINOR/PATCHLEVEL/TWEAK` 宏供代码引用。

---

## VERSION — 应用版本号

```makefile
VERSION_MAJOR = 0
VERSION_MINOR = 1
PATCHLEVEL = 0
VERSION_TWEAK = 0
```

| 字段 | 说明 |
|------|------|
| `VERSION_MAJOR` | 主版本号，重大架构变更时递增 |
| `VERSION_MINOR` | 次版本号，新增功能时递增 |
| `PATCHLEVEL` | 补丁级别，Bug修复时递增 |
| `VERSION_TWEAK` | 微调版本，细微调整时递增（★ 必须存在，GCC 14+ 强制要求） |

---

## CMakeLists.txt — 构建入口

```cmake
# SPDX-License-Identifier: Apache-2.0
# [构建配置] Zephyr 项目的 CMake 构建入口

cmake_minimum_required(VERSION 3.20.0)

# [查找 Zephyr] 引入 Zephyr 构建系统
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

# [定义项目] 项目名称，建议英文小写+下划线
project(my_app)

# [添加源文件] app 是 Zephyr 预定义的应用目标
target_sources(app PRIVATE src/main.c src/led_thread.c)
```

---

## prj.conf — Kconfig 基础配置

```
# ==================== Zephyr 基础配置 ====================

# [GPIO] 启用 GPIO 驱动
CONFIG_GPIO=y

# [日志] 启用 Zephyr 日志子系统
CONFIG_LOG=y

# [线程命名] 为线程启用名称，便于调试
CONFIG_THREAD_NAME=y

# [断言] 开发阶段建议开启
CONFIG_ASSERT=y
```

### 按需启用

```
# [I2C] 传感器 → CONFIG_I2C=y
# [SPI] LCD/Flash → CONFIG_SPI=y
# [PWM] 呼吸灯/电机 → CONFIG_PWM=y
# [ADC] 模拟量采集 → CONFIG_ADC=y
# [传感器] → CONFIG_SENSOR=y
# [LED API] → CONFIG_LED=y + CONFIG_LED_GPIO=y
# [Shell] 交互调试 → CONFIG_SHELL=y
# [LVGL] 图形库 → CONFIG_LVGL=y
```

---

## Kconfig — 应用级自定义配置

> **★ 关键规则**：应用级 `Kconfig` 文件**必须**包含 `source "Kconfig.zephyr"`，否则所有 Zephyr 系统符号（GPIO、LOG、I2C 等）都无法识别。

```kconfig
mainmenu "My Zephyr Application"

# ★★★ 必须！加载 Zephyr 系统 Kconfig 符号树 ★★★
source "Kconfig.zephyr"

# [自定义] LED 闪烁间隔
config MY_LED_BLINK_MS
	int "LED blink interval (ms)"
	default 500
	help
	  LED 闪烁间隔时间，单位毫秒。
```

---

## boards/<板名>.overlay — 设备树覆盖

板名覆盖文件命名规则：目标板名中每段用 `_` 连接（`/` 换成 `_`）。示例：

- NXP 双核: `boards/frdm_mcxn947_mcxn947_cpu0.overlay`（目标 `frdm_mcxn947/mcxn947/cpu0`）
- ESP32 双核: `boards/esp32s3_devkitc_esp32s3_procpu.overlay`（目标 `esp32s3_devkitc/esp32s3/procpu`）
- STM32 单核: `boards/nucleo_f103rb.overlay`（目标 `nucleo_f103rb`）

```dts
/*
 * [设备树覆盖] FRDM-MCXN947 (CPU0)
 *
 * 板级 DTS 已定义（见 boards/nxp/frdm_mcxn947/）：
 *   - green_led / red_led
 *   - user_button_2
 *   - flexcomm4 = 控制台 UART (P1_8 RX / P1_9 TX)
 */

/ {
	aliases {
		/* [别名] 为 LED 添加别名，代码中 DT_ALIAS(led0) 引用 */
		led0 = &green_led;
	};
};
```

---

## src/main.c — 模板

```c
/*
 * main.c — 应用主入口
 *
 * ★ 只做两件事:
 *   1. 打印启动信息 (LOG_INF("Board: %s", CONFIG_BOARD))
 *   2. k_sleep(K_FOREVER) 永久休眠
 *
 * 所有业务逻辑放在独立线程文件中 (led_thread.c / key_thread.c ...)
 * 线程通过 K_THREAD_DEFINE 定义并自动启动
 */

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

/* [日志] 注册 main 模块 */
LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

int main(void)
{
	/* [初始化] 打印板卡信息 */
	LOG_INF("应用启动完成, Board: %s", CONFIG_BOARD);

	/* [休眠] 永久休眠，业务逻辑由独立线程处理 */
	k_sleep(K_FOREVER);
	return 0;
}
```

---

## src/led_thread.c — 独立线程模板

```c
/*
 * led_thread.c — LED 闪烁线程
 *
 * 架构: 一类功能 = 一个线程文件 = 一个 K_THREAD_DEFINE
 *       main.c 不创建线程, K_THREAD_DEFINE 自动启动
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

/* [日志] 注册 led_thread 模块 */
LOG_MODULE_REGISTER(led_thread, LOG_LEVEL_INF);

/* [设备树] 板载 LED（overlay 中 aliases 定义 led0） */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

/* [线程入口] 线程入口函数 */
void led_thread_entry(void *p1, void *p2, void *p3)
{
	k_msleep(2000);  /* [等待] 等待系统稳定 */

	if (!gpio_is_ready_dt(&led)) {
		LOG_ERR("LED GPIO 未就绪");
		return;
	}

	/* [配置] 输出模式，初始灭 */
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	LOG_INF("[LED] 线程启动");

	/* [操作] 周期闪烁 */
	while (1) {
		gpio_pin_toggle_dt(&led);
		k_msleep(1000);
	}
}

/* [线程配置] 栈大小和优先级（必须放在 K_THREAD_DEFINE 紧前面） */
#define LED_STACK_SIZE 1024
#define LED_PRIORITY    14

K_THREAD_DEFINE(led_tid, LED_STACK_SIZE,
		led_thread_entry, NULL, NULL, NULL,
		LED_PRIORITY, 0, 0);
```

---

## README.md — 模板

```markdown
# <项目名>

## 硬件平台

- 开发板: <按实际填写，如 FRDM-MCXN947 / ESP32-S3 DevKitC-1 / Nucleo-F103RB>
- 编译目标: <按实际填写，如 frdm_mcxn947/mcxn947/cpu0、esp32s3_devkitc/esp32s3/procpu、nucleo_f103rb>
- 调试器: <按实际填写，如 MCU-Link / 板载 USB-UART / ST-LINK>

## 项目目标

<一句话描述项目做什么>

## 功能列表

- [x] 功能 1
- [x] 功能 2

## 编译

```bash
# -b 参数按目标板替换；开启 MCUboot 时加 --sysbuild
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b <目标板名> ./<项目名>
```

## 烧录

```bash
# NXP:  west flash
# ESP32: west flash --esp-device /dev/ttyUSB0
# STM32: west flash --runner pyocd
west flash
```

## 串口

- 端口: /dev/ttyACM0 (按实际替换)
- 波特率: 115200

## 运行

<启动后预期现象>
```

---

## 编译命令

```bash
# 完整构建（-b 参数按目标板替换，如 nucleo_f103rb / esp32s3_devkitc/esp32s3/procpu）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b frdm_mcxn947/mcxn947/cpu0 ./my_app

# 带 MCUboot 的 sysbuild 构建（prj.conf 含 CONFIG_BOOTLOADER_MCUBOOT=y 时 ★必须）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b frdm_mcxn947/mcxn947/cpu0 --sysbuild ./my_app
```
