import pytest
from app import validate_schema, validate_type, validate_enum, ValidationError


def test_valid_simple_object():
    schema = {
        "properties": {"name": {"type": "string"}, "age": {"type": "integer"}},
        "required": ["name"],
    }
    errors = validate_schema({"name": "Alice", "age": 30}, schema)
    assert len(errors) == 0


def test_missing_required():
    schema = {"properties": {"name": {"type": "string"}}, "required": ["name"]}
    errors = validate_schema({}, schema)
    assert len(errors) == 1
    assert "required" in errors[0].message.lower()


# FAILS — fix None handling
def test_none_value_fails_required_type():
    schema = {"properties": {"name": {"type": "string"}}, "required": ["name"]}
    errors = validate_schema({"name": None}, schema)
    assert len(errors) > 0


# FAILS — fix bool/int confusion
def test_boolean_not_integer():
    assert validate_type(True, "integer") is False
    assert validate_type(True, "boolean") is True


# FAILS — fix enum strict comparison
def test_enum_strict():
    assert validate_enum(1, [True, "yes"]) is False  # 1 == True in Python
    assert validate_enum(True, [True, "yes"]) is True


# FAILS — fix nested object validation
def test_nested_object_validation():
    schema = {
        "properties": {
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "zip": {"type": "string"},
                },
                "required": ["city"],
            }
        },
    }
    errors = validate_schema({"address": {"zip": 12345}}, schema)
    assert len(errors) >= 2  # missing city + wrong type for zip


# FAILS — fix array minItems/maxItems
def test_array_constraints():
    schema = {
        "properties": {
            "tags": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3}
        },
    }
    errors = validate_schema({"tags": []}, schema)
    assert len(errors) > 0  # empty array violates minItems


# TODO: Add tests for pattern validation
# TODO: Add tests for custom validators
