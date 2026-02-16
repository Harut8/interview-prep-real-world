# Task 15: JSON Schema Validator — Fix Validation Logic & Add Custom Rules

**Time limit: 60 minutes**

## Existing Codebase
A simplified JSON Schema validator that validates Python dictionaries against schema definitions.

## Problems to Fix
1. The `validate_type` function doesn't handle `None` values correctly — should fail for required fields.
2. Nested object validation is not recursive — only validates one level deep.
3. The `validate_enum` function uses `==` for comparison but fails with mixed types (e.g., `1` vs `1.0`).
4. Array validation doesn't check `minItems` / `maxItems` constraints.

## Features to Implement
1. Add support for `pattern` validation (regex matching for strings).
2. Add custom validator registration: users can register functions like `validate_email`, `validate_phone`.
3. Add proper error reporting: return all validation errors (not just the first one), with JSON path.
4. Write tests for all validation rules.

## What We Evaluate
- Recursive algorithm design
- Error accumulation pattern
- Regex handling
- Clean API design
