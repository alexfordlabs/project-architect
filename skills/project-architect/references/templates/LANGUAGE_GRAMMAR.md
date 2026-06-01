<!-- Author: Alexander Ford <alex@alexfordlabs.com> -->
<!-- License: MIT -->
<!-- Project: project-architect (https://github.com/alexfordlabs/project-architect) -->

---
template_name: LANGUAGE_GRAMMAR
generate_when: project.sub_type in ["general_purpose_language", "domain_specific_language", "query_language", "configuration_language", "educational_language", "transpiler_target"]
required_decisions:
  - project.name
  - project.sub_type
optional_decisions:
  - paradigm
  - impl_strategy
depends_on:
  - PROJECT_OVERVIEW.md
  - TECH_STACK.md
revision_triggers:
  - project.sub_type
  - paradigm
---

# Language grammar — {{project.name}}

This document captures the **surface language design** of {{project.name}}: how source text is tokenized, parsed, and disambiguated. It is the lexer + parser + grammar contract that the rest of the toolchain (formatter, LSP, compiler front-end) must respect.

It is consumed by `document-author` at Phase 4 generation time. Semantics (evaluation, scoping, memory) live in `SEMANTICS.md`; the choice of parser/lexer **library** is committed in `TECH_STACK.md`; this doc describes the **language being parsed**, not the tool doing the parsing.

## 1. Tokenization

Tokens are the atomic input units the parser consumes. Decide each class:

- **Keywords:** the fixed reserved set (see §6 for the policy that produced it). Example: `if`, `else`, `let`, `fn`, `return`.
- **Identifiers:** the lexical shape of names.
  - Start character: `[A-Za-z_]` only? `[\p{XID_Start}_]` (Unicode UAX #31, 2026 default)?
  - Continue characters: `[A-Za-z0-9_]` or `[\p{XID_Continue}]`?
  - Unicode normalisation: NFC at lex time (Rust, Swift) vs raw bytes (C, Go).
  - Case sensitivity: case-sensitive (almost all 2026 languages) vs case-insensitive (SQL, Fortran).
  - Maximum length: unlimited / 1024 / impl-defined.
- **Literals:**
  - **Integer:** decimal `42`; hex `0x2A`; octal `0o52` or `052`; binary `0b101010`. Digit separators `1_000_000` (Rust/Swift/Python 3.6+). Type suffixes `42u64` / `42_i32`. Bigint? Arbitrary-precision by default (Python) or fixed-width with explicit promotion (Rust)?
  - **Float:** `3.14`, `1.5e-10`, `0x1.fp3` (hex float, C99/Rust). NaN/Inf literals? Decimal128 (`1.0d`)?
  - **String:** quote shapes — single `'…'` vs double `"…"` vs both. Escape set: `\n \r \t \\ \" \0 \u{…}` (Unicode code point) / `\x..` (byte). Raw strings: `r"…"` / `r#"…"#` (Rust, escape-free). Multi-line: triple-quoted (Python `"""…"""`), backtick (JS), heredoc (shell). Interpolation: `${…}` (TS), `\(…)` (Swift), `f"{…}"` (Python), `{…}` (Rust `format!`)? **Decide:** interpolation is a parser-level concern, not a lexer hack — design accordingly.
  - **Char / rune:** distinct type? `'a'` syntax? Or just length-1 strings (Python)?
  - **Boolean, null/nil/unit:** what are the literal spellings?
- **Operators + punctuation:** the full set, including multi-character operators (`==`, `!=`, `<=`, `>=`, `&&`, `||`, `::`, `=>`, `->`, `..`, `..=`, `?.`, `??`).
- **Comments:**
  - Line: `//` (C-family) / `#` (Python/shell) / `--` (SQL/Lua/Haskell) / `;` (Lisp).
  - Block: `/* … */` (nestable? Rust yes, C no).
  - **Doc comments:** `///` (Rust outer), `//!` (Rust inner module), `/** … */` (Java/JSDoc), `--|` (Haddock). Doc comments are *tokens with semantic significance*, not whitespace — surface them to the parser so doc generators can find them attached to their declarations.
- **Whitespace:** see §4 for whether it is structurally significant.

### Reserved-words list approach

Two design choices, surfaced here because they affect the lexer:

1. **Fixed reserved set** (Go, C): the keyword list is closed; future versions are stuck with the same set unless they break compatibility.
2. **Context-sensitive / soft keywords** (TypeScript `from`, `of`, `async`; Python `match`, `case` since 3.10): tokens that act as keywords only in specific syntactic positions, otherwise valid identifiers. See §6 for the trade-offs.

## 2. Grammar specification

Pick the formal specification language, then write the grammar.

- **EBNF / BNF:** human-readable; matches most spec documents (W3C, ECMA-262). Tooling is sparse. Best when the spec is the artifact, not an executable parser.
- **PEG (Parsing Expression Grammar):** unambiguous by construction (ordered choice, no left recursion without rewriting); maps directly to recursive descent. 2026 tools: `pest` (Rust), `tree-sitter`'s grammar DSL.
- **LALR(1) / LR(1):** generated parsers (yacc/bison, `lalrpop` Rust, `menhir` OCaml, `happy` Haskell). Best perf, worst error messages.
- **Hand-written recursive descent expressed in code, with EBNF in comments:** the 2026 default for serious compilers (Rust, TypeScript, Swift, Go, Zig). EBNF in the spec; recursive descent in the implementation; the two are kept in sync by review.

For {{project.name}} v0.1, write the **EBNF skeleton** here. Even if the implementation ends up hand-written, having the EBNF in this doc keeps the design honest. Example shape:

```ebnf
Program       = { Item } ;
Item          = FnDecl | LetDecl | TypeDecl ;
FnDecl        = "fn" Ident "(" [ ParamList ] ")" [ "->" Type ] Block ;
Block         = "{" { Statement } [ Expr ] "}" ;
Statement     = LetDecl | ExprStmt | ReturnStmt ;
Expr          = Literal | Ident | BinaryExpr | CallExpr | IfExpr | … ;
…
```

**2026-era preference:** maintain **two grammars** with a clearly-documented relationship.
- A `tree-sitter` grammar for editor parsing (incremental, error-tolerant, used by Zed, Neovim, Helix, Emacs 29+ tree-sitter-mode).
- A separate hand-written or generated parser for the compiler proper (where error quality + AST shape control matter more than incrementality).

These intentionally diverge in error recovery and AST shape. Document the differences here so contributors don't re-derive them.

## 3. Ambiguity resolution

Every non-trivial grammar has ambiguities. Resolve them explicitly here.

### Operator precedence + associativity

Lowest precedence at the top, highest at the bottom (the convention C++ used; Rust reversed it — pick one and stick with it). Example:

| Level | Operators | Associativity | Notes |
|---|---|---|---|
| 1 | `=`, `+=`, `-=`, `*=`, … | right | assignment |
| 2 | `?:` (ternary) | right | or omit entirely |
| 3 | `\|\|` | left | short-circuit |
| 4 | `&&` | left | short-circuit |
| 5 | `==`, `!=` | non-associative | `a == b == c` is an error |
| 6 | `<`, `<=`, `>`, `>=` | non-associative | as above |
| 7 | `\|` | left | bitwise OR |
| 8 | `^` | left | bitwise XOR |
| 9 | `&` | left | bitwise AND |
| 10 | `<<`, `>>` | left | shift |
| 11 | `+`, `-` (binary) | left | additive |
| 12 | `*`, `/`, `%` | left | multiplicative |
| 13 | unary `-`, `!`, `*`, `&` | right | prefix |
| 14 | `.`, `()`, `[]`, `?` | left | postfix / call / index |

**Worked example:** `a + b * c == d && e` parses as `((a + (b * c)) == d) && e`.

### Statement vs expression

- **Expression-oriented** (Rust, Scala, Kotlin): `if`/`match`/`block` are all expressions returning values. Statements are expressions whose value is discarded (semicolon-terminated).
- **Statement-oriented** (C, Java, Go): `if`/`switch`/`for` are statements. Expression context is separate.
- **Hybrid** (Python: expressions are statements, but `if` is a statement; the ternary `x if cond else y` is the expression form).

Decide and document: `if cond { 1 } else { 2 }` — legal as an expression? Block expression `{ let x = …; x + 1 }` — legal in arbitrary expression position?

### Dangling else

`if A then if B then S1 else S2` — does `else S2` bind to the inner or outer `if`?

- **Inner binding** (C, Java, virtually every C-family language): the textually nearest `if`.
- **Outer binding via mandatory `end`** (Pascal, Ruby): explicit terminators eliminate the ambiguity at the grammar level.
- **Mandatory braces** (Rust, Swift, Go): block delimiters required after `if`; ambiguity literally cannot arise.

### `if` chain semantics

- `if … else if … else`: is `else if` a single keyword combination (Swift `else if`), or is it `else` followed by an `if`-expression (Rust, where `else if` works because `if` is an expression)?
- `if let` / `if case let` for pattern-matching conditions: design now or defer to a future RFC.

## 4. Significant whitespace

**Decide:** does indentation carry meaning?

- **No** (C, Rust, Go, Java, JS, Swift): blocks use explicit braces / `begin`-`end` / `do`-`end`. Whitespace is for humans only.
- **Yes — Python-style:** `:` introduces a block; consistent INDENT/DEDENT tokens emitted by a stateful lexer.
- **Yes — Haskell-style off-side rule:** the layout algorithm inserts virtual `{`, `}`, `;` tokens based on column alignment. Considerably more complex than Python's; supports both layout-sensitive and brace-explicit forms.
- **Yes — YAML-style indentation-as-structure:** indentation alone defines nesting, no introducing punctuation. Brittle in practice; avoid unless you are designing a configuration language and have studied YAML's footguns first.

Even if "no", document the convention: tabs vs spaces, recommended indent width, line-length convention (these belong here so the formatter has a spec to implement).

For Python-style: specify whether tabs and spaces may mix, what counts as a continuation line, and how blank lines interact with INDENT/DEDENT. (Python 3 forbids mixed tabs/spaces; do the same.)

For Haskell-style: pick a layout-algorithm reference (Haskell 2010 §10.3 is the canonical citation).

## 5. Error recovery

What does the parser do when it hits a token it didn't expect? Three escalating strategies:

1. **Fail fast (no recovery):** report the first syntax error, abort. Acceptable for v0.1 of a research language; unacceptable for editor tooling.
2. **Panic-mode recovery:** on error, skip tokens until a known synchronisation point (statement-terminating `;`, end-of-line, closing brace, keyword that begins a top-level item). Reset and continue. This is the classic compiler-textbook approach; works adequately for batch compilation.
3. **Resilient / fault-tolerant parsing:** keep parsing as if the missing tokens were inserted. Produce a tree with explicit "missing" / "error" nodes. Required for IDE-grade tooling — rust-analyzer's parser (using `rowan` + Salsa) is the reference implementation; tree-sitter also produces error-tolerant trees by design.

**2026 Rust default:** **`chumsky`** for error-recoverable parser combinators (the standout feature is its `recover_with` combinator and Ariadne-integrated rich diagnostics). For perf-critical hot paths, `winnow` (fork of `nom`); for generated LR(1), `lalrpop`. For tree-sitter integration: `tree-sitter`'s grammar DSL + a thin Rust shim.

Specify here:
- Synchronisation tokens (what brings the parser back to a known state).
- Maximum errors per file before bailing out (or "all of them, never bail out" for editor mode).
- Diagnostic format: simple text vs structured (LSP `DiagnosticRelatedInformation`).

## 6. Reserved word policy

The lexer needs a definitive list. Three approaches with concrete 2026 trade-offs:

| Approach | Exemplar | Trade-off |
|---|---|---|
| Fixed reserved set | Go (25 keywords, frozen since 1.0) | Simplest. Cannot add a keyword without breaking code. Adding `any` to Go required a years-long deprecation cycle. |
| Reserved-on-context (raw identifiers) | Rust (`r#match`, `r#async`) | New keywords can be added across editions. Raw-identifier syntax is mildly ugly but rarely used. |
| Minimal-reserved + soft keywords | TypeScript (`from`, `of`, `async`, `await` in some contexts; `type` is contextual) | Cleanest user-facing syntax. Implementation complexity is moderate (parser must look ahead or track context). |

**Recommendation for new languages:** minimal-reserved + soft keywords + edition-based hard-keyword introduction. This matches Rust's edition system (`edition = "2024"` opts into a wider keyword set) — keeps old code parsing while letting the language evolve.

List the v0.1 reserved set explicitly here. Mark each word as `hard` (always reserved) or `soft` (reserved only in context X).

## 7. Lexer/parser implementation

Last section is implementation-strategy; the choice belongs in `TECH_STACK.md` but the **rationale** belongs here.

| Strategy | When to pick | 2026 representative tools |
|---|---|---|
| Hand-written recursive descent | Most serious new languages. Best error messages; total control over AST shape; predictable performance. | The Rust compiler, TypeScript, Swift, Zig, Go — all hand-written. |
| Parser generator (LR / LALR) | When the grammar is genuinely LALR(1) and you want a machine-checked guarantee against shift/reduce conflicts. | `lalrpop` (Rust), `menhir` (OCaml, Inria), `happy` (Haskell), bison (C). |
| Parser combinators | Prototypes; languages where the grammar evolves rapidly; cases where error-recovery quality matters more than peak perf. | **`chumsky`** (Rust — best error recovery, 2026 default), **`winnow`** (Rust — perf, fork of `nom`), `megaparsec` (Haskell). |
| PEG-based generator | Grammars that are most naturally written as ordered choice; when the spec is also the impl. | `pest` (Rust), `tree-sitter` (cross-language; the editor-tooling default). |
| Editor-side incremental | Required IF you ship an LSP. | **`tree-sitter` v0.26.x** — de-facto incremental parser; default in Zed, Neovim, Helix; built-in in Emacs 29+. Pair it with a separate compiler-side parser; do not try to share. |

**Default recommendation for a 2026 new language:** Rust + hand-written recursive descent for the compiler + `tree-sitter` for editor tooling. Use `chumsky` if the team prefers combinators and is willing to trade some perf for shorter implementation time. Avoid `lalrpop` unless the grammar is provably LALR(1) and you can live with the generic "syntax error" messages.

Cross-link to `TECH_STACK.md §Lexer/Parser library` for the concrete dependency choice.

## Notes for the executor

When `document-author` consumes this template at Phase 4:

1. Substitute every `{{...}}` placeholder from `state.decisions`.
2. If `project.sub_type == "transpiler_target"`, drop section 4 (significant whitespace usually inherits from the host source language) and add a section "Source-language grammar reference" that cites the upstream spec (e.g., ECMA-262 for JS targets, PEP 617 for Python targets).
3. Cross-link to `TECH_STACK.md` for the actual lexer/parser library chosen (per §7). Do not duplicate the library list; reference it.
4. Cross-link to `SEMANTICS.md` for the meaning of parsed expressions (this template is shape-only).
5. Commit: `architect(phase-4): generate LANGUAGE_GRAMMAR.md`.

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
