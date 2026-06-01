---
template_name: ACCESSIBILITY
generate_when: "decisions.frontend.framework != null AND decisions.a11y.target != null"
required_decisions:
  - a11y.target
optional_decisions:
  - a11y.audit_tooling
  - a11y.screen_reader_priorities
depends_on:
  - UI_UX_DESIGN
revision_triggers:
  - a11y.target
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Accessibility: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [WCAG Target Level](#wcag-target-level)
- [Keyboard Navigation](#keyboard-navigation)
- [Screen Reader Support](#screen-reader-support)
- [Color & Contrast](#color-contrast)
- [Focus Management](#focus-management)
- [ARIA Patterns Used](#aria-patterns-used)
- [🔧 Audit Tooling](#audit-tooling)
- [↻ Revision Log](#revision-log)

## WCAG Target Level
Target conformance (e.g., WCAG 2.2 AA), exemptions or known gaps with timelines, regulatory drivers (ADA, EAA 2025, Section 508, AODA).

## Keyboard Navigation
Tab-order rules, focus trap behavior for modals/menus, skip links, custom-widget keyboard contracts (e.g., listbox arrow keys), no keyboard traps guarantee.

## Screen Reader Support
Targeted screen readers (NVDA + Firefox/Chrome, JAWS + Chrome, VoiceOver iOS/macOS, TalkBack Android), live-region usage policy, announcement budget.

## Color & Contrast
Minimum contrast ratios (4.5:1 normal, 3:1 large), focus-indicator contrast (3:1), non-color-only state indicators, dark-mode token mirroring.

## Focus Management
Initial focus on route changes, focus restoration on modal close, async-content focus handling, programmatic focus rules, `:focus-visible` styling.

## ARIA Patterns Used
Inventory of WAI-ARIA Authoring Practices patterns adopted (combobox, dialog, tabs, tree, menu, etc.) and the headless library backing each (Radix, React Aria, Reach, native).

## 🔧 Audit Tooling
Automated (axe-core in unit/E2E, Lighthouse CI, Pa11y, Storybook a11y addon) plus manual cadence (screen reader passes, keyboard-only walkthroughs, third-party audit schedule).

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
