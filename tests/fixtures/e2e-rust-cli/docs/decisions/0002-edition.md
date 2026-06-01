---
adr_id: "0002"
title: "Rust 2021 edition"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language_edition"]
affected_docs: ["TECH_STACK.md"]
---

# Rust 2021 edition

Pin the crate to edition 2021. Newer editions (2024) carry breaking changes we
don't need yet; older (2018) lacks features we already rely on.
