# Bootstrap Plan

fern — A functional DSL transpiling to JavaScript for declarative UI definitions.

v0.1 implementation strategy: transpiler on a js_host runtime (ES2026 emit).
Bootstrap order: lexer → parser → AST → type-checker → JS code emitter → CLI.
See ADR-0001 (host language) and ADR-0002 (impl strategy + emit target).

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
