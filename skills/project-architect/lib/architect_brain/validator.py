"""JSON Schema 2020-12 validation for project-architect v8 state files.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT

Provides validate_schema(instance, schema) which returns a list of error
messages (empty list = valid).

Two-tier implementation:

- Stdlib-only path (primary): handles the JSON Schema 2020-12 keywords v8
  uses — type (incl. list-of-types), required, properties, items,
  additionalProperties, enum, const, pattern (regex), minimum, maximum,
  minLength, maxLength, minItems, maxItems, and oneOf/anyOf/allOf
  composition. Fast, zero-dep.

- Optional jsonschema-enhanced path: when ``jsonschema`` >= 4.21 is
  installed AND the schema uses unsupported keywords ($ref, $defs,
  if/then/else, dependencies, format, patternProperties, propertyNames,
  uniqueItems, contains, multipleOf, etc.), falls through to
  ``jsonschema.Draft202012Validator``. Otherwise the stdlib path is
  preferred (faster + zero-dep). A small recursive helper
  (_schema_uses_unsupported) detects this.

Errors include the JSON path to the offending location (e.g.,
``adr.id`` or ``tags[0]``) plus the constraint that failed, so callers
can locate the bad value.

Wave 2.9 will author 11 per-concern state schema fragments. Wave 2.10
will author the ADR frontmatter schema. Wave 5's
check_29_state_schema_valid will use validate_schema to check projection
drift.
"""

from __future__ import annotations

import re
from typing import Any

try:
    import jsonschema  # type: ignore[import-untyped]
    HAS_JSONSCHEMA = True
except ImportError:  # pragma: no cover - exercised only when jsonschema absent
    jsonschema = None  # type: ignore[assignment]
    HAS_JSONSCHEMA = False


# JSON Schema 2020-12 keywords NOT supported by the stdlib path. When any
# of these appear in the schema (recursively), fall through to the
# jsonschema-enhanced path if available.
_UNSUPPORTED_KEYWORDS = frozenset({
    "$ref", "$defs", "$id", "$schema",
    "if", "then", "else", "not",
    "dependencies", "dependentRequired", "dependentSchemas",
    "format", "contentEncoding", "contentMediaType",
    "propertyNames", "patternProperties",
    "uniqueItems", "contains", "minContains", "maxContains",
    "multipleOf",
})


def _schema_uses_unsupported(schema: Any) -> bool:
    """Recursively check whether schema uses keywords stdlib path can't handle."""
    if not isinstance(schema, dict):
        return False
    if any(k in schema for k in _UNSUPPORTED_KEYWORDS):
        return True
    for value in schema.values():
        if isinstance(value, dict) and _schema_uses_unsupported(value):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and _schema_uses_unsupported(item):
                    return True
    return False


def validate_schema(instance: Any, schema: dict) -> list[str]:
    """Validate instance against schema. Returns a list of error messages.

    Empty list means valid. Each error string includes the path to the
    offending location plus the constraint that failed.
    """
    if HAS_JSONSCHEMA and jsonschema is not None and _schema_uses_unsupported(schema):
        validator = jsonschema.Draft202012Validator(schema)
        return [
            f"{'.'.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
            for err in validator.iter_errors(instance)
        ]
    return _validate(instance, schema, path="")


def _validate(instance: Any, schema: dict, path: str) -> list[str]:
    """Recursive stdlib validator."""
    errors: list[str] = []

    # Type check — short-circuits further checks on mismatch to avoid noisy
    # cascades (e.g., applying minLength to an integer).
    if "type" in schema:
        if not _check_type(instance, schema["type"]):
            errors.append(
                f"{path or '<root>'}: type mismatch: expected {schema['type']}, "
                f"got {type(instance).__name__}"
            )
            return errors

    # Composition: oneOf / anyOf / allOf
    if "oneOf" in schema:
        valid_count = sum(
            1 for sub in schema["oneOf"]
            if not _validate(instance, sub, path)
        )
        if valid_count != 1:
            errors.append(
                f"{path or '<root>'}: oneOf: expected exactly 1 match, got {valid_count}"
            )
    if "anyOf" in schema:
        if not any(not _validate(instance, sub, path) for sub in schema["anyOf"]):
            errors.append(f"{path or '<root>'}: anyOf: no schema matched")
    if "allOf" in schema:
        for sub in schema["allOf"]:
            errors.extend(_validate(instance, sub, path))

    # Enum / const
    if "enum" in schema:
        if instance not in schema["enum"]:
            errors.append(
                f"{path or '<root>'}: enum: value {instance!r} not in {schema['enum']}"
            )
    if "const" in schema:
        if instance != schema["const"]:
            errors.append(
                f"{path or '<root>'}: const: value {instance!r} != {schema['const']!r}"
            )

    # String constraints
    if isinstance(instance, str):
        if "pattern" in schema:
            if not re.search(schema["pattern"], instance):
                errors.append(
                    f"{path or '<root>'}: pattern: {instance!r} doesn't match "
                    f"{schema['pattern']!r}"
                )
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(
                f"{path or '<root>'}: minLength: {len(instance)} < {schema['minLength']}"
            )
        if "maxLength" in schema and len(instance) > schema["maxLength"]:
            errors.append(
                f"{path or '<root>'}: maxLength: {len(instance)} > {schema['maxLength']}"
            )

    # Number constraints — exclude bool (Python's bool < int subclass).
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(
                f"{path or '<root>'}: minimum: {instance} < {schema['minimum']}"
            )
        if "maximum" in schema and instance > schema["maximum"]:
            errors.append(
                f"{path or '<root>'}: maximum: {instance} > {schema['maximum']}"
            )

    # Object constraints
    if isinstance(instance, dict):
        if "required" in schema:
            for req in schema["required"]:
                if req not in instance:
                    errors.append(
                        f"{path}.{req}".lstrip(".") + ": required property missing"
                    )
        if "properties" in schema:
            for key, sub_schema in schema["properties"].items():
                if key in instance:
                    sub_path = f"{path}.{key}".lstrip(".")
                    errors.extend(_validate(instance[key], sub_schema, sub_path))
        if "additionalProperties" in schema and schema["additionalProperties"] is False:
            known = set(schema.get("properties", {}).keys())
            for key in instance:
                if key not in known:
                    errors.append(
                        f"{path}.{key}".lstrip(".")
                        + ": additional property not allowed"
                    )

    # Array constraints
    if isinstance(instance, list):
        if "items" in schema:
            for i, item in enumerate(instance):
                errors.extend(_validate(item, schema["items"], f"{path}[{i}]"))
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(
                f"{path or '<root>'}: minItems: {len(instance)} < {schema['minItems']}"
            )
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(
                f"{path or '<root>'}: maxItems: {len(instance)} > {schema['maxItems']}"
            )

    return errors


def _check_type(instance: Any, type_spec: Any) -> bool:
    """Check if instance matches a JSON Schema type spec (str or list)."""
    if isinstance(type_spec, list):
        return any(_check_type(instance, t) for t in type_spec)
    if type_spec == "string":
        return isinstance(instance, str)
    if type_spec == "integer":
        # bool is NOT integer in JSON Schema, despite Python's bool < int.
        return isinstance(instance, int) and not isinstance(instance, bool)
    if type_spec == "number":
        return isinstance(instance, (int, float)) and not isinstance(instance, bool)
    if type_spec == "boolean":
        return isinstance(instance, bool)
    if type_spec == "null":
        return instance is None
    if type_spec == "array":
        return isinstance(instance, list)
    if type_spec == "object":
        return isinstance(instance, dict)
    return False
