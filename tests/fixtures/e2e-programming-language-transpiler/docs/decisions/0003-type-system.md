---
adr_id: "0003"
title: "Static gradual type system with row polymorphism"
status: accepted
date: 2026-05-13
decision_keys: ["type_system", "paradigm"]
affected_docs: ["TYPE_SYSTEM.md", "SEMANTICS.md"]
---

# Static gradual type system with row polymorphism

fern is purely functional: every program is a pipeline of pure value
transformations producing a declarative UI tree. The type system is static
gradual — fully-typed code gets inference + soundness checks, while untyped
fragments are bridged with explicit `dynamic` boundaries. Row polymorphism on
record types lets components compose over open prop sets without surface
ceremony. This matches the functional paradigm choice and keeps the
JS-emit step purely type-erasing.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
