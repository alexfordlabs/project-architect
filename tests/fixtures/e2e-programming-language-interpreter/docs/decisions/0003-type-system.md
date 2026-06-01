---
adr_id: "0003"
title: "Dynamic type system, multi-paradigm"
status: accepted
date: 2026-05-13
decision_keys: ["type_system", "paradigm"]
affected_docs: ["TYPE_SYSTEM.md", "SEMANTICS.md"]
---

# Dynamic type system, multi-paradigm

lume is a teaching language; a dynamic type system lowers the barrier for
first-week exercises and keeps the interpreter loop small. We allow both
imperative and functional styles (multi-paradigm) so courses can introduce
recursion, closures, and mutation at their own pace. A gradual/static layer
can be added in a later RFC without breaking the v0.1 surface.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
