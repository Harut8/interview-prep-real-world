# String Arithmetic Engine

**Energy-domain flavor — maps to LC 43 Multiply Strings / LC 415 Add Strings.**

Implement arithmetic operations on numbers represented as strings (no big-int libraries).

## Interface

```python
class BigNum:
    def __init__(self, value: str) -> None: ...
    def add(self, other: "BigNum") -> "BigNum": ...
    def subtract(self, other: "BigNum") -> "BigNum": ...
    def multiply(self, other: "BigNum") -> "BigNum": ...
    def __str__(self) -> str: ...
    def __eq__(self, other) -> bool: ...
```

## Requirements

- Numbers can be arbitrarily large (hundreds of digits).
- Support negative numbers.
- No leading zeros in output (except "0" itself).
- No use of `int()` on the full string — only single-digit conversions allowed.
- `add`, `subtract`, `multiply` return new `BigNum` instances.

## Patterns Tested

String manipulation, carry propagation, grade-school multiplication algorithm.

## Time Target: 45 minutes
