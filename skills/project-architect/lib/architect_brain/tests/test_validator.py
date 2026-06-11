"""Tests for architect_brain.validator — JSON Schema 2020-12 validation.

Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: Apache-2.0
"""

import unittest

from architect_brain.validator import validate_schema


class TestValidateSchemaBasicTypes(unittest.TestCase):

    def test_valid_string(self):
        errors = validate_schema("hello", {"type": "string"})
        self.assertEqual(errors, [])

    def test_invalid_string_when_int_expected(self):
        errors = validate_schema(42, {"type": "string"})
        self.assertEqual(len(errors), 1)
        self.assertIn("type", errors[0])
        self.assertIn("string", errors[0])

    def test_valid_integer(self):
        errors = validate_schema(42, {"type": "integer"})
        self.assertEqual(errors, [])

    def test_integer_rejects_float(self):
        errors = validate_schema(3.14, {"type": "integer"})
        self.assertEqual(len(errors), 1)

    def test_valid_number_accepts_int_and_float(self):
        self.assertEqual(validate_schema(42, {"type": "number"}), [])
        self.assertEqual(validate_schema(3.14, {"type": "number"}), [])

    def test_valid_boolean(self):
        self.assertEqual(validate_schema(True, {"type": "boolean"}), [])
        self.assertEqual(validate_schema(False, {"type": "boolean"}), [])

    def test_boolean_rejects_int(self):
        """In JSON Schema, bool != int (despite Python's bool < int)."""
        errors = validate_schema(1, {"type": "boolean"})
        self.assertEqual(len(errors), 1)

    def test_integer_rejects_bool(self):
        """JSON Schema: integer rejects bool (Python's bool < int subclass)."""
        self.assertEqual(len(validate_schema(True, {"type": "integer"})), 1)

    def test_number_rejects_bool(self):
        self.assertEqual(len(validate_schema(True, {"type": "number"})), 1)

    def test_valid_null(self):
        self.assertEqual(validate_schema(None, {"type": "null"}), [])

    def test_null_rejects_other(self):
        errors = validate_schema("not null", {"type": "null"})
        self.assertEqual(len(errors), 1)

    def test_type_list_allows_multiple(self):
        """type: ['string', 'null'] accepts both."""
        schema = {"type": ["string", "null"]}
        self.assertEqual(validate_schema("hi", schema), [])
        self.assertEqual(validate_schema(None, schema), [])
        self.assertEqual(len(validate_schema(42, schema)), 1)


class TestValidateSchemaRequired(unittest.TestCase):

    def test_object_with_all_required_props(self):
        schema = {
            "type": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
            },
        }
        instance = {"id": "0007", "title": "Use Next.js"}
        self.assertEqual(validate_schema(instance, schema), [])

    def test_object_missing_required_prop(self):
        schema = {
            "type": "object",
            "required": ["id", "title"],
            "properties": {"id": {"type": "string"}, "title": {"type": "string"}},
        }
        instance = {"id": "0007"}
        errors = validate_schema(instance, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("title", errors[0])
        self.assertIn("required", errors[0].lower())


class TestValidateSchemaArrays(unittest.TestCase):

    def test_array_of_strings(self):
        schema = {"type": "array", "items": {"type": "string"}}
        self.assertEqual(validate_schema(["a", "b"], schema), [])

    def test_array_with_wrong_item_type(self):
        schema = {"type": "array", "items": {"type": "string"}}
        errors = validate_schema(["a", 42], schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("[1]", errors[0])  # path indicates index 1

    def test_minItems_violation(self):
        schema = {"type": "array", "items": {"type": "string"}, "minItems": 2}
        errors = validate_schema(["a"], schema)
        self.assertEqual(len(errors), 1)


class TestValidateSchemaEnum(unittest.TestCase):

    def test_valid_enum_value(self):
        schema = {"enum": ["Accepted", "Proposed", "Rejected"]}
        self.assertEqual(validate_schema("Accepted", schema), [])

    def test_invalid_enum_value(self):
        schema = {"enum": ["Accepted", "Proposed", "Rejected"]}
        errors = validate_schema("Unknown", schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("enum", errors[0].lower())


class TestValidateSchemaPattern(unittest.TestCase):

    def test_valid_pattern(self):
        schema = {"type": "string", "pattern": r"^\d{4}$"}
        self.assertEqual(validate_schema("0007", schema), [])

    def test_invalid_pattern(self):
        schema = {"type": "string", "pattern": r"^\d{4}$"}
        errors = validate_schema("ABC", schema)
        self.assertEqual(len(errors), 1)


class TestValidateSchemaNested(unittest.TestCase):

    def test_nested_object_validation(self):
        schema = {
            "type": "object",
            "required": ["adr"],
            "properties": {
                "adr": {
                    "type": "object",
                    "required": ["id", "status"],
                    "properties": {
                        "id": {"type": "string", "pattern": r"^\d{4}$"},
                        "status": {"enum": ["Accepted", "Proposed", "Rejected"]},
                    },
                }
            },
        }
        valid = {"adr": {"id": "0007", "status": "Accepted"}}
        self.assertEqual(validate_schema(valid, schema), [])

        invalid = {"adr": {"id": "abc", "status": "Bogus"}}
        errors = validate_schema(invalid, schema)
        self.assertEqual(len(errors), 2)
        # Errors should reference the nested path
        for err in errors:
            self.assertIn("adr.", err)


class TestValidateSchemaErrorMessages(unittest.TestCase):

    def test_error_message_includes_path(self):
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
        }
        instance = {"name": 42}
        errors = validate_schema(instance, schema)
        self.assertEqual(len(errors), 1)
        self.assertIn("name", errors[0])


if __name__ == "__main__":
    unittest.main()
