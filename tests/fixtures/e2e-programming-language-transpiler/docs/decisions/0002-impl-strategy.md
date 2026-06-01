---
adr_id: "0002"
title: "Transpile to ES2026 JavaScript"
status: accepted
date: 2026-05-13
decision_keys: ["impl_strategy", "host_runtime"]
affected_docs: ["BOOTSTRAP_PLAN.md"]
---

# Transpile to ES2026 JavaScript

fern is a UI-definition DSL whose programs must run inside existing JavaScript
host environments (browsers, Node, Bun). A transpiler emitting modern ES2026
JavaScript lets us reuse the host's runtime, GC, and module system instead of
shipping a bytecode VM. We deferred a WASM backend until after v0.1 stabilises
the surface syntax. js_host runtime is fixed for v0.1.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
