<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: TYPE_SYSTEM
generate_when: project.sub_type in ["general_purpose_language", "domain_specific_language", "query_language", "configuration_language", "educational_language", "transpiler_target"]
required_decisions:
  - project.name
  - project.sub_type
  - type_system
optional_decisions:
  - paradigm
depends_on:
  - SEMANTICS.md
  - LANGUAGE_GRAMMAR.md
revision_triggers:
  - type_system
  - paradigm
---

# Type system — {{project.name}}

This document captures the **type-system design** of {{project.name}}: which programs are *well-typed*, what guarantees that classification buys you, and what cognitive load it imposes on the user. It is the contract between the type checker (which decides "yes" or "no" for a given program) and every downstream tool that relies on types — the LSP that drives autocomplete, the optimiser that picks a representation, the FFI that needs ABI shapes, the formatter that aligns annotations.

`LANGUAGE_GRAMMAR.md` pinned the *shape* of expressions; `SEMANTICS.md` pinned what they *mean* at runtime; this document pins what they *promise* before runtime. The three documents intentionally overlap at the seams (e.g. mutability appears in semantics §4 *and* type system §3) — when they disagree, prefer this document for the static story and `SEMANTICS.md` for the dynamic story, and file an issue to reconcile.

Eight axes are surfaced explicitly because they tend to lock each other in: once you commit to "static + Hindley-Milner + parametric polymorphism", you've ruled out subtyping-based variance and you've signed up for a value-restriction story. Make each decision deliberately, name a 2026 production exemplar, and write down the rationale — the next person to revise this document will thank you.

## 1. Static / dynamic / gradual

The primary classification. Decide first; everything else follows.

- **Static typing:** every expression has a type known before the program runs; ill-typed programs are rejected by the compiler. Rust, OCaml, Haskell, Swift, Kotlin, Go, TypeScript (modulo `any`/`unknown`), Java, C#, Scala 3. The 2026 default for any general-purpose language: refactoring confidence, IDE features (jump-to-definition, find-references, rename), and a class of bugs that simply cannot occur all derive from this choice. Pays in compile time, in annotation noise (mitigated by inference — see §2), and in a steeper learning curve for the first week.
- **Dynamic typing:** types attach to *values*, not expressions; type errors surface at runtime. Python, Ruby, JavaScript (without TypeScript), Clojure, Erlang, Lua. Faster prototyping; lower friction for one-shot scripts; weaker refactoring guarantees once a codebase passes ~5 kLOC. The 2026 trend is to *retrofit* static types onto dynamic languages (mypy + Pyright for Python, Sorbet for Ruby, TypeScript for JS) rather than to design dynamic-first new languages.
- **Gradual typing:** the language accepts both fully-typed and fully-untyped fragments and inserts runtime casts at the boundary. TypeScript (`any` as the bypass), Python with `typing.Any` + mypy `--strict` opt-in, Hack (Facebook's PHP dialect), Typed Racket. Useful for evolving an existing dynamic codebase; rarely the right choice for greenfield design. The runtime-cast story is where soundness leaks — TypeScript's `any` famously gives up soundness in exchange for migration ergonomics; Typed Racket's contracts preserve soundness at the cost of perf.

**Trade-off table:**

| Axis | Static | Dynamic | Gradual |
|---|---|---|---|
| Tooling support | Highest (LSP, refactor, autocomplete all "free") | Moderate (runtime introspection helps) | Static where typed; dynamic at boundaries |
| Refactoring confidence | High | Low | Medium (depends on coverage) |
| Learning curve | Steeper week 1 | Gentler week 1 | Cumulative (must learn both stories) |
| Prototype velocity | Moderate (inference helps) | Highest | Moderate |
| Runtime overhead | None for types | Type tags on every value | Casts at the boundary |
| Error class eliminated | "X has no attribute Y" entirely | None statically | Only inside the typed fragment |

State the choice, the rationale, and the escape hatches. "Static with `dyn Any`/`Box<dyn Trait>` escape" is a different language than "static with no dynamic dispatch at all".

## 2. Type inference algorithm

How much type annotation is the user required to write?

- **No inference (fully manifest):** every binding declares its type. Java pre-`var` (2018), C, C++ pre-`auto`. Verbose; trivial to implement; gives the IDE every type for free at every position.
- **Local type inference (`var`/`let` reuses RHS type):** the binding takes its type from the initialiser; function signatures are still mandatory. Java 10+ `var`, C++11 `auto`, Go `:=`, Swift `let`/`var`, C# `var`, Rust `let` (Rust inference is local *plus* unification across a function body, slightly more powerful). The 2026 mainstream sweet-spot: low cognitive load, predictable error locations, function signatures remain readable.
- **Hindley-Milner (whole-function, Damas-Milner unification):** the type of every binding and every function is inferred from constraints, often with zero annotations needed. OCaml, Haskell, Standard ML, Elm, PureScript. Powerful; produces the "no annotations" experience famous in ML-family languages; pays in error messages — a unification failure 200 lines from the bug is a real cost, and dense polymorphic types make hover-tooltips less ergonomic than local inference.
- **Bidirectional type checking:** the algorithm alternates between *inferring* a type for an expression and *checking* an expression against an expected type; annotations at boundaries (`let x: T = …`, `(expr : T)`) seed the propagation. Rust, Scala 3, Swift, TypeScript, Roc, Lean 4. The 2026 design trend — combines local-inference ergonomics with HM's algebraic strength, gives precise error locations, and handles features (higher-rank polymorphism, GADTs, dependent types) that pure HM struggles with.
- **Constraint-based (HM extended):** generate constraints during a forward pass, solve them during a backward pass. Rust's borrow checker is constraint-based; Scala's type checker uses constraint propagation; OCaml's `Constraint` module is an explicit example. Composes well with type-class / trait elaboration.

**Specific design decisions that follow:**

- **`let`-polymorphism:** does `let f = fun x -> x in (f 1, f "a")` type-check? In HM, yes (`f` is generalised to `forall a. a -> a` at the `let`). In some bidirectional systems, no — the type is fixed at the inferring use. Decide and document.
- **Value restriction:** ML languages restrict `let`-polymorphism to syntactic *values* to keep type inference sound in the presence of mutable references. SML's classical formulation; OCaml's relaxed value restriction (1995) widens it. If your language has refs/IORef/mutable cells and parametric polymorphism, you owe the user a story here.
- **Rank-1 vs rank-N polymorphism:** rank-1 = quantifiers only at the outermost position (HM-decidable). Rank-N = `forall` may appear under arrows (`(forall a. a -> a) -> Int`). Required for Church-encoded data, ST monad's runST, GHC-style `RankNTypes`. Inference is undecidable for rank ≥ 3; annotations required. Decide whether to support and where annotations are mandatory.

State the algorithm, point at a reference (e.g. "Dunfield-Krishnaswami bidirectional, with let-generalisation per Vytiniotis et al."), and call out which positions accept inference vs require annotations.

## 3. Polymorphism

How does the language let one definition serve many types?

- **None (monomorphic):** every function takes concrete types. Go pre-1.18, K&R C, early Pascal. Simple compilers, no abstraction over types — collections become a stdlib code-generation problem (Go's `sort.Sort` interface workaround).
- **Parametric polymorphism (generics):** definitions are universally quantified over type variables (`fn id<T>(x: T) -> T`). Rust, Java, C#, Scala, Haskell, OCaml, Swift, Kotlin, TypeScript, Go 1.18+. The 2026 baseline. Implementation choices: monomorphisation (Rust, C++, Swift — code-explosion cost, no runtime dispatch) vs type-erasure (Java, Haskell — single code path, requires boxing of value types).
- **Ad-hoc polymorphism (type classes / traits / protocols):** an operation is overloaded; the dispatch is on the *type* of the argument, not the runtime value. Haskell type classes (1989), Rust traits (with coherence + orphan rules), Swift protocols, Scala givens, Lean 4 type classes (used for `Monad`, `Decidable`, `BEq`, …). The 2026 idiomatic mechanism for abstraction without paying a vtable per call. Coherence (the "one canonical instance per type" rule) is the distinguishing axis: Haskell + Rust enforce it; Scala's "implicits" / "givens" do not (with documented foot-guns).
- **Subtyping polymorphism:** `Cat <: Animal` lets a function expecting `Animal` accept a `Cat`. Java, C#, Scala, TypeScript structural subtyping, OCaml object subtyping. Powerful but interacts awkwardly with type inference — Hindley-Milner does not extend to subtyping. Scala 3 and TypeScript both pay real algorithmic complexity for subtype-aware inference.
- **Row polymorphism:** record/variant types parametrise over the *set of fields/cases* they contain (`{ name: String | rest } -> rest`). OCaml object types, PureScript records, Elm records, Koka effect rows. Cleaner than subtyping for "function that needs at least these fields"; integrates well with HM-style inference.
- **Variance:** does `List<Cat> <: List<Animal>`? Covariance (yes for read-only), contravariance (input-only), invariance (mutable containers — Java arrays are unsafely covariant; Java generics are invariant by default with `? extends` / `? super` for variance annotations). Scala uses `+T`/`-T`/`T`. Rust deliberately picks per-position variance and computes it from the field structure — no user annotation. If your language has both subtyping and generics, you owe a variance story.

**2026 Rust exemplar (the state of the art for ad-hoc + parametric):**

- Traits with associated types (`type Item;`) for type-level functions.
- **Generic Associated Types (GATs)** — stable since Rust 1.65 (Nov 2022), now load-bearing for `LendingIterator`, async-trait, and the wider trait-as-type-level-function pattern. GATs let an associated type itself be generic (`type Item<'a> where Self: 'a;`), unblocking abstractions that previously required workarounds.
- **Async fn in traits** — stable since 1.75 (Dec 2023), with `RPITIT` (return position impl trait in traits) generalising the mechanism.
- **Trait upcasting coercion** — stable since 1.86 (Apr 2025), letting `&dyn SubTrait` coerce to `&dyn SuperTrait` cleanly.
- **`impl Trait` in associated types / return position** — broadly applicable as of Rust 2024 edition (stable Feb 2025).
- Edition 2024 tightens trait coherence + the `dyn Trait` syntax (now requires `dyn` consistently — the bare `Trait` form is a warning in 2021 and an error in 2024).

If you are designing a trait/protocol system in 2026, *read the Rust traits chapter of the reference* (and the GAT RFCs) before committing. Many languages have stumbled into the corners Rust has already mapped.

## 4. Sum types + pattern matching

A *sum type* (a.k.a. tagged union, variant, enum-with-data, discriminated union) is a type whose values inhabit exactly one of several named cases, each carrying its own payload. Pattern matching is the elimination form.

**Decide:**

- **Sum types: yes / no.** A 2026 language without sum types is making the user pay for it elsewhere (sentinel values, hand-written tagged-union structs, visitor patterns). Recommended: yes. Exemplars: Rust `enum`, Haskell `data`, OCaml variants, Scala 3 `enum` (since 2021), Swift `enum`, TypeScript discriminated unions, Kotlin sealed classes, F# discriminated unions.
- **Pattern matching: shape.** `match`-expression (Rust, Scala 3, OCaml, Haskell `case`); statement form (older Scala, C# `switch` statement). 2026 default: expression form.
- **Exhaustiveness checking.** Does the compiler reject `match x { Some(_) => … }` when `x: Option<T>` has a `None` case? Rust + Haskell + OCaml + Scala 3 + Swift all enforce; C# `switch` warns since 9.0, errors in some `nullable` configurations. **Mandatory exhaustiveness is the 2026 standard.**
- **Nested patterns.** `match x { Ok(Some(n)) if n > 0 => … }` — recursive patterns inside other patterns. Required for non-trivial use.
- **Or-patterns.** `match x { 0 | 1 | 2 => "small", … }` — disjunction inside one arm. Stable in Rust since 1.53 (Jun 2021), in OCaml since forever, in Python 3.10+ (`case 0 | 1 | 2:`).
- **Guards.** `match x { n if n > 0 => … }` — extra boolean predicate. Standard; remember exhaustiveness checking must treat the guarded arm as *non-covering* for the rest of the analysis (Rust does this correctly; some early languages did not).
- **Refutable vs irrefutable patterns.** `let (a, b) = pair;` is irrefutable (the pattern *must* match — destructuring assignment). `if let Some(x) = opt` is refutable (may not match). Rust distinguishes syntactically; many other languages don't and pay for it with subtle bugs.
- **Bindings + scrutinee ownership.** Does `match x { Some(y) => …}` consume `x`? Move semantics interact with pattern matching — Rust's `match` is a key place where ownership is exercised. If your language has move/affine types (see §6), this is a *primary* design surface.

## 5. Algebraic data types vs OOP class hierarchies

The classic "expression problem" framing: you have *data variants* (Int, Add, Mul, …) and *operations* (eval, pretty-print, optimise, …). Adding either dimension cheaply is easy; adding *both* cheaply is the hard part.

- **ADT-first (functional style):** variants are an enum/sum type; operations are functions that pattern-match. *Adding an operation:* trivial — write a new function. *Adding a variant:* costly — every existing function's pattern match must be updated (compiler will tell you where, thanks to exhaustiveness). The right choice when the *operation set* is open-ended and the *variant set* is mostly closed. Exemplar: a compiler IR. Rust, Haskell, OCaml, F#, Scala 3 enums.
- **OOP-first (class hierarchy):** each variant is a class implementing a shared interface; operations are methods. *Adding a variant:* trivial — write a new class implementing the interface. *Adding an operation:* costly — every existing class needs a new method (no exhaustiveness story to help you find them; runtime errors otherwise). The right choice when the *variant set* is open-ended and the *operation set* is mostly closed. Exemplar: a UI widget hierarchy. Java, C#, Smalltalk, Ruby.
- **Visitor pattern:** OOP's workaround to fake ADT-style dispatch — a visitor interface with one method per variant; double-dispatch. Verbose; loses the ergonomics of pattern matching; reintroduces some of ADT's "update everywhere when adding a variant" cost without the compiler help. Symptom of a language without proper sum types.
- **Sealed hierarchies / sealed traits:** the bridge. A `sealed` type declares that its set of variants is *closed at compile time* — only subtypes in the same file/module are allowed. Now the compiler *can* check exhaustiveness over the hierarchy. Scala 3 sealed traits, Kotlin sealed classes, Java 17+ sealed classes (JEP 409), Rust enums (implicitly sealed). The 2026 sweet spot — gives you both inheritance ergonomics *and* pattern-match exhaustiveness.

**Recommendation:** in a new 2026 language, pick a *primary* modelling primitive (ADTs for FP-leaning, sealed hierarchies for OOP-leaning) and ensure the *other* axis is at least competent. Rust's "ADTs are primary; traits provide operation-extension via blanket impls" is the cleanest contemporary answer. Scala 3's "sealed enums are primary; traits/extensions handle both axes" is the second-cleanest. Avoid Java pre-17's "classes only, write a Visitor by hand" — it is the path of pain.

## 6. Advanced features

The frontier. Adopt selectively — each row below is a genuine cognitive-tax bump on the user.

### Linear / affine types

A *linear* type guarantees a value is used **exactly once**. An *affine* type allows **at most once** (zero or one). Used for resource management without GC, for protocols (channels that must be closed exactly once), for write-once buffers.

- **Rust ownership / move semantics:** affine by construction — every non-`Copy` value is used at most once, dropping is the "use zero times" path. The 2026 mass-market success story for affine types; ships in production at every scale.
- **Linear Haskell (GHC's `LinearTypes` extension):** opt-in linear arrow `a %1 -> b`. Stable in GHC 9.0+ (2021), expanding in 2025-26 with `LinearLet`. Used for safe APIs around mutable arrays, file handles. Not yet pervasive; the ecosystem is gradually moving.
- **Idris 2 (Quantitative Type Theory):** every binding has a *quantity* — `0` (erased at runtime), `1` (linear), `ω` (unrestricted). Designed by Edwin Brady (2020+), self-hosted, the cleanest unified linear+dependent design. Research-positioned in 2026, but actively maintained and pedagogically the right place to learn the theory.

### Refinement types

A type carried with a *predicate* — `{ n: Int | n > 0 }` is the type of positive integers. The SMT solver discharges the proofs.

- **Liquid Haskell** is the production-grade exemplar — refinement annotations on Haskell types, Z3 as the backend, used in production at Tweag, Awake Security. Active 2026: works with GHC 9.x.
- **F\*** (Microsoft Research): refinement types + effects + dependent types; used to verify TLS implementations (miTLS) and cryptographic code (HACL\*, used in Firefox and the Linux kernel).
- **Liquid Java**, **Stainless** (Scala) — academic but production-aimed.

Refinement types pay back when *correctness matters more than incidental ergonomics*: verifying parsers, crypto, financial calculations. They are a poor fit for "we just want fewer null-pointer bugs" — use `Option`/`Maybe` for that.

### Dependent types

Types can *depend on values*: `Vec n A` is the type of vectors of length `n` (where `n` is a term, not just a type variable). Enables: vectors-of-known-length, matrix-multiplication-shape-checking-at-the-type-level, in-language proofs of program properties.

2026 production / production-adjacent options:

- **Lean 4 + Mathlib4:** Lean 4 (Microsoft Research / Lean FRO) is the dependent-types option closest to general-purpose use today. The Mathlib4 library passed **210,000 theorems in May 2025** and is growing weekly; it's the largest unified formal mathematics library in existence. Lean compiles to efficient C via its own backend; the language is genuinely usable as a programming language alongside its theorem-prover role. Used at Microsoft's Lean FRO and at AWS for formal methods. The state-of-the-art "experimental-but-usable" option for someone who wants dependent types in 2026, especially if formal verification is part of the goal. **If you are designing a dependently-typed language in 2026, read the Lean 4 manual and study Mathlib4's tactic-and-elaboration design first.**
- **Idris 2:** Quantitative Type Theory, self-hosted, full dependent types with linear/affine quantities. Edwin Brady's research language; pedagogically excellent; smaller ecosystem than Lean. Research-positioned.
- **Agda:** Cubical Type Theory (HoTT-flavoured), strongest type-theoretic story, weakest as a *programming* language (slow compilation, smaller ecosystem). Research / teaching positioned.
- **Coq / Rocq:** the elder statesman (Rocq Prover is the renamed Coq, since 2024). Production-proven for verification (CompCert, software foundations); not a general-purpose programming language.

Avoid claiming "dependent types" lightly. The implementation work is enormous (a full elaborator + unifier + tactic language); the user-facing complexity is real; and the ergonomic gap to Rust-style refinement-via-traits is small for most non-verification work. Adopt dependent types when *formal proof* is in scope.

### Effect types

Effects in the type system. See `SEMANTICS.md §5` (Effects model) for the runtime story; this section covers the *type* surface.

- **Monadic effects:** `IO a`, `State s a`, `Either e a` — every effect is a parametric type constructor with `>>=`/`return`. Haskell, Idris 2, PureScript. Mature; the cognitive overhead (monad transformers, `do`-notation discipline) is real.
- **Algebraic effect rows:** `<exn|st|console>` — effects accumulate as a row of capabilities. Koka 3.2.3, OCaml 5.4 (runtime is algebraic-effects-based; type-level row tracking is a research direction not yet stable), Eff, Frank. The 2026 research direction.
- **Capability passing (effects via values):** functions take effect handles as ordinary arguments. Roc's effect system, Newspeak, object-capability languages. Aligns with security stories.

## 7. Type coercion rules

When the user writes `x + y` and `x: Int32`, `y: Int64`, what happens?

- **Implicit coercion (auto-widening):** the compiler promotes the narrower type to the wider one. C, C++, Java numeric promotions, JS `+` (with the well-known pathologies — `"3" + 4 === "34"` but `"3" * 4 === 12`). Convenient for arithmetic; treacherous when the promotion lattice has unexpected edges.
- **Explicit-only:** every type change is a user-visible cast — `x + (y as i32)`, `x as f64`. Rust, Go (mostly), Zig, Haskell (no built-in coercions at all — `fromIntegral`/`fromRational` are explicit). The 2026 default for new languages: predictable, surfaces the cost of conversions, no surprise integer-overflow or precision-loss bugs.
- **Numeric tower coercion:** Scheme/Racket's `(+ 1 1.5)` promotes through a defined lattice (Integer ⊂ Rational ⊂ Real ⊂ Complex). Mathematically clean; not a fit for systems languages where the bit-width is part of the contract.
- **Subtype coercion:** if `S <: T`, an `S` is automatically usable where `T` is expected. Java reference types, Scala, TypeScript structural subtyping. The variance question (§3) applies.

**Pitfalls of JavaScript-style `==`:**

JavaScript's `==` operator performs *implicit coercion across types* — `0 == ""` is `true`, `[] == false` is `true`, `null == undefined` is `true` but `null !== undefined`. The result is a comparison operator whose behaviour is essentially unmemorable, leading to the universal lint rule "always use `===`". A 2026 language should *not* repeat this design: either equality coerces predictably (numeric promotion only, no string ↔ number) or it does not coerce at all. Document the rule in `SEMANTICS.md §8` (Equality semantics); commit to it here.

**Recommendation for new languages:** explicit-only, with a small set of named coercion functions (`i32.to_i64`, `f64.from_i32`) and zero implicit promotions. Pay the keystroke cost; collect the predictability dividend.

## Notes for the executor

When `document-author` consumes this template at Phase 4:

1. Substitute every `{{...}}` placeholder from `state.decisions` — `{{project.name}}` in particular.
2. Cross-link to `SEMANTICS.md` throughout; in particular, if `optional_decisions.effect_system` is set in state, the §6 *Effect types* subsection should reference the chosen effect strategy by name and link to the SEMANTICS.md §5 Effects-model section that pins the runtime story.
3. Cross-link to `LANGUAGE_GRAMMAR.md` for the *shape* of type annotations (`: T`, `<T>`, `forall T.`) — this template covers what the types *mean*, not how they are spelled.
4. If `type_system == "dynamic"`, collapse §2 (inference algorithm) to a one-line note ("not applicable — types are runtime values") and expand §7 (coercion) — dynamic languages typically have the most coercion machinery and the most surprises.
5. If `paradigm == "functional"` and `type_system == "static"`, expect §3 to favour parametric + type-class polymorphism (Hindley-Milner extended with Wadler-Blott type classes) and §4 to be load-bearing.
6. If `paradigm == "logic"` (Prolog-family), most of this template is not the right frame — the type system question becomes about modes, determinism annotations, and Mercury-style soundness; either rewrite the template or pick a different one.
7. Commit: `architect(phase-4): generate TYPE_SYSTEM.md`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
