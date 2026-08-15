# Zephyr 设备树配置指南

> 适用于本机 Zephyr 4.4.2 + NXP MCX 系列（FRDM-MCXN947）等通用板卡

---

## 核心原则

1. **始终使用 `.overlay` 覆盖**，不改 Zephyr 源码中的板级文件
2. **使用设备树宏** 获取硬件配置，不硬编码引脚号
3. **使用 pinctrl 子系统** 配置引脚复用功能
4. **板卡硬件信息以板级 `.dtsi` 为准** — 不自行猜测引脚

---

## pinctrl 命名规则

各厂商命名规则不同，**以板级 pinctrl 文件为准**：

- NXP MCX 系列：`<外设>_<信号>_<PIO端口引脚>`，定义在板卡 `*-pinctrl.dtsi` 中
  - 例：`flexcomm4_uart` 控制台 UART，`pinmux = <FC4_P0_PIO1_8>`（P1_8 RX）
- STM32 系列：`<外设>_<信号>_<端口><引脚>`，如 `usart1_tx_pa9`

> ★ 查找方法：`grep -r "pinctrl" <板卡目录>/*-pinctrl.dtsi`，或用 `west build` 后查看预处理生成的 `build/zephyr/zephyr.dts`。

---

## GPIO — LED 与按键

### LED（输出）

板级 DTS 已定义 LED 节点（如 FRDM-MCXN947 的 `green_led`、`red_led`），overlay 只需添加别名：

```dts
/ {
	aliases {
		led0 = &green_led;  /* 绿色 LED */
		led1 = &red_led;    /* 红色 LED */
	};
};
```

> 电平极性（共阳极/共阴极）由 DTS 中的 GPIO flags 定义，代码用 GPIO API 统一处理，无需关心物理极性。

### 按键（输入）

```dts
/ {
	aliases {
		sw0 = &user_button_2;  /* 用户按键 */
	};
};
```

---

## UART — 串口

```dts
/* [UART] 启用控制台 UART 之外的另一路 Flexcomm（节点名查板级 dtsi） */
&flexcomm1 {
	status = "okay";
	pinctrl-0 = <&flexcomm1_uart_pio1_0 &flexcomm1_uart_pio1_1>;  /* 实际节点名查板级 -pinctrl.dtsi */
	pinctrl-names = "default";
	current-speed = <115200>;
};
```

---

## I2C — 总线通信

```dts
/* [I2C] 启用 I2C 控制器（节点名查板级 dtsi，MCX 用 flexcommN） */
&flexcomm0 {
	compatible = "nxp,mcux-flexcomm-i2c";  /* 以板级 dtsi 为准 */
	status = "okay";
	pinctrl-0 = <&flexcomm0_i2c_pio0_0 &flexcomm0_i2c_pio0_1>;
	pinctrl-names = "default";

	/* 挂载的 I2C 传感器 */
	sensor: sensor@48 {
		compatible = "aosong,aht20";
		reg = <0x48>;
	};
};
```

> ⚠️ 多条 I2C 总线如果引脚冲突（SDA 重叠），必须确认板级 dtsi 的引脚分配，避免外设共用冲突。

---

## PWM — 脉宽调制

```dts
/* [PWM] FlexPWM（MCX 系列）或定时器 PWM */
&flexpwm1 {
	status = "okay";
	pinctrl-0 = <&flexpwm1_pwm0_pio1_2>;
	pinctrl-names = "default";
};
```

> ★ `pwm_set(dev, channel, period, pulse, flags)` 的 **period 和 pulse 单位是纳秒 (ns)**，不是微秒！
> `pwm_set(dev, ch, 100, 50, 0)` 中 100 被当作 100ns → period_cycles=0 → 通道被禁用（什么都不输出）。
> 正确写法：`#define PWM_PERIOD_NS 100000  /* 10KHz = 100μs */`，pulse 也用 ns。

---

## ADC — 模数转换

```dts
/* [ADC] 使能 ADC 通道 */
&adc0 {
	status = "okay";
	pinctrl-0 = <&adc0_in0_pio1_4>;
	pinctrl-names = "default";
	#address-cells = <1>;
	#size-cells = <0>;
	channel@0 {
		reg = <0>;  /* 通道 0 */
		zephyr,channel-type = "SINGLE_ENDED";
		zephyr,input-positive = <0>;
	};
};
```

---

## 代码中使用设备树

### 方式一：gpio_dt_spec（推荐）

```c
/* [设备树] 通过节点标签获取 GPIO */
static const struct gpio_dt_spec led =
	GPIO_DT_SPEC_GET(DT_NODELABEL(green_led), gpios);

if (gpio_is_ready_dt(&led)) {
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_toggle_dt(&led);
}
```

### 方式二：DT_ALIAS（通过别名）

```c
/* [设备树] 通过别名获取，板级/overlay 定义 aliases { led0 = &green_led; } */
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
```

### 方式三：DEVICE_DT_GET（获取设备指针）

```c
/* [设备树] 直接获取设备驱动指针 */
const struct device *dev = DEVICE_DT_GET(DT_NODELABEL(flexcomm4));
```

---

## 调试设备树

```bash
# 查看最终生成的设备树（最可靠的调试手段）
grep -A20 "chosen" build/zephyr/zephyr.dts

# 检查外设是否被实例化（在 C 代码中的宏）
grep "DT_N" build/zephyr/include/generated/zephyr/devicetree_generated.h | grep -i flexcomm

# 查看 Kconfig 自动启用的驱动
grep -E "DT_HAS_.*ENABLED" build/zephyr/.config | head
```

> 外设 `status = "okay"` 且驱动存在时，Kconfig 中对应 `DT_HAS_<厂商>_<外设>_ENABLED=y` 会自动置位，驱动自动编译。
