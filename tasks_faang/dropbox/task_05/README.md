# Task 05: File Search Index

## Overview
You are building a file search and indexing system similar to Dropbox's search functionality. The system indexes file names and content, supports various query types, and ranks results by relevance.

**Time Limit: 60 minutes**

## Architecture
- `SearchIndex` maintains an inverted index mapping tokens to documents
- `IndexedDocument` represents an indexed file with metadata
- `SearchResult` contains ranked search results with relevance scores
- `Tokenizer` handles text preprocessing and token extraction
- Supports indexing both file names and file content

## Bugs to Fix (3)

1. **Index Not Updated on Rename/Move**: When a file is renamed or moved, the old path remains in the index and the new path is not indexed. Searching for the old name still returns results, while the new name is not searchable.

2. **Search Ranking Doesn't Boost Exact Matches**: The ranking algorithm scores results purely by token frequency (TF). An exact match of the query in the file name should be boosted significantly, but it currently receives the same score as a partial match in content.

3. **Tokenizer Doesn't Split CamelCase or snake_case**: The tokenizer splits on whitespace and punctuation but fails to split identifiers like "getUserName" into ["get", "user", "name"] or "file_upload_manager" into ["file", "upload", "manager"].

## Features to Implement (3)

1. **Fuzzy Search**: Implement fuzzy matching that finds results even with typos. Use edit distance (Levenshtein) with a configurable max distance.

2. **Search Filters**: Support filtering results by:
   - File type/extension (e.g., `.py`, `.txt`)
   - Modification date range
   - File size range

3. **Search Result Highlighting**: When returning results, highlight (surround with `**`) the matched terms in the content snippet.

## Running Tests
```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Files
- `app.py` — Search index implementation
- `tests/test_app.py` — Test suite
- `requirements.txt` — Dependencies
