---
adr_id: "0001"
title: "Choose Rust as host language"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language"]
affected_docs: ["TECH_STACK.md", "BOOTSTRAP_PLAN.md"]
---

# Choose Rust as host language

For the lume tree-walking interpreter we need a host language with strong
pattern-matching, ergonomic enums (for AST nodes), and a mature crate ecosystem
for parsing and CLI. We considered OCaml (best AST ergonomics but smaller
ecosystem) and Haskell (excellent type machinery, but steeper teaching curve
for contributors). Rust wins on tooling, distribution as a single binary, and
classroom accessibility.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
