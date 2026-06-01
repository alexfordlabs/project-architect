---
template_name: EMBEDDED_SPECIFIC
generate_when: "decisions.project.type == 'embedded'"
required_decisions: [embedded.mcu_class, embedded.language]
optional_decisions: [embedded.rtos, embedded.connectivity, embedded.ota, embedded.power_budget]
depends_on: []
revision_triggers: [embedded.mcu_class, embedded.language, embedded.rtos, embedded.connectivity]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Embedded Specific: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [MCU / SoC Choice](#mcu-soc-choice)
- [RTOS (or bare-metal)](#rtos-or-bare-metal)
- [Programming Language](#programming-language)
- [Power Budget](#power-budget)
- [Connectivity (BLE / Wi-Fi / LoRa / cellular)](#connectivity-ble-wi-fi-lora-cellular)
- [🚀 OTA Update Mechanism](#ota-update-mechanism)
- [🔧 Tooling (PlatformIO / esp-idf / Zephyr)](#tooling-platformio-esp-idf-zephyr)
- [Bootloader & Recovery](#bootloader-recovery)
- [↻ Revision Log](#revision-log)

## MCU / SoC Choice
Microcontroller / SoC family (ESP32, STM32, nRF52/nRF53, RP2040, RISC-V, i.MX RT), variant, peripherals needed, and second-source availability for supply-chain risk.

## RTOS (or bare-metal)
RTOS selection (FreeRTOS, Zephyr, NuttX, ThreadX, RIOT) or bare-metal super-loop, scheduling strategy, and inter-task communication primitives.

## Programming Language
Primary language (C, C++17/20, Rust embedded, MicroPython, TinyGo) with rationale around toolchain maturity, memory safety, and ecosystem.

## Power Budget
Active / sleep / deep-sleep current targets, average duty cycle, battery chemistry & capacity, expected runtime, and wake-source design.

## Connectivity (BLE / Wi-Fi / LoRa / cellular)
Radio stack(s) — BLE (Nordic SoftDevice, Zephyr Bluetooth, ESP-IDF), Wi-Fi, Thread/Matter, LoRaWAN, NB-IoT/LTE-M — provisioning UX, and pairing model.

## 🚀 OTA Update Mechanism
OTA strategy (HTTPS over Wi-Fi, BLE DFU, MCUboot dual-bank, A/B partitions), signing, rollback on boot failure, and delta updates if size-constrained.

## 🔧 Tooling (PlatformIO / esp-idf / Zephyr)
Build system (PlatformIO, ESP-IDF, Zephyr west, STM32CubeIDE, Make/CMake), debugger (J-Link, ST-Link, OpenOCD), and CI strategy for firmware artifacts.

## Bootloader & Recovery
Bootloader choice (MCUboot, native ROM bootloader, custom), recovery mode entry, brick-prevention strategy, and secure boot chain.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
