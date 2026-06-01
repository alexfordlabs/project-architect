# Type System

fern — A functional DSL transpiling to JavaScript for declarative UI definitions.

fern uses a static gradual type system with row polymorphism (see ADR-0003).
Typed regions are checked at compile time; `dynamic` boundaries opt fragments
out of inference and re-enter through explicit casts. Types are fully erased
during JS emit — they exist for safety, not runtime cost.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
