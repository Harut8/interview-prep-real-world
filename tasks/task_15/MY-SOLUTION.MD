1. `validate_type` doesn't handle None (line 23-28)
    - `None` passes no type check (not str, int, etc.) so it returns False — good
    - but the real bug: `None` for a required field with `"type": "string"` should error
    - currently: `{"name": None}` passes the required check (key exists) but fails type check
    - actually this already works — required check is "key in data" (line 45), type check catches None
    - the REAL None bug: `validate_type(None, "object")` → `isinstance(None, dict)` → False, ok
    - BUT: if no `"type"` in field_schema, None values slip through with no error

2. Bool is subclass of int in Python (line 27-28)
    - `isinstance(True, int)` returns `True` in Python
    - `validate_type(True, "integer")` incorrectly passes
    - fix: check bool first, exclude it from integer/number:
        ```
        if expected_type in ("integer", "number") and isinstance(value, bool):
            return False
        ```

3. `validate_enum` uses `in` which relies on `==` (line 33-34)
    - `1 == True` is `True` in Python, `1 == 1.0` is `True`
    - fix: use strict comparison with type check:
        ```
        def validate_enum(value, allowed):
            return any(value is item or (value == item and type(value) is type(item)) for item in allowed)
        ```

4. Nested object validation — not recursive (line 94-96)
    - currently `pass` — does nothing for nested objects
    - fix: recursively call `validate_schema` on the nested value with its sub-schema
    - prepend parent field path to nested errors:
        ```
        if field_schema.get("type") == "object" and isinstance(value, dict):
            nested_errors = validate_schema(value, field_schema)
            for err in nested_errors:
                errors.append(ValidationError(f"{field}.{err.path}", err.message))
        ```

5. Array minItems/maxItems not checked (line 83-91)
    - add before item-level validation:
        ```
        min_items = field_schema.get("minItems", 0)
        max_items = field_schema.get("maxItems", float("inf"))
        if len(value) < min_items:
            errors.append(ValidationError(field, f"Array too short (min {min_items})"))
        if len(value) > max_items:
            errors.append(ValidationError(field, f"Array too long (max {max_items})"))
        ```

6. Pattern validation (regex for strings)
    - add after string length checks:
        ```
        if "pattern" in field_schema:
            import re
            if not re.match(field_schema["pattern"], value):
                errors.append(ValidationError(field, f"Does not match pattern '{field_schema['pattern']}'"))
        ```
    - NOTE: use `re.fullmatch` or anchor with `^...$` — `re.match` only matches start of string

7. Custom validator registration
    - store a registry: `_custom_validators: dict[str, Callable] = {}`
    - register function: `register_validator(name, func)` where func takes (value) → bool or raises
    - in schema: `{"type": "string", "format": "email"}` → looks up `_custom_validators["email"]`
    - call during validation:
        ```
        if "format" in field_schema:
            validator = _custom_validators.get(field_schema["format"])
            if validator and not validator(value):
                errors.append(ValidationError(field, f"Failed '{field_schema['format']}' validation"))
        ```

8. Error reporting with full JSON path
    - currently errors use flat field name ("city" not "address.city")
    - pass `path_prefix` parameter through recursive calls:
        ```
        def validate_schema(data, schema, path_prefix=""):
            ...
            current_path = f"{path_prefix}.{field}" if path_prefix else field
        ```
    - array items: `field[0].name`, nested objects: `address.city`
    - collect ALL errors, not just first (current code already does this — doesn't `continue` after first error... except line 59 does `continue` after type error, which skips constraint checks)

9. Line 59 — `continue` after type error skips further validation
    - if type check fails, all other checks (minLength, minimum, enum) are skipped
    - this is arguably correct (no point checking string length if it's not a string)
    - but means only one error per field is reported for type mismatches

10. `validate_schema` only handles top-level `data` as dict
    - if `data` is not a dict, no error — just returns empty list
    - should validate the root type if schema has `"type": "object"`

11. Tests to write
    - None value on required string field → error
    - `True` is not integer, `True` is boolean
    - enum strict: `1` not in `[True]`, `1.0` not in `[1]`
    - nested object: missing required nested field reports error with path "address.city"
    - deeply nested (3+ levels): errors have correct full path
    - array minItems: empty array with minItems=1 → error
    - array maxItems: 5 items with maxItems=3 → error
    - pattern: email regex matches valid email, rejects invalid
    - custom validator: registered "email" validator called for format="email"
    - custom validator: unregistered format is ignored or errors
    - all errors collected: multiple fields with multiple issues → all reported
    - type error skips constraint checks (line 59 continue behavior)