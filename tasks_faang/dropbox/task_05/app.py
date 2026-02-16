"""
File Search Index - Index and search files by name and content.

Simulates Dropbox-style full-text search with inverted indexing,
relevance ranking, and query processing.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Optional


@dataclass
class IndexedDocument:
    """Represents an indexed file."""
    path: str
    file_name: str
    content: str
    size: int
    modified_at: datetime
    extension: str
    token_counts: dict[str, int] = field(default_factory=dict)


@dataclass
class SearchResult:
    """A single search result with relevance score."""
    path: str
    file_name: str
    score: float
    snippet: str = ""
    highlighted_snippet: str = ""


@dataclass
class SearchFilter:
    """Filters to narrow search results."""
    extension: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    modified_after: Optional[datetime] = None
    modified_before: Optional[datetime] = None


class Tokenizer:
    """
    Text tokenizer for search indexing.

    BUG #3: Does not handle CamelCase or snake_case splitting.
    "getUserName" is indexed as one token instead of ["get", "user", "name"].
    "file_upload_manager" is split by underscore in punctuation, but the
    current regex doesn't treat underscore as a split point.
    """

    @staticmethod
    def tokenize(text: str) -> list[str]:
        """
        Split text into searchable tokens.

        BUG #3: Only splits on whitespace and basic punctuation.
        Does NOT handle:
        - CamelCase: "getUserName" -> ["get", "user", "name"]
        - snake_case: "file_upload_manager" -> ["file", "upload", "manager"]
        """
        # Simple split on non-alphanumeric characters (keeps underscores as part of tokens)
        tokens = re.findall(r'[a-zA-Z0-9_]+', text.lower())
        return tokens

    @staticmethod
    def split_camel_case(text: str) -> list[str]:
        """
        Split CamelCase text into words.
        This helper exists but is NOT called by tokenize().
        """
        words = re.sub(r'([A-Z])', r' \1', text).split()
        return [w.lower().strip() for w in words if w.strip()]


class SearchIndex:
    """
    Inverted index for file search.

    Maps tokens to the documents that contain them, with
    TF-IDF scoring for relevance ranking.
    """

    def __init__(self):
        # token -> set of document paths
        self._inverted_index: dict[str, set[str]] = {}
        # path -> IndexedDocument
        self._documents: dict[str, IndexedDocument] = {}
        self._tokenizer = Tokenizer()

    def index_document(self, path: str, content: str, modified_at: datetime | None = None) -> None:
        """Index a file by path and content."""
        file_name = path.rsplit("/", 1)[-1] if "/" in path else path
        extension = ""
        if "." in file_name:
            extension = "." + file_name.rsplit(".", 1)[-1]

        if modified_at is None:
            modified_at = datetime.now(timezone.utc)

        # Tokenize file name and content together
        name_tokens = self._tokenizer.tokenize(file_name)
        content_tokens = self._tokenizer.tokenize(content)
        all_tokens = name_tokens + content_tokens

        # Count token frequencies
        token_counts: dict[str, int] = {}
        for token in all_tokens:
            token_counts[token] = token_counts.get(token, 0) + 1

        doc = IndexedDocument(
            path=path,
            file_name=file_name,
            content=content,
            size=len(content.encode("utf-8")),
            modified_at=modified_at,
            extension=extension,
            token_counts=token_counts,
        )
        self._documents[path] = doc

        # Update inverted index
        for token in token_counts:
            if token not in self._inverted_index:
                self._inverted_index[token] = set()
            self._inverted_index[token].add(path)

    def remove_document(self, path: str) -> bool:
        """Remove a document from the index."""
        doc = self._documents.get(path)
        if not doc:
            return False

        # Remove from inverted index
        for token in doc.token_counts:
            if token in self._inverted_index:
                self._inverted_index[token].discard(path)
                if not self._inverted_index[token]:
                    del self._inverted_index[token]

        del self._documents[path]
        return True

    def rename_document(self, old_path: str, new_path: str) -> bool:
        """
        Update index when a file is renamed/moved.

        BUG #1: The old document is NOT removed from the index,
        and the new path's file name tokens are NOT indexed.
        The document is just re-keyed in _documents but the
        inverted index still points to the old path.
        """
        doc = self._documents.get(old_path)
        if not doc:
            return False

        # BUG #1: Only updates the _documents dict, does NOT update
        # the inverted index entries which still reference old_path.
        # Also does not re-tokenize the new file name.
        doc.path = new_path
        new_file_name = new_path.rsplit("/", 1)[-1] if "/" in new_path else new_path
        doc.file_name = new_file_name
        self._documents[new_path] = doc
        del self._documents[old_path]

        # Missing: Should remove old_path from all inverted index entries
        # Missing: Should re-tokenize new file name and update index
        return True

    def search(self, query: str, filters: SearchFilter | None = None, limit: int = 20) -> list[SearchResult]:
        """
        Search indexed documents.

        BUG #2: Ranking uses only TF-IDF without boosting exact matches
        in the file name. A file named exactly "report.txt" gets the
        same base score as a file that mentions "report" in its content.
        """
        query_tokens = self._tokenizer.tokenize(query)
        if not query_tokens:
            return []

        # Find candidate documents that contain any query token
        candidates: dict[str, float] = {}
        total_docs = len(self._documents)

        for token in query_tokens:
            if token not in self._inverted_index:
                continue

            matching_paths = self._inverted_index[token]
            # IDF: log(total_docs / docs_with_token)
            idf = math.log(total_docs / len(matching_paths)) if matching_paths else 0

            for path in matching_paths:
                doc = self._documents.get(path)
                if not doc:
                    continue
                # TF: token count in document
                tf = doc.token_counts.get(token, 0)
                score = tf * idf

                # BUG #2: No boost for exact file name match.
                # Should significantly boost score when query exactly
                # matches the file name.
                candidates[path] = candidates.get(path, 0) + score

        # Apply filters
        if filters:
            candidates = self._apply_filters(candidates, filters)

        # Sort by score descending
        sorted_results = sorted(candidates.items(), key=lambda x: x[1], reverse=True)

        results: list[SearchResult] = []
        for path, score in sorted_results[:limit]:
            doc = self._documents[path]
            snippet = self._extract_snippet(doc.content, query_tokens)
            results.append(SearchResult(
                path=path,
                file_name=doc.file_name,
                score=score,
                snippet=snippet,
            ))

        return results

    def _apply_filters(self, candidates: dict[str, float], filters: SearchFilter) -> dict[str, float]:
        """Apply search filters to candidates."""
        filtered: dict[str, float] = {}
        for path, score in candidates.items():
            doc = self._documents.get(path)
            if not doc:
                continue

            if filters.extension and doc.extension != filters.extension:
                continue
            if filters.min_size is not None and doc.size < filters.min_size:
                continue
            if filters.max_size is not None and doc.size > filters.max_size:
                continue
            if filters.modified_after and doc.modified_at < filters.modified_after:
                continue
            if filters.modified_before and doc.modified_at > filters.modified_before:
                continue

            filtered[path] = score
        return filtered

    def _extract_snippet(self, content: str, query_tokens: list[str], max_length: int = 150) -> str:
        """Extract a relevant snippet from content around the first match."""
        content_lower = content.lower()
        best_pos = -1

        for token in query_tokens:
            pos = content_lower.find(token)
            if pos != -1 and (best_pos == -1 or pos < best_pos):
                best_pos = pos

        if best_pos == -1:
            return content[:max_length] + ("..." if len(content) > max_length else "")

        start = max(0, best_pos - 30)
        end = min(len(content), start + max_length)
        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
