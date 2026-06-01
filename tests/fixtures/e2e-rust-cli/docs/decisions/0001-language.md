---
adr_id: "0001"
title: "Choose Rust as primary language"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language"]
affected_docs: ["TECH_STACK.md"]
---

# Choose Rust

Rust is a strong fit for performance + safety. We considered Go (simpler runtime,
GC pauses) and Python (slower cold start, harder distribution); Rust wins on
cold-start latency and single-binary distribution.
