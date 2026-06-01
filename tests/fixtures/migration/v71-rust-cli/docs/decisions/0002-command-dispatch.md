# 0002 — Command-dispatch architecture

Status: accepted
Date: 2026-04-11

## Context

The CLI exposes several sub-commands that share a config-loading prelude.

## Decision

Adopt a command-dispatch pattern: a top-level parser routes to per-command
handlers, each implementing a common trait.

## Consequences

Adding a command is a localised change. Shared setup lives in one place.
