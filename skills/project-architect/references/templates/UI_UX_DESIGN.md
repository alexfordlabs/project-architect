---
template_name: UI_UX_DESIGN
generate_when: "decisions.frontend.framework != null"
required_decisions: [frontend.framework, frontend.styling]
optional_decisions: [frontend.component_library, frontend.state, frontend.data_fetching, frontend.routing, frontend.rendering, frontend.i18n, a11y.target]
depends_on: []
revision_triggers: [frontend.framework, frontend.styling, frontend.component_library, frontend.state, frontend.rendering]
---

<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# UI/UX Design: {{project_name}}

> 📌 **Status:** v{{document_version}} · **Last revised:** {{last_revised_date}} · **ADRs:** {{adr_links}}

## Table of contents
- [🏗️ Design System](#design-system)
- [🎨 Layout & Navigation](#layout-navigation)
- [🎨 Key Pages/Screens](#key-pagesscreens)
- [🎨 Theme & Styling](#theme-styling)
- [State Management](#state-management)
- [🎨 Rendering Strategy](#rendering-strategy)
- [Accessibility](#accessibility)
- [Internationalization](#internationalization)
- [📊 Performance Targets](#performance-targets)
- [↻ Revision Log](#revision-log)

## 🏗️ Design System
Component library (shadcn/ui, Radix, MUI, custom) and tokens source (Figma file, Tailwind config, design-tokens JSON). One-line rationale + ADR link.

## 🎨 Layout & Navigation
Primary navigation pattern (top bar / sidebar / tab bar / nested), route map at a glance, and responsive-breakpoint strategy.

## 🎨 Key Pages/Screens
One subsection per major page/screen. Each subsection captures: purpose, primary user goal, key components, data dependencies, and edge/empty/loading states.

## 🎨 Theme & Styling
Color palette (semantic tokens), typography scale, dark-mode strategy, spacing scale, and shadow/elevation system.

## State Management
Library or pattern (Zustand / Redux Toolkit / Jotai / context / signals), server-state strategy (TanStack Query / SWR / RSC), and form-state strategy.

## 🎨 Rendering Strategy
SSR / SSG / ISR / RSC / client-only mix and which routes use which mode. Streaming and suspense usage.

## Accessibility
WCAG target level, keyboard-navigation expectations, screen-reader priorities, and color-contrast targets. Defer detail to ACCESSIBILITY.md when generated.

## Internationalization
Locales supported, i18n library, RTL strategy. Skip this section if single-locale. Defer detail to INTERNATIONALIZATION.md when generated.

## 📊 Performance Targets
Core Web Vitals targets (LCP, INP, CLS), JS bundle budget, and image strategy. Link to PERFORMANCE_BUDGETS.md if generated.

## ↻ Revision Log

| Date | Decision key | Change | ADR |
|---|---|---|---|
| _(none yet)_ |  |  |  |

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
