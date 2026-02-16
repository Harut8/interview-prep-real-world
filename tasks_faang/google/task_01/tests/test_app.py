"""Tests for the Text Search Engine."""

import math
import pytest
from app import TextSearchEngine, SearchResult, STOP_WORDS


@pytest.fixture
def engine() -> TextSearchEngine:
    """Create a search engine with sample documents."""
    e = TextSearchEngine()
    e.add_document("doc1", "Python Guide", "python is a great programming language for data science and machine learning")
    e.add_document("doc2", "Java Intro", "java is a popular programming language used in enterprise software development")
    e.add_document("doc3", "Python ML", "machine learning with python is powerful for data analysis and prediction")
    e.add_document("doc4", "Web Dev", "javascript and python are used for web development and building apis")
    e.build_index()
    return e


class TestBasicSearch:
    """Tests for basic search functionality — these should pass after bug fixes."""

    def test_search_returns_results(self, engine: TextSearchEngine) -> None:
        """Basic search should return relevant documents."""
        results = engine.search("python")
        assert len(results) > 0
        doc_ids = [r.doc_id for r in results]
        assert "doc1" in doc_ids
        assert "doc3" in doc_ids

    def test_empty_query_returns_empty(self, engine: TextSearchEngine) -> None:
        """Searching with empty string returns no results."""
        results = engine.search("")
        assert results == []

    def test_nonexistent_term_returns_empty(self, engine: TextSearchEngine) -> None:
        """Searching for a term not in any document returns empty."""
        results = engine.search("blockchain")
        assert results == []


class TestTFIDFScoring:
    """Tests for correct TF-IDF scoring — FAILING due to bugs."""

    def test_idf_uses_natural_log(self, engine: TextSearchEngine) -> None:
        """IDF should use natural logarithm (ln), not log base 10.
        FAILING: Bug #1 — uses math.log10 instead of math.log.
        """
        # "java" appears in 1 out of 4 documents
        idf = engine._compute_idf("java")
        expected_idf = math.log(4 / 1)  # natural log
        assert abs(idf - expected_idf) < 0.001, (
            f"IDF for 'java' should be ln(4/1)={expected_idf:.4f}, got {idf:.4f}. "
            f"Check logarithm base."
        )

    def test_tf_normalized_by_doc_length(self, engine: TextSearchEngine) -> None:
        """TF should be normalized by document length to avoid bias toward longer docs.
        FAILING: Bug #2 — raw count is used instead of count/doc_length.
        """
        # doc1 has "python" once in a 12-word doc
        tf = engine._compute_tf("python", "doc1")
        doc_length = len(engine.documents["doc1"].tokens)
        expected_tf = 1 / doc_length
        assert abs(tf - expected_tf) < 0.01, (
            f"TF should be normalized: count/doc_length = 1/{doc_length} = {expected_tf:.4f}, "
            f"got {tf}. Normalize by document length."
        )

    def test_stop_words_not_in_index(self, engine: TextSearchEngine) -> None:
        """Stop words should not appear in the inverted index.
        FAILING: Bug #3 — stop words are removed from queries but not from index.
        """
        for stop_word in ["is", "a", "and", "for", "the", "in"]:
            assert stop_word not in engine.inverted_index, (
                f"Stop word '{stop_word}' found in inverted index. "
                f"Remove stop words during indexing, not just during query."
            )

    def test_ranking_relevance(self, engine: TextSearchEngine) -> None:
        """Documents more relevant to query should rank higher."""
        results = engine.search("python machine learning")
        assert len(results) >= 2
        # doc3 "machine learning with python" should rank high
        assert results[0].doc_id in ("doc1", "doc3")


class TestPhraseSearch:
    """Tests for phrase search — TODO: implement."""

    def test_phrase_search_exact_match(self, engine: TextSearchEngine) -> None:
        """TODO: Phrase search should find exact consecutive term sequences."""
        results = engine.phrase_search("machine learning")
        doc_ids = [r.doc_id for r in results]
        assert "doc1" in doc_ids  # "machine learning" appears in doc1
        assert "doc3" in doc_ids  # "machine learning" appears in doc3
        assert "doc2" not in doc_ids  # no "machine learning" in doc2

    def test_phrase_search_no_match(self, engine: TextSearchEngine) -> None:
        """TODO: Phrase that doesn't exist as consecutive terms returns empty."""
        results = engine.phrase_search("python enterprise")
        assert results == []


class TestSnippets:
    """Tests for search result snippets — TODO: implement."""

    def test_snippet_highlights_terms(self, engine: TextSearchEngine) -> None:
        """TODO: Snippet should highlight matched terms with **bold** markers."""
        snippet = engine.get_snippet("doc1", "python", context_words=3)
        assert "**python**" in snippet

    def test_snippet_includes_context(self, engine: TextSearchEngine) -> None:
        """TODO: Snippet should include surrounding context words."""
        snippet = engine.get_snippet("doc1", "programming", context_words=3)
        assert "**programming**" in snippet
        # Should have some words before/after
        assert len(snippet.split()) > 1


class TestSpellingSuggestions:
    """Tests for spelling suggestions — TODO: implement."""

    def test_suggests_close_terms(self, engine: TextSearchEngine) -> None:
        """TODO: Should suggest indexed terms within edit distance 1."""
        suggestions = engine.suggest_spelling("pythn")
        assert "python" in suggestions

    def test_no_suggestions_for_valid_term(self, engine: TextSearchEngine) -> None:
        """TODO: If query term exists in index, no suggestion needed."""
        suggestions = engine.suggest_spelling("python")
        assert suggestions == [] or "python" in suggestions
