---
adr_id: "0001"
title: "Choose Rust as the transpiler's implementation host"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language"]
affected_docs: ["TECH_STACK.md", "BOOTSTRAP_PLAN.md"]
---

# Choose Rust as the transpiler's implementation host

For the fern transpiler we need a host language with strong pattern-matching,
fast parsing, and a single-binary distribution story so contributors can run
the compiler without a JS toolchain. We considered TypeScript (closest to the
emit target, but slower large-file parsing and runtime dependency on Node) and
OCaml (excellent AST ergonomics, smaller ecosystem). Rust wins on tooling,
performance for cold-start CLI runs, and predictable cross-platform builds.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
