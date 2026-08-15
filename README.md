# zephyr-skills

Zephyr RTOS 开发技能包(Claude Code skill),用于本机 NXP / ESP32 / STM32 多厂商嵌入式开发。

## 内容

- `SKILL.md` — 技能主文件:涵盖 west 工作流、Kconfig、devicetree、构建/烧录/调试
- `references/` — 参考资料:
  - `board-esp32s3-devkitc.md` — ESP32-S3 开发板
  - `board-frdm-mcxn947.md` — NXP FRDM-MCXN947 开发板
  - `board-stm32.md` — STM32 系列(blackpill、weact 等)
  - `build-and-flash.md` — 构建与烧录指南
  - `devicetree-guide.md` — devicetree 快速指南
  - `peripheral-examples.md` — GPIO/UART/I2C/SPI/PWM/ADC/LVGL/WiFi/BLE 外设示例
  - `project-template.md` — 项目模板

## 安装

将 `SKILL.md` 与 `references/` 放入 Claude Code 的 skills 目录:

```bash
mkdir -p ~/.claude/skills/zephyr-skill
cp SKILL.md references/ -r ~/.claude/skills/zephyr-skill/
```
