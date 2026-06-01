---
template_name: HARDWARE_FIRMWARE
generate_when: "decisions.project.type == 'embedded' AND decisions.hardware.combo == true"
required_decisions: [hardware.pcb_design, hardware.manufacturing]
optional_decisions: [hardware.certifications, hardware.enclosure, hardware.sourcing]
depends_on: [EMBEDDED_SPECIFIC]
revision_triggers: [hardware.pcb_design, hardware.manufacturing, hardware.certifications]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Hardware & Firmware: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🎯 Hardware Overview (block diagram)](#hardware-overview-block-diagram)
- [PCB Design Strategy](#pcb-design-strategy)
- [BoM Strategy](#bom-strategy)
- [Manufacturing Partner](#manufacturing-partner)
- [Certifications (FCC / CE / UL / RoHS)](#certifications-fcc-ce-ul-rohs)
- [Enclosure & Mechanical](#enclosure-mechanical)
- [Component Sourcing Risk](#component-sourcing-risk)
- [Firmware ↔ Hardware Interface Contracts](#firmware-hardware-interface-contracts)
- [↻ Revision Log](#revision-log)

## 🎯 Hardware Overview (block diagram)
High-level block diagram of the device — MCU, sensors, radios, power tree, I/O — with a short walkthrough explaining data and power flow.

## PCB Design Strategy
PCB design tooling (KiCad, Altium, EasyEDA), layer count, design-for-EMI/EMC choices, design-for-manufacture (DFM) and design-for-test (DFT) considerations.

## BoM Strategy
Bill-of-materials approach: preferred suppliers, second-source components, lifecycle-status checks (Octopart, Z2Data), cost target per unit, and BoM management tooling.

## Manufacturing Partner
Contract manufacturer / EMS selection (JLCPCB, PCBWay, MacroFab, regional CM), PCBA volumes, panelization, and quality criteria (AOI, ICT, functional test).

## Certifications (FCC / CE / UL / RoHS)
Required certifications per target market (FCC Part 15, CE / RED, UL, IC, MIC, KC, ANATEL, RoHS, REACH), pre-compliance testing plan, and lab partners.

## Enclosure & Mechanical
Enclosure approach (off-the-shelf, custom injection-molded, 3D-printed), IP rating, drop / shock targets, tolerances, and CAD tooling.

## Component Sourcing Risk
Supply-chain risk profile per critical part, lead times, allocation status, alternates qualified, and inventory buffer policy.

## Firmware ↔ Hardware Interface Contracts
Hardware-firmware contract: pin assignments, register maps, version-detect strategy (hardware revision pins), and how firmware adapts to multiple hardware revisions.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
