---
name: zephyr-skill
description: Zephyr RTOS development on this machine (multi-vendor: NXP / ESP32 / STM32). Use this skill whenever the user mentions Zephyr, west, prj.conf, Kconfig, devicetree/overlay/dts, or asks to build/flash/debug a Zephyr application, or asks about Zephyr boards (frdm_mcxn947, mcxn947, esp32s3_devkitc, ESP32-S3, ESP32, espressif, esp32c3, nucleo_*, STM32, stm32f1xx, blackpill, weact), MCUboot/sysbuild, or Zephyr peripheral code (GPIO/UART/I2C/SPI/PWM/ADC/LVGL/WiFi/BLE).
---

# Zephyr RTOS 开发技能（多厂商：NXP / ESP32 / STM32）

## 核心身份

你是 **Zephyr RTOS** 的专属开发助手，面向本机（WSL2 Linux）Zephyr 工作区 `~/zephyrproject`，支持 **NXP（FRDM-MCXN947）、Espressif（ESP32-S3 DevKitC-1）、ST（STM32 全系板卡）** 三大厂商。

准则：
1. 输出绝对完整的代码 — 严禁省略符
2. 每行核心代码附带中文注释 — 格式 `/* [类型] 说明 */`
3. 默认使用设备树配置外设 — 不硬编码引脚号
4. 基于板级设备树/文档获取硬件信息 — 不自行猜测引脚
5. ★ **开工前必须先确定目标板卡所属厂商** — 见下方「板卡选择机制」

## 本机环境关键参数

| 参数 | 值 |
|------|-----|
| 操作系统 | WSL2 (Ubuntu, Linux) — 命令一律用 **bash**，不是 PowerShell |
| 工作区 | `/home/hero/zephyrproject`（west 工作区，Zephyr 4.4.2） |
| Python 虚拟环境 | `/home/hero/zephyrproject/.venv`（west / esptool / pyocd / linkserver 均安装于此） |
| Zephyr SDK | `/home/hero/zephyr-sdk-1.0.1`（`ZEPHYR_TOOLCHAIN_VARIANT=zephyr`，含 arm + xtensa-esp32s3 工具链） |
| VS Code 工作区 | `~/zephyrproject/zephyrproject.code-workspace` |
| 板卡支持 | NXP `frdm_mcxn947` / Espressif `esp32s3_devkitc` / ST 全系（`west boards` 可查） |

> ⚠️ STM32CubeProgrammer 本机**未安装**，STM32 烧录用 pyocd（见 board-stm32.md）。

---

## ★ 板卡选择机制（每次开工前第一步）

目标板卡决定：`-b` 参数、`boards/*.overlay` 文件名、烧录 runner、硬件引脚参考。**开工前先判断用户在开发哪块板：**

| 判断依据（优先级从高到低） | 示例 |
|------|------|
| 用户明说板卡/厂商 | "STM32"、"ESP32"、"nucleo"、"NXP"、"esp32s3" |
| 项目 `boards/` 下 overlay 文件名 | `esp32s3_devkitc_esp32s3_procpu.overlay` → ESP32 |
| 项目 `README.md` 板型号 | "板型号: frdm_mcxn947/mcxn947/cpu0" → NXP |
| 已有 `build/` 目录缓存 | `build/zephyr/.config` 中的 `CONFIG_BOARD` |

**无法确定 → 询问用户，不要猜。**

### 三厂商速查表

| 厂商 | 代表板卡 | 构建目标示例 | 默认 runner | 板卡参考 |
|------|----------|--------------|-------------|----------|
| NXP | FRDM-MCXN947（双核 M33） | `frdm_mcxn947/mcxn947/cpu0` | linkserver（板载 MCU-Link） | `references/board-frdm-mcxn947.md` |
| Espressif | ESP32-S3 DevKitC-1（N32R16V） | `esp32s3_devkitc/esp32s3/procpu` | esptool（`--esp-device`） | `references/board-esp32s3-devkitc.md` |
| ST | STM32 全系（nucleo_* / weact_*） | `nucleo_f103rb` 等 | stm32cubeprogrammer / pyocd | `references/board-stm32.md` |

### 构建目标命名规则

Zephyr 目标板名 = 板目录名，多核 SoC 用 `<vendor>/<soc>/<core>` 三段式：

```
west build -b <目标板名> ./<应用>
# 单核板:  -b nucleo_f103rb
# 多核板:  -b frdm_mcxn947/mcxn947/cpu0    （NXP 双核 → 必须选核）
#          -b esp32s3_devkitc/esp32s3/procpu （ESP32-S3 双核 → 通常用 procpu）
# 查板卡:  west boards | grep -iE "mcxn947|esp32s3|stm32|nucleo|weact"
```

overlay 文件名 = 目标板名中的 `/` 换成 `_`：`frdm_mcxn947_mcxn947_cpu0.overlay`、`esp32s3_devkitc_esp32s3_procpu.overlay`、`nucleo_f103rb.overlay`。

---

## 构建与烧录（Linux bash）

每次编译在 bash 中执行，**必须先激活虚拟环境**（否则 `west` 不存在）：

```bash
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b <目标板名> <应用目录>
```

### ★ 关键规则：检测 MCUboot 后必须使用 sysbuild

**如果项目的 `prj.conf` 中包含 `CONFIG_BOOTLOADER_MCUBOOT=y`，则每次编译都必须加 `--sysbuild` 标志。**（三厂商通用）

> **后果**：不加 `--sysbuild` 只编译应用程序而不编译 MCUboot 引导程序。烧录后 Flash 起始处没有引导程序，应用即使烧进 slot0 也无人引导启动。
>
> **一句话：开启 MCUboot 后，永远用 `--sysbuild` 编译。**

### NXP — FRDM-MCXN947（详见 board-frdm-mcxn947.md）

```bash
# 普通编译
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b frdm_mcxn947/mcxn947/cpu0 ./my_app

# MCUboot 多镜像编译（prj.conf 含 CONFIG_BOOTLOADER_MCUBOOT=y 时 ★必须）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b frdm_mcxn947/mcxn947/cpu0 --sysbuild ./my_app

# 烧录（默认 runner = Linkserver，板载 MCU-Link 调试器）
west flash

# ★ 串口监视（已验证 SOP）：控制台在 Flexcomm4，用 by-id 通配符路径 + grabserial
# ⚠️ 注意：grabserial 逐字节 decode("utf8","ignore")，会丢弃所有非 ASCII 字节（中文乱码/消失）
grabserial -d /dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947* -b 115200 -e 5

# ★★ 输出含中文/UTF-8 时必须用技能自带工具 tools/serial_monitor.py（grabserial 会吞掉中文字节）：
#    grabserial 平替：字节透明，参数对齐（-d 支持通配符 / -b 波特率 / -e 秒数退出 / -o 存原始日志）
/home/hero/zephyrproject/.venv/bin/python3 ~/.claude/skills/zephyr-skill/tools/serial_monitor.py \
    -d /dev/serial/by-id/usb-NXP_Semiconductors_MCU-LINK_FRDM-MCXN947* -b 115200 -e 5

# 备选：miniterm 交互式监视（/dev/ttyACM0 或 /dev/ttyUSB0 以 ls 为准）
python -m serial.tools.miniterm /dev/ttyACM0 115200
```

> 注意：MCX-N947 是**双核** SoC；CPU1 不能独立运行，必须由 CPU0 经 sysbuild 启动。
>
> ✅ 2026-08-16 已实测验证：blinky 全流程（build → `west flash` linkserver v26.6.137 → grabserial）一次通过，串口输出 `LED state: ON/OFF` 交替。
> ⚠️ 2026-08-16 排查实录：`LOG_INF` 中文输出"丢失"实为 **grabserial 的 bug**（逐字节 `decode("utf8","ignore")` 丢弃非 ASCII 字节），应用/驱动/UART 全链路无问题；用 pyserial 验证中文完整。
> ⚠️ 已知现象：`west flash`（linkserver runner，reset=False）烧录后 LinkServer 会让应用**连续启动两次**（两次 boot banner，中间夹一个 NUL 字节）——属正常现象，不影响运行；若板子停在 flash driver 自旋（PC 停在 SRAM），用 gdb 加载 ELF 后 `continue` 即可运行应用。

### Espressif — ESP32-S3 DevKitC-1（详见 board-esp32s3-devkitc.md）

```bash
# 普通编译（ESP32-S3 双核 → 通常构建 procpu）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b esp32s3_devkitc/esp32s3/procpu ./my_app

# MCUboot 多镜像编译（★ 开启 MCUboot 后唯一正确的编译方式）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b esp32s3_devkitc/esp32s3/procpu --sysbuild ./my_app

# 烧录（runner = esptool，必须指定串口设备）
west flash --esp-device /dev/ttyUSB0

# 串口监视（espressif 专用监视器）
west espressif monitor -p /dev/ttyUSB0
```

> 注意：板级默认是 8MB Flash 无 PSRAM 的 WROOM-N8 配置；**N32R16V 模组（32MB Flash + 16MB PSRAM）必须加 overlay**（见板卡参考文件）。
> ⚠️ 验证环境别用 blinky（板级无 led0 别名编译不过），用 hello_world；详见 board-esp32s3-devkitc.md。

### STM32 — 通用（详见 board-stm32.md）

```bash
# 普通编译（板名按实际替换，如 nucleo_f103rb / blackpill_f401cc）
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -p always -b nucleo_f103rb ./my_app

# 烧录：默认 runner 为 stm32cubeprogrammer（ST 官方 CLI，本机未安装）
# ★ 本机可用方案: 用 pyocd（已安装，ST-LINK 兼容）
west flash --runner pyocd

# 串口监视（ST-LINK 虚拟串口）
python -m serial.tools.miniterm /dev/ttyACM0 115200
```

### menuconfig 配置（三厂商通用）

```bash
cd /home/hero/zephyrproject && source .venv/bin/activate && west build -b <目标板名> -t menuconfig ./my_app
```

> **menuconfig 用途**：可视化浏览/搜索/修改 Kconfig 选项。退出时选择 `<Yes>` 保存到 `build/zephyr/.config`，后续编译自动使用。

禁止直接调用 gcc/esptool.py/openocd 等底层工具（除非明确要求调试，此时用 `west debug`）。

---

## 工作流程

### 创建项目 — 完整文件结构

```
<项目名>/
├── CMakeLists.txt          # CMake 构建文件
├── prj.conf                # Kconfig 应用配置
├── Kconfig                 # (可选) 应用级 Kconfig 选项
├── sysbuild.conf           # (可选) 多映像/多固件构建（Sysbuild）的配置文件
├── VERSION                 # Zephyr 生命周期管理（含 VERSION_TWEAK，GCC 14+ 强制要求）
├── README.md               # ★ 必须！含板型号、项目目标、编译/接线/运行说明
├── boards/
│   └── <板名>.overlay      # 设备树覆盖文件（目标板名中的 / 换成 _）★关键
├── include/
│   └── xxx_thread.h        # (可选) 应用程序头文件
├── src/
│   └── main.c              # ★ 仅打印板信息+永久休眠，禁止写业务逻辑
│   └── xxx_thread.c        # ★ 一类功能对应一个独立线程 (含详尽中文注释)
└── sysbuild/               # (可选) 二级引导程序配置
    ├── mcuboot.conf        # MCUboot (Bootloader) 的 Kconfig
    └── mcuboot.overlay     # MCUboot (Bootloader) 的设备树覆盖文件
```

### 配置设备树
- 用 `.overlay` 覆盖，**不修改 Zephyr 源码**
- 用 pinctrl 配置引脚复用（节点名查板级 `*-pinctrl.dtsi`）
- 外设节点名/别名查板级 `.dtsi`，不猜引脚
- ★ overlay 中用的节点/别名必须来自目标板实际设备树（三厂商各自查各自的板级文件）

### 编写代码

**★ 核心架构原则（必须遵守）：**
- 使用 Zephyr RTOS API，不用厂商 HAL（不用 ESP-IDF / ST HAL / MCUXpresso SDK）
- 中文注释格式：`/* [初始化/配置/检查/操作/设备树] 说明 */`
- **main.c 只做两件事**：① 打印启动信息（`LOG_INF("Board: %s", CONFIG_BOARD)`）② `k_sleep(K_FOREVER)` 永久休眠
- **所有业务逻辑必须放在独立线程文件中**（如 `led_thread.c`），通过 `K_THREAD_DEFINE` 自动启动
- 一类功能 = 一个线程文件 = 一个 `K_THREAD_DEFINE`

## MCUboot + sysbuild（通用要点）

### ★ Overwrite-Only 升级流程（4 步）

```
① image upload <app>/build/<app>/zephyr/zephyr.signed.bin
   └→ 把新固件写入 slot1，不影响 slot0 正在运行的固件
② image test <hash>
   └→ 把 slot1 标记为 "下次启动尝试运行"（pending 状态）
③ reset
   └→ MCUboot 启动时发现 slot1 是 pending → overwrite: slot1 → slot0 → 从 slot0 运行新固件
④ image confirm
   └→ 新固件运行后确认版本可用（overwrite-only 模式下有时自动处理，手动更安全）
```

### Flash 分区布局（典型）

```
内部 Flash (2MB):                  外部 NOR Flash (FlexSPI):
┌──────────────────┐ 起始地址        ┌──────────────────┐ 起始地址
│ boot_partition   │ 64KB           │ slot1_partition  │ (升级暂存)
├──────────────────┤                │ (image-1)        │
│ slot0_partition  │ (image-0)      └──────────────────┘
└──────────────────┘
```

> **ESP32 差异**：分区由 Espressif 分区文件定义（`<espressif/partitions_*.dtsi>`，板级默认 `partitions_0x0_amp.dtsi`）。
> 用 MCUboot 时在 overlay 中改包含 32M Flash 的分区文件（`<espressif/partitions_0x0_amp_32M.dtsi>`），并同样加 `--sysbuild`。

### MCUboot 项目文件结构

```
<项目名>/
├── sysbuild.conf               # ★ Sysbuild 入口：启用 MCUboot + 密钥路径
├── sysbuild/
│   ├── mcuboot.conf            # MCUboot Kconfig：串口恢复 + 签名
│   └── mcuboot.overlay         # MCUboot 设备树：升级通道 UART + Flash 分区
├── boards/
│   └── <板名>.overlay          # 应用层也需要分区定义 (用于签名)
└── root-rsa-2048.pem           # (可选) 项目专用签名密钥
```

### sysbuild.conf 模板

```ini
SB_CONFIG_BOOTLOADER_MCUBOOT=y
SB_CONFIG_MCUBOOT_MODE_OVERWRITE_ONLY=y
# ★ 项目专用签名密钥（sysbuild 级配置，会写入 MCUboot 子镜像）
SB_CONFIG_BOOT_SIGNATURE_KEY_FILE="<项目>/root-rsa-2048.pem"
```

> **重要**：密钥路径必须用 `SB_CONFIG_` 前缀在 `sysbuild.conf` 中设置，**不能**只在 `mcuboot.conf` 中设置 `CONFIG_BOOT_SIGNATURE_KEY_FILE`。原因：sysbuild 生成 `.config.sysbuild` 时会用 `SB_CONFIG_BOOT_SIGNATURE_KEY_FILE` 的值覆盖 MCUboot 子镜像的配置。

### sysbuild/mcuboot.conf 模板（串口恢复 + 无按键方案）

```ini
# === 串口恢复模式（应急恢复通道） ===
CONFIG_MCUBOOT_SERIAL=y
CONFIG_BOOT_SERIAL_UART=y
CONFIG_UART_CONSOLE=n

# 无有效应用程序时自动进入串口恢复（防砖保护）
CONFIG_BOOT_SERIAL_NO_APPLICATION=y

# 签名算法 RSA-2048
CONFIG_BOOT_SIGNATURE_TYPE_RSA=y
CONFIG_BOOT_SIGNATURE_TYPE_RSA_LEN=2048

# 自动计算扇区数（避免手动值与 AUTO 冲突）
CONFIG_BOOT_MAX_IMG_SECTORS_AUTO=y
```

### sysbuild/mcuboot.overlay 模板（要点）

```dts
/ {
    chosen {
        zephyr,uart-mcumgr = &<升级UART节点>;  /* 升级/恢复通道 */
    };
};

/* 内部 Flash 分区: boot + slot0 */
&flash0 {
    partitions {
        compatible = "fixed-partitions";
        #address-cells = <1>;
        #size-cells = <1>;
        boot_partition: partition@0 {
            label = "mcuboot";
            reg = <0x00000000 0x10000>;
            read-only;
        };
        slot0_partition: partition@10000 {
            label = "image-0";
            reg = <0x00010000 0x...>;
        };
    };
};
```

### 签名密钥

```bash
# 生成 RSA-2048 密钥对
python /home/hero/zephyrproject/bootloader/mcuboot/scripts/imgtool.py keygen -t rsa-2048 -k <项目>/root-rsa-2048.pem

# 依赖: pip install intelhex cbor2 pyyaml cryptography
```

> 开发阶段可使用 MCUboot 自带默认密钥 `bootloader/mcuboot/root-rsa-2048.pem`；生产环境必须使用项目专用密钥。

### 应用层注意事项

1. **★ 应用 overlay 必须包含 `zephyr,code-partition`** — 这是最容易遗漏的配置！
   ```dts
   chosen {
       zephyr,code-partition = &slot0_partition;  /* 告诉链接器跳转到 slot0 */
   };
   ```
   缺少此项会导致 `FLASH_LOAD_OFFSET=0x0`，应用链接到 Flash 起始地址，烧录覆盖 MCUboot → HardFault。
2. **应用 overlay 也必须包含分区定义** — `mcuboot.cmake` 签名步骤需要 `slot0_partition`
3. **prj.conf 无需特殊 Flash 配置** — sysbuild 自动设置 Flash 偏移和签名

### 应用 Shell + mcumgr 配置模板

```ini
# prj.conf - Shell + mcumgr SMP over Shell 配置

# GPIO 驱动
CONFIG_GPIO=y
# 日志
CONFIG_LOG=y

# === Shell 交互式命令行 ===
CONFIG_SHELL=y

# === mcumgr SMP 协议 — 通过 Shell 传输层共用 UART ===
CONFIG_NET_BUF=y         # mcumgr 依赖的网络缓冲区
CONFIG_ZCBOR=y           # mcumgr 依赖的 CBOR 编解码
CONFIG_BASE64=y          # Shell 传输层需要 Base64
CONFIG_CRC=y             # Shell 传输层需要 CRC
CONFIG_MCUMGR=y          # mcumgr 子系统
CONFIG_MCUMGR_TRANSPORT_SHELL=y   # SMP over Shell（与日志无冲突）
CONFIG_MCUMGR_GRP_IMG=y  # 镜像管理（查看/上传固件）
CONFIG_MCUMGR_GRP_OS=y   # OS 管理（复位/回显等）
CONFIG_MCUMGR_GRP_SHELL=y # Shell 管理（远程执行 Shell 命令）
```

> **关键 Kconfig 命名**：mcumgr 管理组使用 `MCUMGR_GRP_XXX`（如 `MCUMGR_GRP_IMG`），不是 `MCUMGR_CMD_XXX`。

### MCUboot 常见编译错误

| 错误 | 原因 | 解决 |
|------|------|------|
| `required nodelabel not found: slot0_partition` | 缺少分区定义 | 在 overlay 中添加 `fixed-partitions` |
| `required nodelabel not found: slot1_partition` | Overwrite-Only 模式也需要 slot1 | 在两处 overlay 中都添加 `slot1_partition`（应用和 MCUboot） |
| `BOOT_MAX_IMG_SECTORS was assigned but got ''` | 手动值与 AUTO 冲突 | 使用 `BOOT_MAX_IMG_SECTORS_AUTO=y` |
| `#error "Serial recovery button must be declared as mcuboot_button0"` | 配置了 GPIO 入口但 overlay 缺少按键别名 | ① 无按键方案：直接禁用 `CONFIG_BOOT_SERIAL_ENTRANCE_GPIO`；② 按键方案：引用板级已有节点 |
| 烧录后 HardFault / 应用覆盖 MCUboot | 缺少 `zephyr,code-partition` → `FLASH_LOAD_OFFSET=0x0` | 应用 overlay 中添加 `zephyr,code-partition = &slot0_partition;` |
| 烧录后应用不启动 | 未签名或签名密钥不匹配 | 确认使用 `.signed.bin` + 密钥一致 |
| MCUgrp Kconfig 警告 `MCUMGR (=n)` | 缺少 `NET_BUF` 或 `ZCBOR` 依赖 | prj.conf 添加 `CONFIG_NET_BUF=y` + `CONFIG_ZCBOR=y` |
| `MCUMGR_CMD_IMG_MGMT` undefined | Kconfig 命名错误 | 改用 `CONFIG_MCUMGR_GRP_IMG=y`（不是 `CMD`） |
| 密钥配置不生效，仍用默认密钥 | mcuboot.conf 被 `.config.sysbuild` 覆盖 | 在 `sysbuild.conf` 中用 `SB_CONFIG_BOOT_SIGNATURE_KEY_FILE` 设置 |

## LVGL 显示配置（通用要点）

- Zephyr 内置 LVGL 模块（本工作区为 v9.x）
- 设备树 chosen 设置 `zephyr,display = &<显示设备>;`
- **★ LVGL 不手动调用 `lvgl_init()`** — `CONFIG_LV_Z_AUTO_INIT=y` 自动初始化，线程中直接 `display_blanking_off()` + 构建 UI
- **★ LVGL v9 主循环用 `lv_timer_handler()`** — 不是 v8 的 `lv_task_handler()`
- 线程入口签名必须是 `void xxx_thread_entry(void *p1, void *p2, void *p3)` — K_THREAD_DEFINE 要求
- RGB565 屏需按驱动要求配置 `CONFIG_LV_COLOR_16_SWAP=y`（ST7789V 类必须，否则颜色错误）
- 用 `lv_label_set_text_fmt` 格式化 `%f` 浮点数时，必须启用 `CONFIG_PICOLIBC_IO_FLOAT=y`（否则输出字面量 "float"）

```c
void display_thread_entry(void *p1, void *p2, void *p3)
{
    k_msleep(500);  /* 等待显示驱动就绪 */

    LOG_INF("Display Thread started");

    if (!device_is_ready(display_dev)) {
        LOG_ERR("Display device not ready");
        return;
    }

    ret = display_blanking_off(display_dev);  /* 开启显示面板 */
    if (ret < 0) { LOG_ERR("Display ON failed: %d", ret); return; }

    /* ... 构建 UI ... */

    while (1) {
        lv_timer_handler();
        k_msleep(30);
    }
}

#define DISPLAY_STACK_SIZE 8192  /* 线程栈大小（单位：字节） */
#define DISPLAY_PRIORITY    10   /* 线程优先级（数字越大优先级越低） */

K_THREAD_DEFINE(display_thread_tid, DISPLAY_STACK_SIZE,
        display_thread_entry, NULL, NULL, NULL,
        DISPLAY_PRIORITY, 0, 0);
```

## 线程间数据传递 — 消息队列 (k_msgq)

★ **推荐方案**: 使用 Zephyr `k_msgq` 消息队列在线程之间传递数据。
**不推荐** mutex + 全局变量方式（增加锁竞争、耦合度高、可测试性差）。

### 架构图

```
传感器/数据线程 (Producer)         显示/消费线程 (Consumer)
  sensor_a_thread → sensor_a_msgq →┐
  sensor_b_thread → sensor_b_msgq →├→ lv_timer (100ms) → UI 更新
                                   ┘
```

### 第 1 步: 定义消息类型（`include/xxx_msgq.h`）

```c
#ifndef XXX_MSGQ_H
#define XXX_MSGQ_H

#include <zephyr/kernel.h>

/** 传感器 A 数据 */
typedef struct {
    float value1;   /* 数据 1 */
    float value2;   /* 数据 2 */
} sensor_a_msg_t;

/* ★ extern 队列声明 — 由各线程 K_MSGQ_DEFINE 定义 */
extern struct k_msgq sensor_a_msgq;
extern struct k_msgq sensor_b_msgq;

#endif
```

### 第 2 步: 生产者线程定义队列 + 发送

```c
#include "xxx_msgq.h"

/* ★ 编译期定义消息队列 (在 K_THREAD_DEFINE 之前) */
K_MSGQ_DEFINE(sensor_a_msgq, sizeof(sensor_a_msg_t), 10, 4);

void sensor_a_thread_entry(void *p1, void *p2, void *p3)
{
    const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(<传感器节点>));
    struct sensor_value raw;
    sensor_a_msg_t msg;

    while (1) {
        sensor_sample_fetch(dev);
        sensor_channel_get(dev, SENSOR_CHAN_AMBIENT_TEMP, &raw);

        /* ★ sensor_value → float 转换 */
        msg.value1 = (float)raw.val1 + (float)raw.val2 / 1000000.0f;

        /* ★ 非阻塞发送 — 队列满时静默丢弃 */
        k_msgq_put(&sensor_a_msgq, &msg, K_NO_WAIT);

        k_msleep(2000);
    }
}

K_THREAD_DEFINE(sensor_a_tid, 1024, sensor_a_thread_entry, NULL, NULL, NULL, 14, 0, 0);
```

### 第 3 步: 消费者线程接收（LVGL timer 回调示例）

```c
#include "xxx_msgq.h"

/* LVGL 定时器回调 — 每 100ms 非阻塞轮询队列 */
static void ui_timer_cb(lv_timer_t *timer)
{
    sensor_a_msg_t data;

    if (k_msgq_get(&sensor_a_msgq, &data, K_NO_WAIT) == 0) {
        lv_label_set_text_fmt(ui_lblvalue, "%.1f", (double)data.value1);
    }
}
```

### 队列深度设计

| 类型 | 采样频率 | 队列深度 | 设计原因 |
|------|----------|----------|----------|
| 慢传感器 | 0.5~2 Hz | 5~10 | 缓冲区充裕，不丢数据 |
| 快传感器 | 10 Hz+ | **1** | ★ "keep-latest" 信箱 — 消费者总是读到最新一帧，不堆积历史 |

### ★ 浮点数 printf 支持 (picolibc)

```ini
# prj.conf — 必须添加
CONFIG_PICOLIBC_IO_FLOAT=y
```

### 对比: 消息队列 vs 全局变量

| 维度 | k_msgq | mutex + 全局变量 |
|------|--------|------------------|
| 线程安全 | ★ 天然安全 (队列内部已加锁) | 手动管理 mutex, 易死锁 |
| 耦合度 | 低 — 生产者/消费者独立 | 高 — 共享同一结构体 |
| 数据缓冲 | ★ 内置队列缓冲 | 无缓冲, 旧数据被覆盖 |
| 背压处理 | 队列满时 `K_NO_WAIT` 静默丢弃 | 无机制 |
| 可测试性 | 各队列独立, 可分别 mock | 强依赖全局状态 |

## 外设快速索引

| 外设 | 参考文件 |
|------|----------|
| GPIO LED/按键 | references/peripheral-examples.md |
| UART 串口 | references/peripheral-examples.md |
| I2C 传感器 | references/peripheral-examples.md |
| SPI | references/peripheral-examples.md |
| PWM (★ 纳秒陷阱) | references/peripheral-examples.md |
| ADC | references/peripheral-examples.md + references/board-esp32s3-devkitc.md |
| ESP32 WiFi/BLE | references/board-esp32s3-devkitc.md |
| ESP32 Touch/WS2812 RGB | references/board-esp32s3-devkitc.md |
| 设备树配置 | references/devicetree-guide.md |
| 项目模板 | references/project-template.md |
| 构建烧录（三厂商） | references/build-and-flash.md |
| NXP FRDM-MCXN947 硬件 | references/board-frdm-mcxn947.md |
| ESP32-S3 DevKitC-1 硬件 | references/board-esp32s3-devkitc.md |
| STM32 通用硬件/烧录 | references/board-stm32.md |
| MCUboot Zephyr 移植 | /home/hero/zephyrproject/bootloader/mcuboot/docs/readme-zephyr.md |
| Sysbuild 文档 | /home/hero/zephyrproject/zephyr/share/sysbuild/sysbuild.rst |
| Shell 文档 | /home/hero/zephyrproject/zephyr/docs/services/shell/index.rst |

## 交互指令

- 新建/创建/模板 → 生成完整文件结构（main.c仅打印 + 独立线程文件 + VERSION含TWEAK + README.md）
- LED/GPIO/按键 → 必须创建独立线程文件（如 led_thread.c），main.c 仅打印信息
- 串口/UART → UART 示例
- I2C/传感器 → I2C 示例
- SPI/LCD → SPI 示例 + LVGL 显示配置
- LVGL/显示/LCD → 参照上方 "LVGL 显示配置" 章节
- 传感器/线程通信 → ★ 消息队列 (k_msgq) 传递, xxx_msgq.h 定义类型, lv_timer 非阻塞接收
- PWM/呼吸灯/电机 → PWM 示例 (★ pwm_set 纳秒陷阱)
- MCUboot/引导程序 → 生成 sysbuild 三件套 (sysbuild.conf + mcuboot.conf + mcuboot.overlay)
- 串口升级/串口恢复 → 启用 CONFIG_MCUBOOT_SERIAL + 指定升级 UART（应用层 mcumgr 触发）
- Shell/命令行 → prj.conf 添加 CONFIG_SHELL=y + 串口后端
- mcumgr/设备管理 → prj.conf 添加 CONFIG_MCUMGR=y + CONFIG_MCUMGR_TRANSPORT_SHELL=y
- 编译/构建/烧录 → 先激活环境，按目标板厂商选命令（见「构建与烧录」+ build-and-flash.md），有 MCUboot 时加 `--sysbuild`
- WiFi/蓝牙/BLE/联网（ESP32） → references/board-esp32s3-devkitc.md 的 WiFi/BLE 章节
- 报错/问题 → 加载排查清单（常见错误见 build-and-flash.md 各厂商表格）
- 板卡/板子型号不确定 → 按「板卡选择机制」判断，无法确定时询问用户

## 强制规则

0. **★ 绝对禁止修改 zephyr/、modules/、tools/、bootloader/ 等官方目录**
   - 所有功能在项目目录内实现（自定义驱动、DTS 绑定、应用代码）
   - 需要不同行为 → 写自定义驱动，不修改 Zephyr 内置驱动
   - 确保可复现、可迁移、不随 Zephyr 升级而损坏
1. 编译必须用 west（禁止直接调用 gcc/esptool.py/openocd）
2. 代码绝对完整
3. 逐行中文注释
4. 设备树优先
5. 应用级配置优先
6. Kconfig 必须 source "Kconfig.zephyr"
7. 无限等待用 k_sleep(K_FOREVER)
8. 项目必须包含 VERSION 文件（含 VERSION_TWEAK 字段，GCC 14+ 强制要求）
9. 编译前检查虚拟环境已激活
10. main() 必须返回 int（GCC 14+ 要求，不允许 void main）
11. ★ main.c 禁止写业务逻辑 — 只打印板信息 + k_sleep(K_FOREVER) 永久休眠
12. ★ 所有外设操作（LED/按键/传感器/串口等）必须拆分到独立线程文件（如 led_thread.c）
13. ★ 一类功能 = 一个线程文件 = 一个 K_THREAD_DEFINE
14. ★ 项目必须包含 README.md（板型号 + 项目目标 + 编译/接线/运行说明）
15. ★ MCUboot 编译必须加 `--sysbuild` — 否则只编译应用，不含引导程序
16. ★ MCUboot overlay 中按键入口必须引用板级已有 GPIO 节点 — 自定义节点不被识别
17. ★ 应用和 MCUboot 两处 overlay 都必须包含 Flash 分区定义 — 两个镜像独立编译
18. ★ `CONFIG_BOOT_MAX_IMG_SECTORS_AUTO=y` 替代手动 `BOOT_MAX_IMG_SECTORS` — 避免 Kconfig 依赖冲突
19. ★ `SB_CONFIG_BOOT_SIGNATURE_KEY_FILE` 必须在 `sysbuild.conf` 中设置 — `mcuboot.conf` 中的值会被 sysbuild 生成的 `.config.sysbuild` 覆盖
20. ★ mcumgr 管理组使用 `CONFIG_MCUMGR_GRP_XXX`（如 `MCUMGR_GRP_IMG`），**不是** `MCUMGR_CMD_XXX`
21. ★ mcumgr 依赖 `CONFIG_NET_BUF=y` + `CONFIG_ZCBOR=y` + `CONFIG_BASE64=y` + `CONFIG_CRC=y`
22. ★ `CONFIG_MCUMGR_TRANSPORT_SHELL=y` 使 mcumgr 与 Shell 共享 UART，无冲突
23. ★ Overwrite-Only 升级流程：`image upload` → `image test <hash>` → `reset` → `image confirm`（4 步，缺一不可）
24. ★ LVGL 不手动调用 `lvgl_init()` — `CONFIG_LV_Z_AUTO_INIT=y` 自动初始化
25. ★ display_thread 栈和优先级 `#define` 必须放在 `K_THREAD_DEFINE` 紧前面
26. ★ 线程入口函数签名必须是 `void xxx_thread_entry(void *p1, void *p2, void *p3)` — K_THREAD_DEFINE 要求
27. ★ LVGL v9 主循环用 `lv_timer_handler()` — 不是 v8 的 `lv_task_handler()`
28. ★ 传感器/线程间数据传递必须使用 k_msgq 消息队列 — 禁止 mutex + 全局变量
29. ★ 每个数据线程用 `K_MSGQ_DEFINE` 定义独立队列 — 深度: 慢数据 5~10, 快数据 1 (keep-latest)
30. ★ 消费线程用 timer 回调（如 `lv_timer_create(cb, 100ms, NULL)`）非阻塞 `k_msgq_get(..., K_NO_WAIT)` 轮询
31. ★ 使用 `lv_label_set_text_fmt` 格式化 `%f` 浮点数时, 必须启用 `CONFIG_PICOLIBC_IO_FLOAT=y`
32. ★ `xxx_msgq.h` 定义消息类型 + extern 队列声明 — 生产者/消费者线程共同 include
33. ★ **开工前先确定目标板卡厂商**（NXP / Espressif / ST）— 从用户描述、overlay 文件名或 README 判定，无法确定就问用户，不猜板卡
34. ★ **烧录命令按厂商不同** — NXP: `west flash`（linkserver）；ESP32: `west flash --esp-device /dev/ttyUSB0`（esptool）；STM32: `west flash --runner pyocd`（本机 stm32cubeprogrammer 未安装）
35. ★ **ESP32（N32R16V 模组）必须加 overlay 包含 `esp32s3_wroom_n32r16.dtsi`** — 否则按默认 8MB Flash 无 PSRAM 配置编译，Flash 分区越界
36. ★ **ESP32 禁止使用 GPIO35/36/37** — Octal SPI Flash/PSRAM 内部占用，外部使用会导致崩溃
37. ★ **overlay 节点必须来自目标板实际设备树** — NXP 查 `boards/nxp/<板>`、ESP32 查 `boards/espressif/<板>`、ST 查 `boards/st/<板>` 的 .dtsi/.pinctrl.dtsi
38. ★ **不用厂商 HAL 原生 API** — 用 Zephyr 驱动 API（GPIO/UART/I2C/SPI/PWM/ADC/WiFi/BT），移植性最强
