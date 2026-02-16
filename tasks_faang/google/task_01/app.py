"""
Text Search Engine with TF-IDF Ranking

A simple in-memory search engine that indexes documents and retrieves them
using TF-IDF (Term Frequency - Inverse Document Frequency) scoring.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional


STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "and", "but", "or", "nor", "not", "so", "yet", "both", "either",
    "neither", "each", "every", "all", "any", "few", "more", "most", "other",
    "some", "such", "no", "only", "own", "same", "than", "too", "very",
    "just", "because", "if", "when", "where", "how", "what", "which", "who",
    "whom", "this", "that", "these", "those", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her", "they",
    "them", "their",
})


@dataclass
class Document:
    """Represents an indexed document."""
    doc_id: str
    title: str
    content: str
    tokens: list[str] = field(default_factory=list)


@dataclass
class SearchResult:
    """A single search result."""
    doc_id: str
    title: str
    score: float
    snippet: str = ""


class TextSearchEngine:
    """TF-IDF based text search engine."""

    def __init__(self) -> None:
        self.documents: dict[str, Document] = {}
        self.inverted_index: dict[str, set[str]] = {}  # term -> set of doc_ids
        self.term_frequencies: dict[str, dict[str, int]] = {}  # doc_id -> {term: count}
        self._indexed: bool = False

    def add_document(self, doc_id: str, title: str, content: str) -> None:
        """Add a document to the engine."""
        tokens = self._tokenize(content)
        doc = Document(doc_id=doc_id, title=title, content=content, tokens=tokens)
        self.documents[doc_id] = doc
        self._indexed = False

    def build_index(self) -> None:
        """Build the inverted index from all added documents."""
        self.inverted_index.clear()
        self.term_frequencies.clear()

        for doc_id, doc in self.documents.items():
            term_counts: dict[str, int] = {}
            for token in doc.tokens:
                # BUG #3: Stop words are NOT removed during indexing,
                # but they ARE removed from search queries (see _tokenize_query).
                # This means stop words pollute the index and affect IDF calculations.
                term_counts[token] = term_counts.get(token, 0) + 1
                if token not in self.inverted_index:
                    self.inverted_index[token] = set()
                self.inverted_index[token].add(doc_id)

            self.term_frequencies[doc_id] = term_counts

        self._indexed = True

    def search(self, query: str, top_k: int = 10) -> list[SearchResult]:
        """Search for documents matching the query, ranked by TF-IDF score."""
        if not self._indexed:
            self.build_index()

        query_terms = self._tokenize_query(query)
        if not query_terms:
            return []

        scores: dict[str, float] = {}
        for term in query_terms:
            if term not in self.inverted_index:
                continue
            idf = self._compute_idf(term)
            for doc_id in self.inverted_index[term]:
                tf = self._compute_tf(term, doc_id)
                scores[doc_id] = scores.get(doc_id, 0.0) + tf * idf

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for doc_id, score in ranked:
            doc = self.documents[doc_id]
            results.append(SearchResult(
                doc_id=doc_id,
                title=doc.title,
                score=round(score, 6),
            ))
        return results

    def _compute_tf(self, term: str, doc_id: str) -> float:
        """Compute term frequency for a term in a document."""
        count = self.term_frequencies.get(doc_id, {}).get(term, 0)
        # BUG #2: Term frequency is raw count, not normalized by document length.
        # This unfairly favors longer documents. Should divide by total tokens in doc.
        return count

    def _compute_idf(self, term: str) -> float:
        """Compute inverse document frequency for a term."""
        n_total = len(self.documents)
        n_containing = len(self.inverted_index.get(term, set()))
        if n_containing == 0:
            return 0.0
        # BUG #1: Uses log base 10 instead of natural log (ln).
        # Standard TF-IDF uses natural logarithm. This compresses the IDF range
        # and makes scores less discriminative.
        return math.log10(n_total / n_containing)

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into lowercase terms (keeps all words including stop words)."""
        return re.findall(r'[a-z0-9]+', text.lower())

    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize a search query, removing stop words."""
        tokens = re.findall(r'[a-z0-9]+', query.lower())
        # Stop words are removed from query but NOT from the index (bug #3 interaction)
        return [t for t in tokens if t not in STOP_WORDS]

    # -------------------------------------------------------------------------
    # TODO: Implement phrase_search
    # -------------------------------------------------------------------------
    def phrase_search(self, phrase: str, top_k: int = 10) -> list[SearchResult]:
        """
        Search for an exact phrase in documents.
        The phrase terms must appear consecutively in the document in order.
        Returns results ranked by TF-IDF of the phrase terms.
        """
        raise NotImplementedError("phrase_search not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement get_snippet
    # -------------------------------------------------------------------------
    def get_snippet(self, doc_id: str, query: str, context_words: int = 5) -> str:
        """
        Return a snippet from the document around the first occurrence of a
        query term. Matched terms should be wrapped in **bold** markers.

        Example: "...the **quick** brown fox jumps over the **lazy** dog..."
        """
        raise NotImplementedError("get_snippet not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement suggest_spelling
    # -------------------------------------------------------------------------
    def suggest_spelling(self, query: str) -> list[str]:
        """
        When a query returns no results, suggest alternative terms from the index
        that are within edit distance 1 of the query terms.
        Returns a list of suggested replacement queries.
        """
        raise NotImplementedError("suggest_spelling not implemented")
