---
adr_id: "0002"
title: "Tree-walking interpreter for v0.1"
status: accepted
date: 2026-05-13
decision_keys: ["impl_strategy"]
affected_docs: ["BOOTSTRAP_PLAN.md"]
---

# Tree-walking interpreter for v0.1

For an educational language, a tree-walking interpreter keeps the code path
between source and behaviour short and readable. We deferred bytecode VM and
JIT until after v0.1 ships and the language semantics stabilise. Tree-walking
also makes step-debugging trivial for student exercises.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
