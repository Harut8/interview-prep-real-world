from typing import Any


class ValidationError:
    def __init__(self, path: str, message: str):
        self.path = path
        self.message = message

    def __repr__(self):
        return f"ValidationError({self.path}: {self.message})"


def validate_type(value: Any, expected_type: str) -> bool:
    """Check if value matches expected JSON schema type."""
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    # BUG: doesn't handle None values
    expected = type_map.get(expected_type)
    if expected is None:
        return False
    # BUG: bool is a subclass of int in Python — `True` passes as integer
    return isinstance(value, expected)


def validate_enum(value: Any, allowed: list) -> bool:
    """Check if value is one of the allowed values."""
    # BUG: uses == which can match 1 == True, 1 == 1.0
    return value in allowed


def validate_schema(data: dict, schema: dict) -> list[ValidationError]:
    """Validate a dictionary against a JSON schema."""
    errors = []
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(ValidationError(field, f"Required field '{field}' is missing"))

    # Validate each property
    for field, field_schema in properties.items():
        if field not in data:
            continue

        value = data[field]

        # Type validation
        if "type" in field_schema:
            if not validate_type(value, field_schema["type"]):
                errors.append(ValidationError(field, f"Expected type '{field_schema['type']}'"))
                continue

        # String constraints
        if field_schema.get("type") == "string" and isinstance(value, str):
            min_len = field_schema.get("minLength", 0)
            max_len = field_schema.get("maxLength", float("inf"))
            if len(value) < min_len:
                errors.append(ValidationError(field, f"String too short (min {min_len})"))
            if len(value) > max_len:
                errors.append(ValidationError(field, f"String too long (max {max_len})"))

        # Number constraints
        if field_schema.get("type") in ("integer", "number"):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                errors.append(ValidationError(field, f"Value below minimum {field_schema['minimum']}"))
            if "maximum" in field_schema and value > field_schema["maximum"]:
                errors.append(ValidationError(field, f"Value above maximum {field_schema['maximum']}"))

        # Enum validation
        if "enum" in field_schema:
            if not validate_enum(value, field_schema["enum"]):
                errors.append(ValidationError(field, f"Value not in allowed enum"))

        # Array validation
        if field_schema.get("type") == "array" and isinstance(value, list):
            # BUG: doesn't check minItems/maxItems
            items_schema = field_schema.get("items")
            if items_schema:
                for i, item in enumerate(value):
                    if "type" in items_schema and not validate_type(item, items_schema["type"]):
                        errors.append(ValidationError(
                            f"{field}[{i}]", f"Expected type '{items_schema['type']}'"
                        ))

        # Nested object validation
        if field_schema.get("type") == "object" and isinstance(value, dict):
            # BUG: doesn't recursively validate nested objects
            pass

    return errors


# TODO: Add pattern validation (regex)
# TODO: Add custom validator registration
# TODO: Fix error reporting to include full JSON path for nested errors
