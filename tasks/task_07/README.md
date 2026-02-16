# Task 07: CSV Data Pipeline — Fix Processing Bugs & Add Validation

**Time limit: 60 minutes**

## Existing Codebase
A data pipeline that reads CSV files, processes/transforms records, and outputs results. Used for processing user transaction data.

## Problems to Fix
1. The CSV reader doesn't handle files with BOM (byte order mark) — first column name has garbage prefix.
2. The `parse_amount` function fails on European number formats (comma as decimal separator: "1.234,56").
3. Memory issue: the pipeline loads the entire file into memory. Refactor to use generators.
4. The date parser silently returns None for invalid dates instead of raising an error.

## Features to Implement
1. Add data validation: reject rows where amount is negative or date is in the future.
2. Add a summary report generator: total amount, count, average, min/max per category.
3. Write tests including edge cases (empty file, malformed data, huge numbers).

## What We Evaluate
- File I/O handling
- Generator/iterator patterns
- Data validation
- Edge case handling
