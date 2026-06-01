# Semantics

fern — A functional DSL transpiling to JavaScript for declarative UI definitions.

fern is purely functional: programs are referentially transparent pipelines
producing a UI tree. Evaluation is eager and left-to-right at the source
level; the JS emit preserves that order. See ADR-0003 for the paradigm +
type-system rationale.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
