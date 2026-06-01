<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: STDLIB
generate_when: project.sub_type in ["general_purpose_language", "domain_specific_language", "query_language", "configuration_language", "educational_language", "transpiler_target"]
required_decisions:
  - project.name
  - project.sub_type
optional_decisions:
  - paradigm
  - host_runtime
depends_on:
  - SEMANTICS.md
  - TYPE_SYSTEM.md
revision_triggers:
  - project.sub_type
  - host_runtime
---

# Standard library — {{project.name}}

This document captures the **shape of {{project.name}}'s standard library** — what ships in the box, what is deliberately delegated to a package manager, and the cross-cutting design rules that make the stdlib hang together as a coherent surface rather than a junk drawer accumulated by historical accident. It is the contract between the language designers (who can change names and shapes only at major-version cost) and every downstream user, who will type `import` against this surface every working day for the lifetime of the language.

`SEMANTICS.md` pinned what programs *mean* at runtime; `TYPE_SYSTEM.md` pinned what they *promise* before runtime; this document pins what they *can call without writing it themselves*. Those three documents define the language as experienced by a user — the syntax (`LANGUAGE_GRAMMAR.md`) is the part they read; the stdlib is the part they reach for. A beautiful core semantics with a stdlib that does not contain a `HashMap` is a beautiful language nobody adopts.

Ten axes are surfaced explicitly because the stdlib is where most of a language's long-term maintenance debt lives. The keyword `print` cannot evolve once it ships; the JSON parser's behaviour around duplicate keys becomes folklore; the time API's choice of representation gets enshrined for thirty years (Java's `Date` class shipped in 1995 and was only meaningfully replaced in Java 8 — *thirteen years later*). Decide each axis deliberately, name a 2026 production exemplar, and write down the rationale — the cost of getting this wrong is measured in decades.

## 1. Inclusion philosophy

The first decision: how much ships in the box?

- **Small core ("microkernel" stdlib):** ship the bare minimum — primitives, basic collections, FFI, control flow. Everything else lives in user-space packages. **Lua** (the canonical example — the full Lua 5.4 stdlib fits in a few hundred KB), **Scheme** (R7RS-small at ~50 procedures, with R7RS-large for the optional batteries), **Clojure** (leans on Java's stdlib for the bulk; Clojure-proper is small). Cheap to maintain, easy to embed, lets the ecosystem evolve the boring parts at its own pace. Pays in onboarding friction (`Hello, world` works; `download a URL` requires hunting a package) and in version-skew when two libraries pick different competing implementations of the same primitive.
- **Batteries-included:** ship a comprehensive stdlib covering HTTP, JSON, regex, datetime, crypto, archive formats, subprocess management. **Python** ("batteries-included" is literally Guido's slogan from 1999 — `urllib`, `json`, `csv`, `xml.etree`, `sqlite3`, `argparse`, `unittest`, `datetime`, `os.path`, `pathlib`, `subprocess` all in core), **Go** (`net/http`, `encoding/json`, `database/sql`, `crypto/*`, `html/template`, `testing` — Go's stdlib is the reason a Go binary needs zero runtime dependencies for most server tasks), **Rust** (notably *not* batteries-included for its core stdlib — see "curated" below — but the `tokio` + `serde` + `reqwest` triad has *de facto* canonical status). High user-onboarding velocity; new users can be productive in week one without a package-manager tutorial. Pays in stdlib churn (Python's `urllib` vs `urllib2` vs `urllib3` saga; the `asyncio` retrofit took a decade to settle) and in deprecation tax — once a JSON parser ships in stdlib it is part of the language's compatibility surface forever.
- **Curated minimal + first-party package ecosystem:** ship a tight core stdlib (primitives, collections, async runtime hooks, FFI) and treat a small set of *first-party* but separately-versioned packages as effectively-stdlib. **Rust** is the 2026 exemplar — `std` is tightly scoped (no HTTP, no JSON, no datetime — only what cannot live outside the compiler's release train), and `serde`, `tokio`, `rayon`, `regex`, `chrono`/`time`, `reqwest`, `clap` form the *de facto* stdlib through `crates.io`. **Zig** follows a similar philosophy. Lets the high-churn libraries iterate without dragging the compiler release cycle; pays in discoverability (new users do not know which crate is canonical) and in the social cost of maintaining an "is this crate trustworthy?" cultural knowledge layer (cargo doc, `crates.io` download counts, `lib.rs` curation).

**Trade-off table:**

| Axis | Small core | Batteries-included | Curated + first-party packages |
|---|---|---|---|
| Onboarding velocity | Low | Highest | Medium (after one tutorial) |
| Stdlib churn cost | Lowest | Highest (forever-compat surface) | Medium (each package versions independently) |
| Compile/binary size | Smallest | Largest | Medium |
| Embeddability | Highest | Lowest | Medium |
| Library evolution | Fastest (no release-train coupling) | Slowest | Fast (per-package) |
| "Which JSON library?" cultural cost | Highest | Lowest | Medium |

State the chosen philosophy explicitly, with one sentence on *why* — e.g. "batteries-included because {{project.name}} is aimed at scripting workloads where dependency setup is friction we cannot afford". Then keep the rest of this document consistent with that choice: a small-core language should not grow a `stdlib::http` module in section 6.

## 2. Module organization

How is the stdlib *namespaced*, and how does the user reach into it?

- **Flat namespace:** every stdlib symbol lives in one global namespace; users write `print(x)`, `length(s)`, `map(f, xs)` without qualifying. Lua, early Scheme, Tcl. Cheapest to learn; collides catastrophically at scale (every name a stdlib function takes is a name a user cannot use without shadowing).
- **Hierarchical, single global root:** `os.path.join(...)`, `collections.defaultdict`, `xml.etree.ElementTree`. Python is the canonical example — every stdlib module hangs off the implicit root, accessed by dotted paths and `import` statements. Familiar; scales to thousands of names without collision; pays in import ceremony (`from collections.abc import Mapping` is six tokens to get one name).
- **Hierarchical, multiple roots / crates:** Rust's `std::*`, `core::*`, `alloc::*` — a small number of top-level crates partition by *capability* (does this code need an OS? does it allocate?), reflecting Rust's no-std story. Go's stdlib similarly partitions into `net/`, `encoding/`, `crypto/`, etc. — qualified imports (`import "net/http"`) are the only access path, so collision-by-shadowing is impossible.
- **Qualified imports vs unqualified imports:** does `import foo` bring `foo`'s names into the local scope (Python `from foo import *`, Java `import foo.Bar`), or does it bring only the module object (Python `import foo` → `foo.bar()`, Go, Rust `use foo`)? The 2026 default is "qualified by default, unqualified is opt-in" — it loses one keystroke per call site and gains a vastly clearer reading experience at every call site forever.

**Specific design questions to commit to:**

- **Naming conventions.** `snake_case` (Rust, Python), `camelCase` (Java, JS, Swift), `PascalCase` (Go exported, C#)? Decide once; enforce mechanically (formatter + lint) for the entire stdlib.
- **Submodule discovery.** Can a user list everything in a module? Python's `dir()`, Lua's `pairs(_G)`, Rust's `cargo doc --open` — the answer "yes, ergonomically" is a quiet 10x for new-user velocity.
- **Re-exports / prelude.** Does the stdlib ship a *prelude* — a small set of names made available without explicit `import`? Rust's prelude (`Option`, `Result`, `Vec`, `String`, `Box`, `Iterator` traits, `Drop`, `Send`, `Sync`, `Default`, `Clone`, the macros…) is genuinely load-bearing for ergonomics; Haskell's `Prelude` is famously the source of name collisions (`Data.List.map` vs `Prelude.map`) that Haskellers spend social energy navigating. Decide what is in the prelude, and treat that list as a stability contract.
- **Module identity vs file identity.** Does one file = one module (Python, Go), or can modules span files (Rust `mod` blocks, OCaml `.ml`+`.mli` pairs)? The former is simpler; the latter is more flexible at scale.

## 3. Numeric tower

What numeric types ship, and how do they relate?

The "numeric tower" — Lisp's term for the inclusion lattice **Integer ⊂ Rational ⊂ Real ⊂ Complex** — is one design extreme. The other is the C/Rust style: a flat set of fixed-width primitives (`i8`, `i16`, `i32`, `i64`, `u8`, …, `f32`, `f64`) with explicit conversion. Most languages live somewhere in between.

**The principal axes:**

- **Integer types.** Fixed-width (`i32`, `i64`, `u64`) like Rust, Go, C, Java, Swift, Zig? Or *arbitrary-precision* like Python (`int` is automatically promoted to bignum on overflow), Scheme, Ruby, Lisp, Haskell `Integer`? Fixed-width is faster, predictable in memory, surface arithmetic overflow as a correctness concern (Rust panics in debug + wraps in release by default — `checked_add` / `wrapping_add` / `saturating_add` are the explicit forms; Zig requires `+%` for wrapping). Bignum integers are slower (heap allocation past machine-word size) but eliminate an entire class of integer-overflow CVEs.
- **Floating point.** **IEEE 754 binary64** (`f64` / `double`) is mandatory in 2026 — every language must have it, every spec must commit to it, every numerics test suite assumes it. **IEEE 754 binary32** (`f32` / `float`) is standard for GPU code, embedded, and ML inference. Specifying which IEEE 754 features are guaranteed (subnormals, signed zero, NaN propagation, the rounding mode) is the design question — Java famously departed from strict IEEE on `strictfp` until JEP 306 (Java 17, 2021) made strict-IEEE the only mode. **2026 mandate: state explicitly that `f32`/`f64` follow IEEE 754-2008 strictly, including subnormals, signed zero, and NaN propagation.** Anything weaker is a footgun masquerading as performance.
- **Decimal / fixed-point.** For money, billing, anywhere `0.1 + 0.2 != 0.3` is a bug not a feature: do you ship a base-10 decimal type? Python's `decimal.Decimal`, Java's `BigDecimal`, C#'s `decimal`, Swift's `Decimal`. The 2026 default: yes, ship one. Even a *good* developer will reach for `f64` to represent a price under deadline pressure; the only counter-measure is making the right type as available as the wrong type.
- **Rational.** Exact rationals `p/q` with `q` reduced. Scheme, Common Lisp, Python (`fractions.Fraction`), Haskell (`Data.Ratio`). Useful for symbolic / scientific code; nearly irrelevant for everyday programming. Optional — ship it if your audience is numerics-heavy, skip it otherwise.
- **Complex.** `a + bi`. Python (`complex` is a built-in!), Julia, Fortran, Scheme. Ship if your language targets numerics; skip otherwise.
- **Promotion rules.** When the user writes `1 + 1.5`, what happens? The Scheme/Python answer: silent promotion `Integer → Real → Complex`. The Rust/Zig answer: type error — you wrote two different types, write the cast. See `TYPE_SYSTEM.md §7` (Type coercion rules) — this section commits to the same rule from the stdlib's side.
- **Overflow behaviour.** What does `i32::MAX + 1` do? **Trap** (Swift default, Rust debug), **wrap** (C unsigned, Rust release default, Go), **saturate** (uncommon as a default, common as an explicit `saturating_add`), or **promote to bignum** (Python, Scheme)? State the default and the opt-out.

## 4. String model

A string in 2026 is **not** a sequence of bytes, and a string is **not** a sequence of code points. It is a sequence of *grapheme clusters* — what the user perceives as "one character" — assembled from Unicode code points, themselves encoded as bytes. Get this layering wrong and you ship `len("👨‍👩‍👧")` returning 7 (it is one grapheme cluster, four code points, 25 UTF-8 bytes).

**Commit on each layer:**

- **Encoding.** UTF-8 (Rust `String`, Go `string`, Swift `String` internally, modern JS engines for storage), UTF-16 (Java `String`, C# `string`, JavaScript spec), UTF-32 (Python 3 `str` *sometimes* — internally PEP 393 picks 1/2/4 byte per char based on highest code point). **2026 default: UTF-8.** Smaller in memory for the bulk of real-world text (ASCII-heavy code, JSON, logs), aligns with the wire format of every protocol you will ever speak (HTTP, JSON, gRPC, SQL).
- **Mutable vs immutable.** Python, Java, C#, JavaScript, Go: strings are **immutable**. Rust: `String` is mutable owned, `&str` is borrowed immutable view, `&mut str` is borrowed mutable view (rare, only for in-place ASCII transforms). C, C++: mutable by default. **2026 default: immutable strings + a separate mutable builder type** (`StringBuilder` in Java/.NET, `String::push_str` in Rust on owned strings). Immutability means strings can be safely shared across threads without locks, hashed once, interned trivially.
- **Indexing semantics.** What does `s[5]` mean? **Byte index** (Rust does not let you write `s[5]` at all — you must use `.as_bytes()[5]` or `.chars().nth(5)` and explicitly pay the linear scan), **code-point index** (Python `s[5]`, with O(1) implementation enabled by PEP 393's fixed-width internal storage), **UTF-16 code-unit index** (JavaScript, Java — leaks the encoding choice into the API forever, hence the `surrogate pair` confusion every JS dev has waded through), **grapheme-cluster index** (Swift `String.Index` — the right answer for user-facing text, with a real cost: indexing is O(n) and the `Index` type is opaque, forcing users to interact via `firstIndex(of:)`, `distance(from:to:)`). **2026 default: byte indexing is the cheap operation, grapheme indexing is the correct operation, and the stdlib must ship *both* with names that make their cost visible.**
- **Unicode normalisation.** Same visible string, two different code-point sequences: `é` as U+00E9 (one code point, "Latin small letter e with acute") versus `e` U+0065 + U+0301 (two code points, "e" + combining acute). The Unicode Standard defines four normalisation forms — **NFC** (canonical composed, the 2026 web default per W3C charmod-norm), **NFD** (canonical decomposed), **NFKC**, **NFKD** (compatibility variants). State which form your stdlib's string-equality `==` operator assumes. **2026 recommendation: do not normalise on equality automatically** (it would be O(n) on every `==`), but ship `str.normalize(form)` (Python, JavaScript ES2015, Swift, Rust via the `unicode-normalization` crate) and document the trap loudly.
- **Grapheme cluster handling.** Iterating "user-perceived characters" requires UAX #29 (Unicode Text Segmentation) plus the latest emoji ZWJ-sequence updates — currently **Unicode 16.0 (released September 2024)** with **Unicode 17.0 expected in late 2025**, both adding new ZWJ sequences for family / professional emoji. Ship a grapheme-iterator (`str.graphemes()` in the Rust `unicode-segmentation` crate, Swift `String.Character`, Python's `regex` library `\X` — Python's *built-in* `re` notably does *not* support graphemes, a long-standing wart). State the Unicode version your stdlib targets and the cadence at which you will track new releases.
- **String literals + interpolation.** `"hello {name}"` (Python f-strings, C# `$"..."`, JS template literals, Rust `format!`/`println!` macros)? Heredocs (`r"raw"`, `"""triple-quoted"""`)? Escape sequences (`\n`, `\u{1F600}`, `\x41`)? Cross-link to `LANGUAGE_GRAMMAR.md` for the *syntax*; this section commits to what the stdlib provides for *runtime* string construction (`format!`, `f"{x}"`, `String.format`, …).

## 5. Collections

The set of container types every program will reach for daily. Ship these well — they are the most-touched stdlib surface, and the names you pick become unmovable.

**Required core:**

- **Sequence / list / vector.** A heap-allocated, growable, integer-indexed sequence. `Vec<T>` (Rust), `list` (Python), `[]T` slice + `append` (Go), `ArrayList<T>` (Java), `Array<T>` (Swift, JS), `vector<T>` (C++). Document the amortised cost (O(1) `push_back`, O(n) `insert` at front), the growth factor (typically 1.5x or 2x), and whether iteration during mutation is detected.
- **Map / dictionary / hash table.** Key-value, hash-based, O(1) average lookup. `HashMap<K, V>` (Rust), `dict` (Python — guaranteed insertion-ordered since 3.7), `map[K]V` (Go), `HashMap<K, V>` / `LinkedHashMap` (Java), `Dictionary<K, V>` (Swift), `Map` (JS). **State whether iteration order is insertion-ordered (Python 3.7+, Go: deliberately randomised, JS Map: insertion-ordered), and the hashing strategy (SipHash for HashDoS-resistance is the 2026 baseline — Rust `std::collections::HashMap` defaults to SipHash-1-3 for exactly this reason).**
- **Set.** Unique-element collection backed by the map type. `HashSet<T>` (Rust), `set` / `frozenset` (Python), `map[T]struct{}` idiom (Go has no first-class set), `HashSet<T>` (Java), `Set<T>` (Swift, JS). If your map is good, your set is nearly free — ship it.

**Common second-tier:**

- **Ordered map / sorted map.** Tree-backed, O(log n) lookup, sorted iteration. `BTreeMap<K, V>` (Rust — actually a B-tree, better cache behaviour than red-black), `OrderedDict` / `sorted dict` from `sortedcontainers` (Python, not in stdlib), `TreeMap<K, V>` (Java), `std::map` (C++). Ship if your audience does range scans / iteration in sorted order; skip otherwise.
- **Deque (double-ended queue).** O(1) push/pop at both ends. `VecDeque<T>` (Rust), `collections.deque` (Python), `ArrayDeque<E>` (Java), `Deque<T>` (Swift). Useful enough that a stdlib without it forces users to roll bad versions.
- **Queue, stack.** Usually the vec/deque double as these; an explicit `Stack` type rarely earns its keep. Concurrent variants (`ConcurrentLinkedQueue`, `crossbeam_channel::unbounded`) are §7 territory.
- **Bitset.** Compact bit-vector. `BitSet` (Java, `roaring` crate in Rust), `bitarray` (Python, not stdlib). Ship if your audience does index-set work.

**Persistent vs mutable:**

- **Mutable collections (the 2026 default):** in-place updates, reference semantics, O(1) `push`. Java, Python, Go, Rust (with explicit `&mut`). What every imperative programmer expects.
- **Persistent / immutable collections:** `cons`-style or HAMT-backed (hash array mapped tries) structures that return a new collection on every "update", sharing structure with the previous version. **Clojure** is the canonical exemplar — `assoc`, `conj`, `update` all return new values; the underlying HAMT shares ~99% of nodes between versions. **Haskell** `Data.Map.Map` is a balanced tree, persistent by construction. **Scala** has both `mutable.Map` and `immutable.Map`, with the immutable family being the language's default. Persistent collections give you cheap snapshots, lock-free concurrency, and undo-stack semantics for free; pay in constant-factor overhead (typically 2-4x for HAMT vs hashmap) and in cache behaviour. If you are doing FP-leaning design (`paradigm = "functional"`), default to persistent; otherwise default to mutable and ship a `freeze` / `Arc<T>` story.

**Built-in literal syntax:**

Decide which collection types get *literal syntax*. `[1, 2, 3]` for a list/array? `{1, 2, 3}` for a set (Python) or a map (JS, Lua)? `{"k": "v"}` for a map (Python, JS)? `#[1, 2, 3]` for a vector vs a list (Clojure)? Cross-link to `LANGUAGE_GRAMMAR.md`. **The 2026 minimum: list literals + map literals + string literals.** Sets are usually one keystroke away (`Set([1,2,3])` is acceptable); other types live behind their constructors.

## 6. I/O surface

What can the user do *to the outside world* from stdlib alone? The shape of this section is downstream of §1 (Inclusion philosophy) — a small-core language ships only the minimum file/stdin/stdout primitives and delegates HTTP/databases to packages; a batteries-included language ships HTTP clients, JSON, SQL drivers in the box.

**The canonical layers:**

- **Standard streams.** `stdin`, `stdout`, `stderr` — every language has these and gets them roughly right. The 2026 design choice is whether they are *line-buffered* by default (the Unix tty heuristic — flush on newline when stdout is a TTY, block-buffer when redirected) or *block-buffered always* (which means `print(x)` in a piped command may surprise the user). Python flushes by default since 3.0; Rust `println!` flushes on `\n` if stdout is a TTY; Go uses block buffering and the user must `bufio.NewWriter` + `Flush` themselves. Document the choice.
- **Filesystem.** Open / read / write / seek / close, file metadata (size, mtime, permissions), directory traversal, symlinks, atomic rename, file locks. Rust's `std::fs` is a tight, opinionated surface; Python's `pathlib` is the 2026 reference design for an object-oriented path API (chainable, immutable, cross-platform via `PurePosixPath` / `PureWindowsPath` shadow types). Ship a `Path` type — `string + string concatenation for paths` is a 1990s mistake.
- **Process / subprocess.** Spawn a subprocess, capture stdout/stderr, send to stdin, wait, signal, kill. Python `subprocess.run`, Rust `std::process::Command`, Go `os/exec.Cmd`, Node `child_process.spawn`. The 2026 design defaults: arguments-as-list (never shell-string concatenation — *every* shell-string concatenation is a CVE), child handle owns the pipes, explicit `.wait()` to reap zombies.
- **Network.** TCP, UDP, Unix sockets, optional TLS. Rust `std::net::TcpStream` (low-level, no TLS — TLS lives in `rustls`/`native-tls` crates per §1's "curated" philosophy); Go `net.Dial` + `crypto/tls` (TLS in stdlib — batteries philosophy); Python `socket` + `ssl` (in stdlib). HTTP, WebSocket, gRPC, DNS-over-anything: usually package-land except in batteries-included stdlibs.

**Sync vs async:**

- **Sync I/O:** the calling thread blocks until the operation completes. Python `open` + `read` (pre-`asyncio`), Rust `std::io::Read` (sync trait), Go `net.Conn.Read` (sync from the user's perspective; the runtime multiplexes on goroutines underneath — the cleanest model in 2026 for "sync code that scales like async"), Java pre-NIO. Simplest mental model; one thread per blocked I/O is fine until you need ten thousand.
- **Async I/O:** non-blocking, yield-points (`await`, `.poll()`), event-loop driven. Python `asyncio` (built into stdlib since 3.4), Rust `async fn` + the choose-your-runtime model (`tokio` / `async-std` / `smol` — *deliberately not in stdlib*; the runtime question is too contested for `std`), JS Promises + `async`/`await`, C# `async`/`await`. The 2026 design tension: async code has *colour* (async functions can call sync but sync cannot call async without blocking) — this is the famous "What Color is Your Function?" problem (Bob Nystrom, 2015) and it has not been solved, only worked around (Go's solution: hide async in the runtime so all code is sync-coloured; Rust's solution: embrace the colour and pay the ergonomics cost; Project Loom's solution for the JVM: virtual threads — *finalised in Java 21 (Sept 2023)* — bring Go's "sync code, async runtime" approach to the JVM).
- **Capability-gated I/O:** I/O is mediated by *capability* values that must be passed explicitly to the functions that need them. **Roc** is the 2026 production-positioned exemplar — every effectful function takes a capability handle (`Stdout`, `File`, `Network`) as an argument; pure functions cannot perform I/O at all because they have no capability to do so. Aligns naturally with effect-typed semantics (cross-ref `SEMANTICS.md §5` and `TYPE_SYSTEM.md §6` Effect types). Powerful for sandboxing, deterministic testing, and security; pays in API verbosity. **Newspeak**, **Pony**, and the object-capability research line are the heritage; Roc is bringing the idea to mass-market language design in 2026.

**2026 note — WasmGC changes the I/O calculus:**

The **WebAssembly 3.0** release (September 2025) finalised the **WasmGC** proposal, providing native garbage-collected reference types at the Wasm runtime layer. Before WasmGC, a GC'd language targeting `wasm32` had to ship its entire GC runtime in the `.wasm` binary — typically 1-2 MB of overhead before any user code. Java's TeaVM, Kotlin/Wasm, Dart-to-Wasm, and OCaml's `wasm_of_ocaml` all paid this tax. After WasmGC (now shipping in Chrome 119+, Firefox 120+, V8, SpiderMonkey, and Wasmtime 23+), GC'd languages can compile to Wasm at *near-zero runtime overhead* — Dart's WasmGC backend (stable in Flutter 3.27, December 2024) ships under 300 KB versus the prior 1.5 MB. **The design implication for {{project.name}}:** if you target Wasm, you can now ship *more* of your I/O surface in stdlib without binary-size guilt, because the GC + collections that used to dominate the Wasm payload are amortised against the runtime's built-in WasmGC primitives. The old rule "Wasm-targeting language → tiny stdlib" no longer applies in 2026; revisit it explicitly.

## 7. Concurrency primitives

What primitives ship in stdlib for parallel and concurrent code? The *semantics* of these primitives live in `SEMANTICS.md §6` (Concurrency model) — this section commits to which *named types* the user can reach for.

**The canonical primitives:**

- **Thread spawn.** `std::thread::spawn` (Rust), `go func() { … }()` (Go — calling it a "goroutine" rather than a "thread" is a deliberate signal about M:N scheduling), `threading.Thread` (Python — historically GIL-throttled until **PEP 703 free-threaded Python** landed in 3.13 *experimental* (Oct 2024) and is on track for 3.14 stable + 3.15 default-on per the rollout schedule), `Thread` (Java — with virtual threads since 21), `Task.detached` / `async let` (Swift's structured concurrency). State whether spawn returns a *handle* that can be joined / cancelled (Rust `JoinHandle`, Java `Thread.join()`), or fires-and-forgets (Go goroutines — no handle, you build your own via channels). The 2026 trend is **structured concurrency** — Swift's `TaskGroup`, Kotlin's `coroutineScope`, Python's `asyncio.TaskGroup` (3.11+), Java's `StructuredTaskScope` (preview in 21, stable in later JDKs) — where child tasks are guaranteed to complete before the parent scope exits. Adopt this if you can; it eliminates an entire class of "where did that thread go?" leaks.
- **Mutexes / locks.** `std::sync::Mutex<T>` (Rust — the data is *inside* the mutex by construction; you cannot access the protected data without locking, which eliminates a class of bugs), `sync.Mutex` (Go — protected data is a sibling field; user discipline required), `threading.Lock` (Python), `synchronized` / `ReentrantLock` (Java). Decide: reentrant (Java default) or non-reentrant (Rust default)? Mutex with associated data (Rust) or bare lock (everyone else)? **The Rust pattern of bundling lock + data is the 2026 state of the art** — if you can ship it, do; if you can't (because your type system isn't expressive enough), document the discipline loudly.
- **RWLocks.** Many readers, one writer. `std::sync::RwLock<T>` (Rust), `sync.RWMutex` (Go), `threading.RLock` (Python is reentrant lock, not RW — Python lacks a standalone RWLock in stdlib), `ReentrantReadWriteLock` (Java). Less load-bearing than people think — modern designs lean on `Arc<T>` + immutable data or on lock-free structures.
- **Atomics.** Word-sized atomic operations: load, store, compare-and-swap, fetch-add. `std::sync::atomic::{AtomicUsize, AtomicBool, ...}` (Rust — with explicit `Ordering` parameter on every operation, the cleanest API), `sync/atomic` (Go), `java.util.concurrent.atomic.*` (Java), `std::atomic<T>` (C++). State whether you expose memory orderings (sequential consistency, acquire/release, relaxed, …) — Rust does (correctly hard); Go's atomic package gives you only sequential consistency (correctly simple).
- **Channels.** Typed message-passing endpoints. **Go** is the 2026 mainstream exemplar — `chan T` is a language primitive with buffered/unbuffered variants, `select` for multiplexing, `close` for completion. Rust ships `std::sync::mpsc::channel` (multi-producer single-consumer, unbounded — and somewhat deprecated; the community uses `crossbeam_channel` and `tokio::sync::mpsc`). State the variants: bounded / unbounded, sync / async, SPSC / MPSC / MPMC. Channels + structured concurrency are the 2026 default for high-level coordination; mutexes are the lower-level primitive you reach for when channels don't fit.
- **Async runtime primitives.** If your language has `async fn` (cross-ref `SEMANTICS.md §6`), the stdlib must commit to: where does the event loop live? Python ships `asyncio` *in* stdlib (single canonical runtime, ten years of evolution to settle on it). Rust ships *no* runtime in stdlib (the runtime question was too contested in 2018-2019; `tokio` won the de facto crown via `crates.io`). Go has the runtime in the language itself (the scheduler is invisible to the user). Decide and commit — this is one of the most consequential calls.

## 8. Time, errors, testing

Three cross-cutting concerns the stdlib must address coherently.

### 8a. Time

**Java's `java.util.Date` shipped in 1995 — mutable, leaked mutability through accessors, conflated instants with calendar dates, ignored time zones, and required `Calendar` for arithmetic.** It became the canonical example of "do not let the first version of your time API survive". The replacement — `java.time.*` (JSR 310, the work of Stephen Colebourne building on Joda-Time) — shipped in **Java 8 (March 2014)**, thirteen years later, and is now widely considered the reference design for a stdlib time API in any language. Read JSR 310 *first*, then design your time module.

**Required types:**

- **Instant / timestamp.** A single moment on the timeline — UTC, no calendar, no zone. `Instant` (Java `java.time.Instant`, Rust `std::time::SystemTime` and `std::time::Instant` — the two-type split is a Rust subtlety: `Instant` is monotonic and non-zoned, `SystemTime` is wall-clock and can move backwards). Pick a precision (nanoseconds is the modern default; PostgreSQL settled on microseconds; some embedded targets are milliseconds).
- **Duration / interval.** Elapsed nanoseconds. `Duration` (Java, Rust `std::time::Duration`, Python `datetime.timedelta`, Go `time.Duration`). Distinguish *durations* (always 86400 seconds, never variable) from *periods* (one calendar month = 28-31 days; one calendar year = 365-366 days) — Java's `Duration` vs `Period` split is the clean version.
- **Calendar date / time / zoned datetime.** `LocalDate` / `LocalTime` / `LocalDateTime` / `ZonedDateTime` / `OffsetDateTime` (the Java 8 hierarchy). Most languages collapse these — Python's `datetime.datetime` is one type with optional `tzinfo`; Rust's `chrono` crate (de facto stdlib) splits them more carefully.
- **Time zones.** Ship a current **IANA tz database** snapshot bundled with the language and a clear update story. The IANA db is updated multiple times per year (currently shipping **tzdata 2024b** as the de-facto baseline for 2026, with **2025a** out and a steady cadence ahead — DST policy in Chile, Mexico, Turkey, Egypt, and others changes more often than people expect). Document how a user updates their zone data without recompiling everything.
- **Monotonic vs wall-clock.** A monotonic clock never goes backwards (used for *measuring elapsed time*); a wall clock can be adjusted by NTP or the user (used for *displaying a timestamp*). Conflating these — using wall clock for `tic`/`toc` — is one of the most common time bugs in production. Rust gets this right by typing them differently; Go's `time.Now()` returns both kinds wrapped (the monotonic reading is preserved through `time.Sub`). State your stdlib's position.

### 8b. Errors

Cross-reference `SEMANTICS.md §7` (Error handling) for the runtime mechanism — exceptions, `Result`, panic-and-recover. This subsection commits to **what's in stdlib to *inspect* an error**:

- **Stack trace capture.** Cheap or expensive? Python captures on `raise` (cheap); Java captures eagerly (somewhat expensive — historically 0.5-5 ms per exception); Rust `std::backtrace::Backtrace` is opt-in via `RUST_BACKTRACE=1` because capture is *slow* (10-100 ms typical, dominated by symbol resolution).
- **Error chains / causes.** Can a higher-level error wrap a lower-level cause? Java `Throwable.getCause()` (since 1.4, 2002), Python `raise X from Y` (since 3.0), Rust `std::error::Error::source()` + the `thiserror` / `anyhow` crates (de facto). **Ship error chaining as a first-class concept** — without it, users invent ad-hoc string-concatenation and lose all structural information.
- **Error context attachment.** Can a user annotate an error with extra context as it propagates? Go's `fmt.Errorf("doing X: %w", err)` (the `%w` verb since Go 1.13), Rust's `anyhow::Context` trait, Java's `addSuppressed`. The 2026 default: yes, with a clear precedence rule when context conflicts.

### 8c. Testing

A 2026 language without an in-stdlib testing story is sending users to npm-style chaos. Ship:

- **Assertion library.** `assert_eq!`, `assert!`, `assert_matches!` (Rust), `assertEqual` (Python `unittest`), `t.Equal` (Go `testing` + de facto `testify`), `assertEquals` (Java JUnit — *not* stdlib, but JUnit is so canonical it might as well be).
- **Test runner.** `cargo test` (Rust — runs `#[test]`-annotated functions), `go test ./...` (Go — runs `Test*` functions in `*_test.go` files), `python -m unittest` / `pytest` (Python — stdlib is `unittest`, but `pytest` is the *de facto* runner — a small-core / batteries lesson worth studying).
- **Property-based testing.** Hypothesis (Python — not stdlib, but ubiquitous), `proptest` and `quickcheck` (Rust — not stdlib), Hedgehog (Haskell). Optional for stdlib but increasingly expected for serious 2026 design — the bug-finding power per LOC is genuinely an order of magnitude over example-based tests.
- **Doc-tests.** Executable examples inside doc comments. Rust's `///` examples are run by `cargo test`; Python's `doctest`; OCaml's `mdx`. The 2026 best-in-class — every public symbol's doc is a tested example.
- **Benchmark harness.** `criterion` (Rust — not stdlib, but the canonical benchmark crate), `go test -bench`, `pytest-benchmark`, JMH (Java). Ship at least a *minimal* timing helper in stdlib (`std::time::Instant::elapsed` is enough); the full benchmark suite can live in package-land.

## 9. What is deliberately NOT in stdlib

The honesty section. Every stdlib should publish an explicit non-inclusion list with rationale — it heads off recurring "why isn't `<X>` in stdlib?" questions and signals to the ecosystem where to invest.

**Worked example — the Rust philosophy applied to a hypothetical {{project.name}}:**

- **JSON parsing — not in stdlib.** Rationale: serde + serde_json have iterated through nine major versions since 2016; if `serde_json` had been in stdlib, the 2018 ergonomic improvements (`#[derive(Deserialize)]` polish), the 2020 zero-copy work, and the 2023 streaming-parser story would all have been blocked by the compiler release cycle. Lives in `crates.io`. Cross-link: see `THIRD_PARTY_INTEGRATIONS.md`.
- **HTTP client — not in stdlib.** Rationale: every API choice (sync vs async, blocking vs streaming bodies, connection pool semantics, TLS backend) is contested and benefits from independent iteration. `reqwest` (high-level async) + `ureq` (sync) + `hyper` (low-level) all coexist; ratifying one in stdlib would freeze the design.
- **Regex engine — opinion split, see your call.** Python ships `re` in stdlib (and pays the cost — `re` is slower than `regex` and supports a different dialect); Rust ships `regex` *outside* stdlib (de facto canonical, written by the same author as `RE2`). The 2026 lesson: if regex performance is core to your audience (text processing, log parsing), shipping a fast Rust-style `regex` *out* of stdlib is fine; users will find it.
- **Async runtime — explicitly out, per §7.** Rationale: the choice between `tokio`, `async-std`, `smol`, `glommio` is workload-specific; stdlib commitment would harm users who picked the other one.
- **Cryptography (high-level) — out; primitives possibly in.** Hashing primitives (SHA-256, BLAKE3) can live in stdlib (fixed-output, audited, slow-moving). High-level constructions (TLS, JWT, OAuth flows) should not — they need to evolve faster than stdlib release cycles and they need third-party audit you cannot supply.
- **GUI framework — out.** A platform decision, not a language decision. Cross-link: `PLATFORMS.md`.
- **Database driver — out.** Per-database driver work; let the ecosystem.

**The principle:** anything that needs to *evolve faster than the language* should live outside stdlib. Anything that is a stable mathematical / OS / encoding primitive (sort, hash, UTF-8 decode, filesystem) belongs in stdlib because freezing its API for a decade is a feature, not a bug.

Cross-link the non-inclusion list to `TOOLCHAIN.md` (the package-manager section) so users see *where* to find the missing pieces, and to `THIRD_PARTY_INTEGRATIONS.md` for the canonical-package guidance.

## 10. Notes for the executor

When `document-author` consumes this template at Phase 4:

1. Substitute every `{{...}}` placeholder from `state.decisions` — `{{project.name}}` in particular. There are several occurrences across §1, §3 (numeric tower scoping), §6, §9 — keep them consistent.
2. Cross-link to `SEMANTICS.md` from §6 (I/O surface — async/sync depends on the evaluation model), §7 (Concurrency primitives — the semantics live in SEMANTICS.md §6), and §8b (Errors — error model lives in SEMANTICS.md §7).
3. Cross-link to `TYPE_SYSTEM.md` from §3 (numeric tower — coercion rules live in TYPE_SYSTEM.md §7), §4 (string model — immutability and ownership semantics) and §6 (capability-gated I/O — effect types live in TYPE_SYSTEM.md §6).
4. Cross-link to `TOOLCHAIN.md` from §1 (curated + first-party package ecosystem requires a package manager), §6 (`reqwest`/`tokio` are package-manager artefacts), and §9 (the "what's NOT in stdlib" list assumes a working package manager to fetch the alternatives from).
5. If `host_runtime == "wasm"`, the §6 WasmGC note is load-bearing — expand it into a paragraph about which {{project.name}} stdlib types can leverage WasmGC reference types directly.
6. If `project.sub_type == "domain_specific_language"` or `"query_language"`, most of §3 (numeric tower) and §7 (concurrency primitives) are not applicable — collapse those sections to a one-line note and expand §4 (the DSL's value-type model) and §6 (which host I/O the DSL exposes).
7. If `paradigm == "functional"`, expect §5 to favour persistent collections by default and §7 to lean on STM / immutable shared state rather than mutex-protected mutable state.
8. Commit subject: `architect(phase-4): generate STDLIB.md`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
