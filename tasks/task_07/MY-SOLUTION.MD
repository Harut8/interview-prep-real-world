1. For parsing date we should raise ValueError instead of returning None

2. For amount handling in european format
    - rule: whichever separator ("." or ",") appears **last** is the decimal separator
    - "1.234,56" — comma is last → comma = decimal, dots = thousands
        - remove ".", replace "," with "." → "1234.56" → float()
    - "1,234.56" — dot is last → dot = decimal, commas = thousands
        - remove "," → "1234.56" → float()
    - if only one type of separator, treat "," as decimal: replace "," with "." → float()
    - no need for Decimal — Transaction dataclass uses float

3. Generator refactor for memory
    - change function signature: accept file path (or file object), not full string
    - return a generator that yields one Transaction at a time
    - `def read_transactions(file_path: str) -> Generator[Transaction, None, None]:`
    - open file, use csv.DictReader, yield each row as Transaction
    - downstream functions (process_transactions) must also accept iterables, not lists

4. BOM handling
    - use `encoding="utf-8-sig"` when opening the file — strips BOM automatically
    - if keeping string-based API, strip `\ufeff` from the start of content

5. Data validation
    - reject rows where amount is negative → raise ValueError or skip + log
    - reject rows where date is in the future (compare to `date.today()`)
    - validation should happen during read/parse, before processing

6. Summary report generator
    - total amount, count, average, min/max grouped per category
    - single pass through data using a dict of category → running stats
    - `{category: {"count": N, "total": X, "min": X, "max": X, "avg": X}}`

7. SAMPLE_CSV (line 72) is broken
    - "1.234,56" inside CSV without quoting splits into two columns
    - needs to be quoted: `"1.234,56"` so csv parser treats it as one field

8. Tests to write
    - invalid date raises ValueError
    - European amounts: "1.234,56" → 1234.56
    - BOM-prefixed CSV parses correctly
    - empty CSV file → no transactions (no crash)
    - negative amount → rejected by validation
    - future date → rejected by validation
    - summary report correctness per category
    - generator: verify lazy evaluation (doesn't load all rows at once)
