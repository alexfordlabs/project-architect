# Type System

lume uses a dynamic type system for v0.1 (see ADR-0003). Values carry their
type tag at runtime; the interpreter performs type checks at each primitive
operation and raises a TypeError on mismatch. A gradual-typing RFC is tracked
for a later release.

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
