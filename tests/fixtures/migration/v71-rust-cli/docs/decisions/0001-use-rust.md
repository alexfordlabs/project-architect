# 0001 — Use Rust for the CLI

Status: accepted
Date: 2026-04-10

## Context

We need a fast, single-binary CLI with no runtime dependency.

## Decision

Use Rust. Considered Go and Zig; Rust wins on the ownership model and the
maturity of `clap` for argument parsing.

## Consequences

Contributors need a Rust toolchain. Cold-start is well under the 50ms target.
