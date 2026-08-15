# Zephyr 外设代码示例（通用）

> 所有示例基于设备树，不硬编码引脚号。注释格式：`/* [类型] 说明 */`

---

## 1. GPIO — LED 控制

### 单线程 LED 闪烁

```c
/*
 * [LED 闪烁] 控制板载 LED 周期性闪烁
 *
 * 硬件：板载 LED（如 FRDM-MCXN947 的 green_led）
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(led_blink, LOG_LEVEL_INF);

/* [设备树] 通过节点标签获取 LED */
static const struct gpio_dt_spec led =
	GPIO_DT_SPEC_GET(DT_NODELABEL(green_led), gpios);

#define SLEEP_TIME_MS 1000

int main(void)
{
	if (!gpio_is_ready_dt(&led)) {
		LOG_ERR("LED GPIO 未就绪");
		return -ENODEV;
	}

	/* [配置] 输出模式，初始灭 */
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	LOG_INF("LED 初始化完成");

	while (1) {
		/* [操作] 翻转 LED */
		gpio_pin_toggle_dt(&led);
		k_msleep(SLEEP_TIME_MS);
	}
	return 0;
}
```

### 多线程 LED 控制（★ 推荐架构：独立线程文件）

```c
/*
 * [LED 线程] 板载 LED 闪烁线程
 *
 * 架构: 线程入口仅等待驱动就绪后永久休眠, 闪烁逻辑由线程内定时器驱动
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(led_thread, LOG_LEVEL_INF);

/* [设备树] 板载 LED */
static const struct gpio_dt_spec led =
	GPIO_DT_SPEC_GET(DT_NODELABEL(green_led), gpios);

void led_thread_entry(void *p1, void *p2, void *p3)
{
	k_msleep(2000);  /* [等待] 等待其他外设初始化完成 */

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

/* [线程配置] 栈大小和优先级 */
#define LED_STACK_SIZE 1024
#define LED_PRIORITY    14

K_THREAD_DEFINE(led_tid, LED_STACK_SIZE,
		led_thread_entry, NULL, NULL, NULL,
		LED_PRIORITY, 0, 0);
```

---

## 2. 按键输入

```c
/*
 * [按键线程] 用户按键检测（轮询模式，无需中断）
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(key_thread, LOG_LEVEL_INF);

/* [设备树] 用户按键 */
static const struct gpio_dt_spec key =
	GPIO_DT_SPEC_GET(DT_NODELABEL(user_button_2), gpios);

void key_thread_entry(void *p1, void *p2, void *p3)
{
	int prev, cur;

	if (!gpio_is_ready_dt(&key)) {
		LOG_ERR("按键 GPIO 未就绪");
		return;
	}

	/* [配置] 输入模式 */
	gpio_pin_configure_dt(&key, GPIO_INPUT);
	prev = gpio_pin_get_dt(&key);
	LOG_INF("[KEY] 线程启动");

	while (1) {
		cur = gpio_pin_get_dt(&key);
		/* [检查] 下降沿检测（按下） */
		if (prev == 1 && cur == 0) {
			LOG_INF("按键按下");
		}
		prev = cur;
		k_msleep(20);  /* 消抖 */
	}
}

#define KEY_STACK_SIZE 1024
#define KEY_PRIORITY    14

K_THREAD_DEFINE(key_tid, KEY_STACK_SIZE,
		key_thread_entry, NULL, NULL, NULL,
		KEY_PRIORITY, 0, 0);
```

---

## 3. UART 串口

```c
/*
 * [UART 线程] 从 UART 读取数据（异步回调模式）
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(uart_thread, LOG_LEVEL_INF);

/* [设备树] 串口设备（节点名查板级 dtsi） */
static const struct device *const uart_dev =
	DEVICE_DT_GET(DT_NODELABEL(flexcomm1));

static uint8_t rx_buf[64];
static volatile bool uart_ready;

/* [回调] UART 接收回调（中断上下文，只做标志位/环形缓冲） */
static void uart_rx_cb(const struct device *dev, int evt, void *user_data)
{
	switch (evt) {
	case UART_RX_RDY:
		uart_ready = true;
		break;
	case UART_RX_DISABLED:
		break;
	default:
		break;
	}
}

void uart_thread_entry(void *p1, void *p2, void *p3)
{
	int ret;

	if (!device_is_ready(uart_dev)) {
		LOG_ERR("UART 未就绪");
		return;
	}

	/* [配置] 接收回调并开启接收 */
	uart_irq_callback_user_data_set(uart_dev, uart_rx_cb, NULL);
	ret = uart_rx_enable(uart_dev, rx_buf, sizeof(rx_buf), 100);
	if (ret < 0) {
		LOG_ERR("UART RX 使能失败: %d", ret);
		return;
	}
	LOG_INF("[UART] 线程启动");

	while (1) {
		if (uart_ready) {
			/* 处理接收数据... */
			uart_ready = false;
		}
		k_msleep(10);
	}
}

#define UART_STACK_SIZE 2048
#define UART_PRIORITY    14

K_THREAD_DEFINE(uart_tid, UART_STACK_SIZE,
		uart_thread_entry, NULL, NULL, NULL,
		UART_PRIORITY, 0, 0);
```

---

## 4. I2C 传感器扫描

```c
/*
 * [I2C 扫描] 扫描总线上所有设备地址
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(i2c_scan, LOG_LEVEL_INF);

/* [设备树] I2C 控制器 */
static const struct device *const i2c_dev =
	DEVICE_DT_GET(DT_NODELABEL(flexcomm0));

int main(void)
{
	uint8_t addr;

	if (!device_is_ready(i2c_dev)) {
		LOG_ERR("I2C 未就绪");
		return -ENODEV;
	}

	LOG_INF("扫描 I2C 总线...");

	for (addr = 0x08; addr <= 0x77; addr++) {
		struct i2c_msg msg = {
			.buf = &addr,
			.len = 1,
			.flags = I2C_MSG_WRITE | I2C_MSG_STOP,
		};

		/* [操作] 探测地址是否有 ACK */
		if (i2c_transfer(i2c_dev, &msg, 1, addr) == 0) {
			LOG_INF("发现设备: 0x%02X", addr);
		}
	}
	return 0;
}
```

---

## 5. PWM 呼吸灯

```c
/*
 * [PWM 线程] LED 呼吸灯效果
 *
 * ★ pwm_set 的 period/pulse 单位是纳秒 (ns)
 */

#include <zephyr/kernel.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(pwm_led, LOG_LEVEL_INF);

/* [设备树] PWM 设备（节点名查板级 dtsi） */
static const struct pwm_dt_spec pwm_led =
	PWM_DT_SPEC_GET(DT_NODELABEL(flexpwm1_pwm0));

#define PWM_PERIOD_NS  1000000   /* 1ms = 1KHz */
#define STEPS          100       /* 呼吸渐变步数 */

void pwm_thread_entry(void *p1, void *p2, void *p3)
{
	int i;

	if (!device_is_ready(pwm_led.dev)) {
		LOG_ERR("PWM 未就绪");
		return;
	}

	LOG_INF("[PWM] 线程启动");

	while (1) {
		/* [操作] 渐亮 */
		for (i = 0; i <= STEPS; i++) {
			pwm_set_pulse_dt(&pwm_led, (PWM_PERIOD_NS * i) / STEPS);
			k_msleep(10);
		}
		/* [操作] 渐灭 */
		for (i = STEPS; i >= 0; i--) {
			pwm_set_pulse_dt(&pwm_led, (PWM_PERIOD_NS * i) / STEPS);
			k_msleep(10);
		}
	}
}

#define PWM_STACK_SIZE 1024
#define PWM_PRIORITY    14

K_THREAD_DEFINE(pwm_tid, PWM_STACK_SIZE,
		pwm_thread_entry, NULL, NULL, NULL,
		PWM_PRIORITY, 0, 0);
```

> ★ **pwm_set 关键陷阱**：`pwm_set(dev, channel, period, pulse, flags)` 的 `period` 和 `pulse` 单位是**纳秒**。
> 错误：`pwm_set(dev, 0, 100, 50, 0)` → 100ns → period_cycles=0 → 通道被禁用（什么都不输出）。
> 正确：`pwm_set(dev, 0, 100000, 50000, 0)` → 100μs 周期 50% 占空比。
> 通道号：MCX 等厂商驱动通常从 0 开始（STM32 是 1-based），以驱动源码为准。

---

## 6. LVGL 图形库 + LCD（通用）

### LVGL 常见坑

| 坑 | 说明 |
|----|------|
| ★ 不要手动调 `lvgl_init()` | `CONFIG_LV_Z_AUTO_INIT=y` 自动初始化（默认开启） |
| ★ v9 主循环用 `lv_timer_handler()` | v8 的 `lv_task_handler()` 已删除 |
| ★ RGB565 屏需 `CONFIG_LV_COLOR_16_SWAP=y` | 按驱动要求开启（ST7789V 类必须） |
| ★ `%f` 浮点输出 | 必须 `CONFIG_PICOLIBC_IO_FLOAT=y`，否则输出字面量 "float" |
| 线程入口签名 | 必须 `void xxx_entry(void *p1, void *p2, void *p3)` |
| 所有 LVGL API 同线程 | 单线程驱动，无需加锁 |

### prj.conf (LCD+LVGL 最小)

```ini
# === 显示子系统 ===
CONFIG_DISPLAY=y
CONFIG_SPI=y

# === LVGL 图形库 ===
CONFIG_LVGL=y
CONFIG_LV_COLOR_DEPTH_16=y        # RGB565
CONFIG_LV_Z_BITS_PER_PIXEL=16

# === 内存优化 ===
CONFIG_LV_Z_MEM_POOL_SIZE=16384   # 16KB 内存池（按 RAM 大小调整）

# === 字体（按实际使用启用） ===
CONFIG_LV_FONT_MONTSERRAT_14=y
CONFIG_LV_FONT_MONTSERRAT_24=y
```

### display_thread.c 模板（auto-init 模式）

```c
/* [LVGL] 显示线程 — LVGL 通过 CONFIG_LV_Z_AUTO_INIT=y 自动初始化，本线程不调用 lvgl_init() */

#include <zephyr/kernel.h>
#include <zephyr/drivers/display.h>
#include <zephyr/logging/log.h>
#include <lvgl.h>

LOG_MODULE_REGISTER(display_thread, LOG_LEVEL_INF);

/* [设备树] 显示设备（chosen: zephyr,display） */
static const struct device *display_dev = DEVICE_DT_GET(DT_CHOSEN(zephyr_display));

void display_thread_entry(void *p1, void *p2, void *p3)
{
	int ret;

	k_msleep(500);  /* [等待] 等待显示驱动就绪 */

	if (!device_is_ready(display_dev)) {
		LOG_ERR("Display device not ready");
		return;
	}

	/* [操作] 开启显示面板 */
	ret = display_blanking_off(display_dev);
	if (ret < 0) {
		LOG_ERR("Display ON failed: %d", ret);
		return;
	}
	LOG_INF("[Display] 线程启动");

	/* [UI] 构建界面 */
	lv_obj_t *label = lv_label_create(lv_scr_act());
	lv_label_set_text(label, "Hello Zephyr!");

	/* [主循环] LVGL v9 必须用 lv_timer_handler() */
	while (1) {
		lv_timer_handler();
		k_msleep(30);
	}
}

#define DISPLAY_STACK_SIZE 8192
#define DISPLAY_PRIORITY    10

K_THREAD_DEFINE(display_thread_tid, DISPLAY_STACK_SIZE,
		display_thread_entry, NULL, NULL, NULL,
		DISPLAY_PRIORITY, 0, 0);
```

---

## 外设依赖配置速查

| 外设 | prj.conf 配置 | 说明 |
|------|--------------|------|
| GPIO | `CONFIG_GPIO=y` | 基础 |
| UART | `CONFIG_UART_INTERRUPT_DRIVEN=y`（异步时） | 控制台 UART 默认已启用 |
| I2C | `CONFIG_I2C=y` | 传感器等 |
| SPI | `CONFIG_SPI=y` | LCD/Flash 等 |
| PWM | `CONFIG_PWM=y` | 呼吸灯/电机 |
| ADC | `CONFIG_ADC=y` | 模拟量采集 |
| 传感器 | `CONFIG_SENSOR=y` | sensor API |
| LED | `CONFIG_LED=y` + `CONFIG_LED_GPIO=y` | LED API |
| Shell | `CONFIG_SHELL=y` | 交互命令行 |
| Logging | `CONFIG_LOG=y` | 日志子系统 |
| LVGL | `CONFIG_LVGL=y` | 图形库 |

> 厂商驱动由设备树自动启用（`DT_HAS_<厂商>_<外设>_ENABLED`），一般无需手动开。
