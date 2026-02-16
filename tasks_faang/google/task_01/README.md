# Task 01: Text Search Engine

**Time Limit: 60 minutes**

## Overview

You are given a simple text search engine that indexes documents and retrieves them
using TF-IDF ranking. The engine supports adding documents, building an inverted index,
and searching with ranked results.

## Current State

The codebase has a working but buggy implementation of a TF-IDF search engine.
Several tests are failing due to bugs in the core logic.

## Bugs to Fix

There are **3 bugs** in the existing code. Find them by running the tests and
reading the failing test output. The bugs are in the core ranking and indexing logic.

Hints:
1. Look at how IDF is computed — the logarithm base matters for correct scoring.
2. Check how term frequency is calculated — is it fair to longer documents?
3. Examine stop word handling — are stop words treated consistently between
   indexing and querying?

## Features to Implement

After fixing the bugs, implement the following features (see TODO tests):

1. **Phrase Search** — Support quoted phrases like `"exact match"` that require
   terms to appear consecutively in the document in the given order.

2. **Search Result Snippets with Highlighting** — Return a short snippet of the
   document around the matched terms with the matching terms wrapped in `**bold**`
   markers.

3. **Spelling Suggestions** — When a search returns no results, suggest alternative
   queries by finding indexed terms within edit distance 1 of query terms.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Evaluation Criteria

- All existing tests pass after bug fixes
- New feature tests pass
- Code quality and type hints
- Edge case handling
