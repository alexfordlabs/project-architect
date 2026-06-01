---
adr_id: "0001"
title: "Choose Python as primary language"
status: accepted
date: 2026-05-13
decision_keys: ["tech_stack.language"]
affected_docs: ["TECH_STACK.md"]
---

# Choose Python

Python 3.12 is a strong fit for rapid TUI development with rich ecosystem support
(textual, rich, prompt_toolkit, typer). We considered Go (better single-binary
distribution but weaker TUI libraries) and Rust (great performance but slower to
iterate on UI/UX); Python wins on ecosystem breadth for full-TUI experiences.
