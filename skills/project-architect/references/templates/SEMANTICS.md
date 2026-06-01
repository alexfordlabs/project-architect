<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: SEMANTICS
generate_when: project.sub_type in ["general_purpose_language", "domain_specific_language", "query_language", "configuration_language", "educational_language", "transpiler_target"]
required_decisions:
  - project.name
  - project.sub_type
  - paradigm
optional_decisions:
  - host_runtime
  - impl_strategy
depends_on:
  - LANGUAGE_GRAMMAR.md
  - TECH_STACK.md
revision_triggers:
  - paradigm
  - host_runtime
---

# Semantics — {{project.name}}

This document captures the **dynamic semantics** of {{project.name}}: what programs *mean* once they have been parsed. It is the contract between the compiler/interpreter front-end (which produces an AST conforming to `LANGUAGE_GRAMMAR.md`) and the back-end / runtime that actually executes that AST. Where the grammar is shape-only, this document is meaning-only — together they pin down what a valid {{project.name}} program does.

Eight axes are surfaced explicitly because they tend to be load-bearing for everything downstream (stdlib design, FFI surface, concurrency story, tool ergonomics): evaluation order, scoping, memory, mutability, effects, concurrency, error handling, and equality. Each section lists the principal options in active 2026 use, names one or two production exemplars, and asks for an explicit decision rather than letting the answer accrete by accident. A language can be perfectly internally consistent on each axis individually and still be miserable to use if those axes were chosen independently — return to this document when you discover that two of these decisions are pulling against each other and reconcile them here.

## 1. Evaluation model

Decide how arguments and sub-expressions are reduced.

- **Call-by-value (strict, applicative-order):** arguments are fully evaluated before the call. The default in C, Java, Go, Rust, Swift, Python, JavaScript, OCaml — i.e. essentially every mainstream language since 1990. Predictable cost; trivial reasoning about side effects; eager work even when the result is discarded.
- **Call-by-name (normal-order):** arguments substituted unevaluated; re-evaluated every use. Mostly historical (Algol 60); seen today only inside specific constructs (C-preprocessor macros, Scala by-name `=> T` parameters).
- **Call-by-need (lazy + memoised):** arguments substituted unevaluated, evaluated at most once, result memoised. Haskell's default. Enables infinite data structures and elegant control combinators; pays in unpredictable space (thunk leaks) and reasoning about strictness becomes a discipline of its own.
- **Mixed / opt-in laziness:** strict by default with explicit `lazy` / thunks / iterators where useful (Rust's `Iterator`, Python generators, Scala `lazy val`, OCaml's `Lazy.t`). The 2026 mainstream consensus.

State the default explicitly here, then state which opt-out (if any) is available and what it costs the user (an allocation? a thunk header? a hidden recomputation?).

## 2. Scoping

The rule that says which binding a name refers to.

- **Lexical (static) scoping:** the binding is the one textually enclosing the use site. Closures capture lexically. Every serious 2026 language. Pick this unless you have a specific reason not to.
- **Dynamic scoping:** the binding is the most-recent runtime caller's. Emacs Lisp historically; bash variables; Perl `local`. Useful for thread-locals and contextual logging, but globally unprincipled — avoid as a default.
- **Block scope vs function scope:** `let` / `const` are block-scoped; `var` is function-scoped in JS. C blocks scope; Python functions scope (with the `nonlocal` / `global` escape hatches).
- **Hoisting:** are declarations visible before their textual position? JS hoists `var` + function declarations; Python does not hoist but raises `UnboundLocalError`; Rust forbids use-before-declaration at compile time.

Spell out closure semantics in detail. The questions that bite later:
- Do closures capture by reference or by value?
- Can a closure outlive its enclosing scope (heap-allocated) or not (stack-only, Rust `FnOnce` taken-by-move)?
- Can a closure mutate captured bindings (Rust `FnMut`, JS yes, Python with `nonlocal`)?
- What is captured: the binding (cell-style, like Lisp / JS / Rust references) or the value at capture time (Python's `default-arg` workaround forces value-capture)?

## 3. Memory model

How is memory acquired, retained, and freed? This is the single largest semantic choice.

- **Tracing GC** — mark-sweep, mark-compact, generational, concurrent, region-marking. Java (G1/ZGC/Shenandoah), Go, C#, JavaScript, Python (alongside refcounting), OCaml (generational major+minor). Lowest user cognitive overhead; highest implementation effort to get latency right. **2026 note:** the JDK 25 LTS ZGC is fully generational and routinely hits sub-millisecond pauses on multi-TB heaps in production.
- **Reference counting (refcounting) / ARC (automatic ref counting):** Python (with a cycle collector on top), Swift, Objective-C. Predictable destruction order; pays for every assignment; requires a separate cycle-detector or a `weak`-reference discipline.
- **Manual:** C, C++ raw new/delete, Zig (with explicit allocators). Maximum control; maximum hazard. Modern variants (Zig's per-arena allocators, C++ smart pointers) recover much of the safety without ceding control.
- **Ownership + borrowing:** Rust's model — every value has exactly one owner; references are either shared-immutable or exclusive-mutable; lifetimes are inferred or annotated. The **Rust 2024 edition** (stable since Feb 2025) tightened temporary-lifetime rules and made `if let` scopes block-scoped, sharpening this story further. The 2026 exemplar for systems languages and any language where deterministic resource cleanup is part of the spec.
- **Region-based / arena:** all allocations in a scope share a lifetime and are freed in bulk. Cyclone (historical), Mojo (region-typed via MLIR), research languages. Useful for compilers / request-scoped servers; awkward as a sole strategy.
- **Hybrid generational + region (research):** Vale's "generational references" combine generational GC's amortised cost with region-style determinism. Roc, Koka also explore variants. Currently research-grade — interesting reading, not a load-bearing default.
- **No runtime allocation:** every value lives on the stack or in static memory. Realtime / safety-critical / hard-embedded niche. MISRA C profile, SPARK Ada.

**2026 note (Wasm hosting):** **WasmGC** (part of Wasm 3.0, W3C standard since Sept 2025) finally lets a hosted language compile to Wasm without bundling its own GC — the host runtime (browser, Wasmtime, Node, Bun) provides one. This makes "hosted on Wasm with WasmGC" a genuinely viable memory-management story for a new language in 2026, eliminating what used to be a 1-2 MB baseline cost for languages like Kotlin/JS or Scala.js compiled to Wasm.

State your choice. State the FFI memory contract that follows from it (e.g. "GC'd values cannot cross FFI boundary without pinning"). State the destruction semantics (deterministic? finalisers? both?).

## 4. Mutability defaults

Are bindings mutable or immutable by default? This is a small choice that ripples through everything.

- **Immutable-by-default + opt-in mutability** (Rust `let` vs `let mut`, OCaml `let` vs `let mutable`, Haskell entirely, Scala `val` vs `var`, F# `let` vs `let mutable`). The 2026 design trend. Encourages local reasoning; cooperates well with parallelism; surfaces shared mutable state as a code-review concern by syntax.
- **Mutable-by-default + opt-in immutability** (Java `final`, C++ `const`, JS `let` vs `const`, Python — no real const, only naming conventions, Go — no `const` for local variables). Familiar; lower friction for procedural code; harder to reason about aliasing.
- **Pure-functional (no mutability)** — Haskell, Elm, Idris 2. Mutation is encoded as an effect (state monad, etc.). Strongest reasoning guarantees; steepest learning curve.

The aliasing question follows from mutability: if mutable references can be shared, the language MUST give the user some way to talk about that aliasing (Rust's `&mut T` exclusivity, Swift's exclusivity enforcement, OCaml's `mutable` records). If mutable references cannot be shared (Haskell), the question dissolves.

Decide: defaults, sigil/keyword spelling, and whether structural fields inherit container mutability or have their own modifier (Rust: container mutability propagates; OCaml: `mutable` is per-field).

## 5. Effects model

How does the language describe and control side effects (IO, mutation, exceptions, async)?

- **Effectful by default (implicit effects):** any function may perform any side effect. C, Java, Python, Go, Rust (for everything except `unsafe`), Swift, OCaml. The mainstream pragmatic choice. Effects don't appear in types; reasoning is by convention and documentation.
- **Pure-functional with explicit effect monads:** every effect is a value of an effect-typed monad (`IO`, `ST`, `State s`, etc.). Haskell, PureScript, Elm (Cmd/Sub). Strong static guarantees; significant cognitive load; forces an `Applicative`/`Monad` learning step.
- **Capability-based effects:** functions can only perform effects whose capabilities they have been passed as values. Newspeak, Pony (with the wider "reference capability" idea), Roc (effect-marked but capability-flavoured), object-capability research. Promising for security-critical and sandboxed-plugin scenarios.
- **Algebraic effect handlers:** effects are first-class operations whose semantics are supplied by an enclosing handler — like resumable, type-checked exceptions. The most active research area in 2026 language semantics.
  - **Koka 3.2.3** (Microsoft Research) is the cleanest research design: row-polymorphic effect rows, exhaustive handler checking, compiles natively to C with reference-counting (Perceus) — no GC needed. The reference language to read if you are designing your own effect system in 2026.
  - **OCaml 5.4** ships production-grade algebraic effects in the runtime (used to implement `Eio`, the modern async/IO library); the **deep-handler** syntax landed in 5.3 (Oct 2025) and is still officially labelled "experimental" but is now used in production by multiple teams.
  - **Roc** (alpha) marks effectful functions with a trailing `!` (`readFile!`) and tracks effects in the type system without monad noise.

If you choose anything other than "effectful by default", document the escape hatch: a language that has no `unsafePerformIO`-style hatch is research-grade by construction.

## 6. Concurrency model

How do multiple computations interleave or run in parallel?

- **None / single-threaded:** the language is synchronous and the user runs multiple processes for parallelism. Reasonable for embedded DSLs, build-time tools, configuration languages.
- **Threads + locks (shared-memory):** OS threads, mutexes, condition variables. C/C++, Java, Rust (`std::thread`, `Mutex`), Go (alongside goroutines), Swift. Composes poorly under correctness pressure; ubiquitous because OS primitives are themselves shared-memory.
- **Async / await (cooperative + non-blocking I/O):** the user's code is single-threaded by default; awaits yield to a scheduler that multiplexes thousands of tasks onto a small thread pool. JS, Python (asyncio), C#, Rust (`async fn`), Swift (`async let`, structured concurrency since 2021). **Rust note:** async-fn-in-trait is stable since 1.75 (Dec 2023); **async closures** stabilised in 1.85 (Feb 2025), unblocking ergonomic combinator APIs.
- **Actor model:** units of state are isolated actors; communication is via asynchronous messages. Erlang/Elixir (BEAM-supervised), Akka (Scala/Java), Pony (with capability-safe message passing). Famous fault-tolerance story; weaker for synchronous request/response patterns.
- **CSP (communicating sequential processes):** goroutines + channels (Go), occam, Clojure `core.async`. Easier-than-actors local reasoning; harder distribution story.
- **Structured concurrency:** all child tasks are scoped to a parent block and the parent cannot return until its children have terminated or been cancelled. Pioneered by Trio (Python), formalised in Kotlin (`coroutineScope`), shipped in Swift (`async let`, task groups), shipped in **Java 25 LTS** as **JEP 506** (structured concurrency, finalised after JEP 480/505 previews; pairs with virtual threads). The 2026 best-practice frame for any new async/concurrency story — adopt by default unless you have a specific reason to ship raw spawn/join.

**2026 note (Java virtual threads):** Java 21 finalised **virtual threads** (JEP 444); Java 25 LTS (Sept 2025) is the long-term-support release that's now baseline in greenfield enterprise codebases. Virtual threads + structured concurrency together remove most of the reason async-await exists in Java — synchronous-looking code scales to millions of concurrent tasks. A new JVM-hosted language should design around this.

Pick a primary model, and explicitly call out interop: can structured-concurrency code call into thread-pool code? Can async code call into sync code without deadlocking? (The classic Python `asyncio` gotcha; address it head-on here.)

## 7. Error model

How does a function signal failure?

- **Unchecked exceptions:** thrown freely, propagate up the stack, caught by `try/catch`. Java's `RuntimeException`, Python, JS, C#, C++. Convenient; obscures the failure surface in function signatures; performance cost on the throw path is real.
- **Checked exceptions:** the failure types are in the signature; callers must catch or re-declare. Java's checked `Exception` (widely disliked but instructive), Swift's `throws` (a lighter take that works because there's only one error type per throwing function), C++ `noexcept` as the negative form.
- **Result / Either / Optional values:** failures are values returned from the function; the type system forces handling. Rust `Result<T, E>` + `?`, Haskell `Either e a`, Swift `Result<T, E>` (rarely used because `throws` covers it), Go (the `(value, error)` tuple convention — the same pattern minus the type system support).
- **Panic-and-abort:** unrecoverable failure terminates the program (or the thread / fibre). Rust `panic!`, Erlang's "let it crash". Pairs with a supervisor (Erlang) or unwind-and-cleanup (Rust) discipline.
- **Hybrid (Rust-style):** `Result` for expected failures (file not found, parse error) + `panic!` for programmer-bug failures (index out of bounds, broken invariants). Spelling these as different things is the design lesson Rust contributed; consider adopting it directly.

Decide the propagation sugar (`?` in Rust, `try` in Swift, `do`-notation in Haskell). Decide whether errors carry a stack trace (Java yes always; Rust optional via `Backtrace`; Go via `errors.New` plus convention). Decide the panic-handler / unhandled-error contract: log + abort? log + thread-die? operator-supplied callback?

## 8. Equality semantics

What does `a == b` mean?

- **Reference equality:** `==` compares object identity (Java's `==` for objects, JS strict `===` for objects, Lisp `eq`). Fast; almost never what the user actually wanted; usually requires a separate `.equals` / `.equal?` for value comparison.
- **Structural equality:** `==` compares values component-wise by default. Python, Ruby, Haskell (`Eq` derived), Rust (`#[derive(PartialEq, Eq)]`), OCaml's `=`. The 2026 default.
- **Custom-derivable / user-controlled:** equality is a trait/type-class the user must implement (or derive) per-type. Rust, Haskell, Swift (`Equatable`). Pairs structural defaults with full extensibility.

Spell out the equality / hash / ordering contract here:
- If `a == b` then `hash(a) == hash(b)` — does the language enforce this (Rust does via `Eq + Hash`; Java requires it by convention; Python by convention)?
- Total order vs partial order: `NaN != NaN` is one of the few cases where IEEE-754 forces partial order. Rust splits `PartialOrd` from `Ord` for exactly this reason; document your stance.
- Default equality for floats: Rust's `f64: PartialEq + !Eq` is the principled answer. Python's `float.__eq__` lies about NaN. Pick a side.
- Default equality for collections, closures, function types — these are usually not implementable safely; spell out what `==` does (or refuses to do) on them.

## Notes for the executor

When `document-author` consumes this template at Phase 4:

1. Substitute every `{{...}}` placeholder from `state.decisions` — `{{project.name}}` in particular.
2. If `paradigm == "functional"` or `"logic"`, expand §5 (effects model) — pure-functional designs usually need a section per effect handled.
3. If `host_runtime` is `wasm` or `wasm_component`, add a paragraph in §3 acknowledging WasmGC's effect on the memory model choice.
4. If `host_runtime` is `beam`, default §6 to "actor model" and §7 to "let it crash" — those are the BEAM idioms and diverging from them costs the user the platform's value.
5. Cross-link to `LANGUAGE_GRAMMAR.md` for the *shape* of expressions and to `TYPE_SYSTEM.md` for what *types* mean. This document only covers the dynamic interpretation.
6. Commit: `architect(phase-4): generate SEMANTICS.md`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
