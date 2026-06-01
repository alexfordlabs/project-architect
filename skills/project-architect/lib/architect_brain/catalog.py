"""Declarative document catalog: load + conditions DSL + topological sort.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Replaces v7's prose ``document-catalog.md``. The catalog (``references/
catalog.json``) declares, per document: ``conditions`` (a conditions-DSL
expression list deciding whether to generate it), ``depends_on`` (topological
ordering), and metadata (template, producing agent, phase, concern).

Module surface, built across Wave 3:
  load_catalog(path)                 — JSON-load + schema + per-document validate
  tokenize(expr) / parse_condition(expr)  — conditions DSL front-end
  eval_condition(expr, flat_index)   — evaluate against 99-flat-index decisions
  filter_applicable(catalog, flat_index)  — applicable subset (conditions truthy)
  topo_sort(documents)               — Kahn's algorithm, stable (alpha tiebreak)
  detect_cycles(documents)           — concrete cycle witness, or []
"""

from __future__ import annotations

import bisect
import json
import re
from pathlib import Path
from typing import Any, NamedTuple

from architect_brain.validator import validate_schema


class CatalogError(Exception):
    """Base error for catalog load/validation problems."""


def _schema_path() -> Path:
    """Resolve references/schemas/catalog-v4.json relative to this module."""
    return (
        Path(__file__).resolve().parents[2]
        / "references" / "schemas" / "catalog-v4.json"
    )


# Per-document required shape. Validated against each documents[name] via the
# shared validate_schema primitive (zero-dep, same path as state projections).
_DOCUMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": [
        "conditions", "depends_on", "produces",
        "produced_by", "template", "phase", "concern",
    ],
    "properties": {
        "conditions": {"type": "array", "items": {"type": "string"}, "minItems": 1},
        "depends_on": {"type": "array", "items": {"type": "string"}},
        "produces": {"type": "array", "items": {"type": "string"}},
        "produced_by": {"type": "string"},
        "template": {"type": "string"},
        "phase": {"type": "string"},
        "concern": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
}


def load_catalog(path: Path) -> dict[str, Any]:
    """Load + validate a catalog.json file. Raise CatalogError on any problem.

    Validates the top-level envelope against catalog-v4.json, then validates
    every document entry against ``_DOCUMENT_SCHEMA``. All errors are collected
    and reported together so an author sees every problem in one pass.
    """
    try:
        raw = Path(path).read_text(encoding="utf-8")
        catalog = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogError(f"cannot load catalog {path}: {exc}") from exc

    schema = json.loads(_schema_path().read_text(encoding="utf-8"))
    errors = list(validate_schema(catalog, schema))

    documents = catalog.get("documents", {})
    if isinstance(documents, dict):
        for name, doc in documents.items():
            for err in validate_schema(doc, _DOCUMENT_SCHEMA):
                errors.append(f"documents.{name}.{err}")

    if errors:
        raise CatalogError(
            f"catalog {path} is invalid:\n  " + "\n  ".join(errors)
        )
    return catalog


class ConditionError(CatalogError):
    """A conditions-DSL expression failed to tokenize, parse, or evaluate."""


class Token(NamedTuple):
    kind: str      # KEY | OP | LIT | KW | LPAREN | RPAREN | LBRACKET | RBRACKET | COMMA
    value: Any


_KEYWORDS = frozenset({"ALWAYS", "AND", "OR", "IN", "NOT", "EXISTS"})

# Ordered alternation. Leading bare \s+ is the skip branch (lastgroup is None).
_TOKEN_RE = re.compile(
    r"""
      \s+
    | (?P<NEQ>!=)
    | (?P<EQ>==)
    | (?P<GT>>)
    | (?P<LT><)
    | (?P<LPAREN>\()
    | (?P<RPAREN>\))
    | (?P<LBRACKET>\[)
    | (?P<RBRACKET>\])
    | (?P<COMMA>,)
    | (?P<STRING>'[^']*'|"[^"]*")
    | (?P<NUMBER>-?\d+\.\d+|-?\d+)
    | (?P<WORD>[A-Za-z_][A-Za-z0-9_.]*)
    """,
    re.VERBOSE,
)

_OP_GROUPS = {"NEQ": "!=", "EQ": "==", "GT": ">", "LT": "<"}
_PUNCT_GROUPS = {
    "LPAREN": "(", "RPAREN": ")", "LBRACKET": "[", "RBRACKET": "]", "COMMA": ",",
}


def tokenize(expr: str) -> list[Token]:
    """Lex a conditions-DSL expression into a flat token list.

    Disambiguation: UPPERCASE words are keywords; lowercase ``true``/``false``/
    ``null`` are literals; every other word (single or dotted) is a key.
    ``NOT IN`` / ``NOT EXISTS`` are emitted as separate ``NOT`` + ``IN`` /
    ``EXISTS`` tokens and recombined by the parser.
    """
    tokens: list[Token] = []
    pos, n = 0, len(expr)
    while pos < n:
        m = _TOKEN_RE.match(expr, pos)
        if not m:
            raise ConditionError(f"unexpected character at {pos}: {expr[pos]!r}")
        pos = m.end()
        group = m.lastgroup
        if group is None:          # whitespace skip
            continue
        text = m.group()
        if group in _OP_GROUPS:
            tokens.append(Token("OP", _OP_GROUPS[group]))
        elif group in _PUNCT_GROUPS:
            tokens.append(Token(group, _PUNCT_GROUPS[group]))
        elif group == "STRING":
            tokens.append(Token("LIT", text[1:-1]))
        elif group == "NUMBER":
            tokens.append(Token("LIT", float(text) if "." in text else int(text)))
        else:  # WORD
            if text in _KEYWORDS:
                tokens.append(Token("KW", text))
            elif text == "true":
                tokens.append(Token("LIT", True))
            elif text == "false":
                tokens.append(Token("LIT", False))
            elif text == "null":
                tokens.append(Token("LIT", None))
            else:
                tokens.append(Token("KEY", text))
    return tokens


def parse_condition(expr: str) -> tuple:
    """Parse a conditions-DSL expression string into an AST tuple."""
    tokens = tokenize(expr)
    if not tokens:
        raise ConditionError("empty condition expression")
    parser = _Parser(tokens)
    node = parser._or()
    if parser.pos != len(tokens):
        raise ConditionError(f"unexpected trailing tokens: {tokens[parser.pos:]}")
    return node


class _Parser:
    """Recursive-descent parser. Grammar (lowest→highest precedence):

        or_expr    := and_expr (OR and_expr)*
        and_expr   := comparison (AND comparison)*
        comparison := ALWAYS
                    | '(' or_expr ')'
                    | EXISTS key
                    | NOT EXISTS key
                    | key ('==' | '!=' | '>' | '<') literal
                    | key IN list
                    | key NOT IN list
    """

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def _or(self) -> tuple:
        node = self._and()
        while self._peek() == Token("KW", "OR"):
            self._advance()
            node = ("or", node, self._and())
        return node

    def _and(self) -> tuple:
        node = self._comparison()
        while self._peek() == Token("KW", "AND"):
            self._advance()
            node = ("and", node, self._comparison())
        return node

    def _comparison(self) -> tuple:
        tok = self._peek()
        if tok is None:
            raise ConditionError("unexpected end of expression")
        if tok == Token("KW", "ALWAYS"):
            self._advance()
            return ("always",)
        if tok == Token("LPAREN", "("):
            self._advance()
            node = self._or()
            if self._peek() != Token("RPAREN", ")"):
                raise ConditionError("expected ')'")
            self._advance()
            return node
        if tok == Token("KW", "EXISTS"):
            self._advance()
            return ("exists", self._expect_key())
        if tok == Token("KW", "NOT"):
            self._advance()
            if self._peek() != Token("KW", "EXISTS"):
                raise ConditionError("expected EXISTS after prefix NOT")
            self._advance()
            return ("not_exists", self._expect_key())
        if tok.kind == "KEY":
            key = self._advance().value
            return self._comparison_tail(key)
        raise ConditionError(f"unexpected token {tok!r}")

    def _comparison_tail(self, key: str) -> tuple:
        op = self._peek()
        if op is None:
            raise ConditionError(f"expected operator after key {key!r}")
        if op == Token("KW", "NOT"):
            self._advance()
            if self._peek() != Token("KW", "IN"):
                raise ConditionError("expected IN after NOT (infix)")
            self._advance()
            return ("cmp", "NOT IN", key, self._list())
        if op == Token("KW", "IN"):
            self._advance()
            return ("cmp", "IN", key, self._list())
        if op.kind == "OP":
            self._advance()
            if op.value in (">", "<"):
                return ("cmp", op.value, key, self._expect_number())
            return ("cmp", op.value, key, self._expect_literal())
        raise ConditionError(f"expected operator after key {key!r}, got {op!r}")

    def _list(self) -> list:
        if self._peek() != Token("LBRACKET", "["):
            raise ConditionError("expected '[' to start list")
        self._advance()
        items: list = []
        if self._peek() == Token("RBRACKET", "]"):
            self._advance()
            return items
        items.append(self._expect_literal())
        while self._peek() == Token("COMMA", ","):
            self._advance()
            items.append(self._expect_literal())
        if self._peek() != Token("RBRACKET", "]"):
            raise ConditionError("expected ']' to close list")
        self._advance()
        return items

    def _expect_literal(self) -> Any:
        tok = self._peek()
        if tok is None or tok.kind != "LIT":
            raise ConditionError(f"expected literal, got {tok!r}")
        return self._advance().value

    def _expect_number(self) -> Any:
        value = self._expect_literal()
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ConditionError(f"expected number for > / <, got {value!r}")
        return value

    def _expect_key(self) -> str:
        tok = self._peek()
        if tok is None or tok.kind != "KEY":
            raise ConditionError(f"expected key, got {tok!r}")
        return self._advance().value


def eval_condition(expr: str, flat_index: dict[str, Any]) -> bool:
    """Evaluate a conditions-DSL expression against a flat-index projection.

    Dotted keys resolve by direct lookup in ``flat_index['decisions']`` (the
    keys are stored flat — the whole dotted string is one dict key). A missing
    key reads as ``None``.
    """
    ast = parse_condition(expr)
    decisions = flat_index.get("decisions", {}) if isinstance(flat_index, dict) else {}
    return _eval_ast(ast, decisions)


def _eval_ast(node: tuple, decisions: dict[str, Any]) -> bool:
    op = node[0]
    if op == "always":
        return True
    if op == "exists":
        return node[1] in decisions and decisions[node[1]] is not None
    if op == "not_exists":
        return not (node[1] in decisions and decisions[node[1]] is not None)
    if op == "and":
        return _eval_ast(node[1], decisions) and _eval_ast(node[2], decisions)
    if op == "or":
        return _eval_ast(node[1], decisions) or _eval_ast(node[2], decisions)
    if op == "cmp":
        _, cmp_op, key, operand = node
        actual = decisions.get(key)
        if cmp_op == "==":
            return actual == operand
        if cmp_op == "!=":
            return actual != operand
        if cmp_op == "IN":
            return actual in operand
        if cmp_op == "NOT IN":
            return actual not in operand
        if cmp_op in (">", "<"):
            if not isinstance(actual, (int, float)) or isinstance(actual, bool):
                return False
            return actual > operand if cmp_op == ">" else actual < operand
    raise ConditionError(f"cannot evaluate AST node {node!r}")


def filter_applicable(
    catalog: dict[str, Any], flat_index: dict[str, Any]
) -> dict[str, Any]:
    """Return the subset of catalog documents whose conditions evaluate truthy.

    Each document's ``conditions`` list is space-joined into one expression
    (see module note). The returned dict preserves catalog insertion order.
    """
    documents = catalog.get("documents", {})
    applicable: dict[str, Any] = {}
    for name, doc in documents.items():
        clauses = doc.get("conditions", ["ALWAYS"])
        expr = " ".join(clauses).strip() or "ALWAYS"
        if eval_condition(expr, flat_index):
            applicable[name] = doc
    return applicable


class CycleError(CatalogError):
    """The document dependency graph contains a cycle."""


def _restrict_deps(documents: dict[str, Any]) -> dict[str, list[str]]:
    """depends_on restricted to dependencies that are IN the document set.

    A dependency on a document excluded by conditions is dropped (the dependent
    becomes a root w.r.t. that edge) — per spec §3.5 step 3.
    """
    names = set(documents)
    return {
        n: [d for d in documents[n].get("depends_on", []) if d in names]
        for n in documents
    }


def topo_sort(documents: dict[str, Any]) -> list[str]:
    """Kahn's algorithm with a stable alphabetical tiebreak. Raise CycleError.

    Edge semantics: ``A depends_on B`` is an edge B -> A (B must come first).
    Among nodes simultaneously ready (in-degree 0), the alphabetically smallest
    name is emitted first, making the ordering deterministic.
    """
    deps = _restrict_deps(documents)
    indegree = {n: len(deps[n]) for n in documents}
    dependents: dict[str, list[str]] = {n: [] for n in documents}
    for n in documents:
        for d in deps[n]:
            dependents[d].append(n)

    ready = sorted(n for n in documents if indegree[n] == 0)
    order: list[str] = []
    while ready:
        node = ready.pop(0)
        order.append(node)
        for m in dependents[node]:
            indegree[m] -= 1
            if indegree[m] == 0:
                bisect.insort(ready, m)

    if len(order) != len(documents):
        remaining = sorted(n for n in documents if n not in set(order))
        raise CycleError(f"dependency cycle among documents: {remaining}")
    return order


def detect_cycles(documents: dict[str, Any]) -> list[str]:
    """Return ONE concrete dependency cycle as a node path, or [] if acyclic.

    DFS with white/grey/black coloring; on encountering a grey node, returns the
    grey-stack slice from that node to the current node plus the node again, so
    the witness reads e.g. ``['A', 'B', 'C', 'A']``. Deterministic: nodes are
    visited in sorted order. Dependencies outside the document set are ignored.
    """
    deps = _restrict_deps(documents)
    WHITE, GREY, BLACK = 0, 1, 2
    color = {n: WHITE for n in documents}
    stack: list[str] = []

    def _dfs(u: str) -> list[str] | None:
        color[u] = GREY
        stack.append(u)
        for v in deps[u]:
            if color[v] == GREY:
                return stack[stack.index(v):] + [v]
            if color[v] == WHITE:
                found = _dfs(v)
                if found is not None:
                    return found
        stack.pop()
        color[u] = BLACK
        return None

    for n in sorted(documents):
        if color[n] == WHITE:
            found = _dfs(n)
            if found is not None:
                return found
    return []
