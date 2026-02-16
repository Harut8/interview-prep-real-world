"""Tests for File Search Index."""

import pytest
from datetime import datetime, timezone

from app import (
    SearchIndex,
    Tokenizer,
    SearchFilter,
    SearchResult,
    IndexedDocument,
)


@pytest.fixture
def index() -> SearchIndex:
    idx = SearchIndex()
    idx.index_document("/docs/readme.txt", "Welcome to the project documentation")
    idx.index_document("/docs/api_guide.txt", "API guide for developers with examples")
    idx.index_document("/src/main.py", "def main():\n    print('hello world')")
    idx.index_document("/src/utils.py", "def getUserName(user_id):\n    return db.query(user_id)")
    idx.index_document("/reports/quarterly_report.txt", "Quarterly financial report for Q3 2024")
    return idx


class TestBasicSearch:
    """Tests for basic search functionality."""

    def test_search_finds_matching_document(self, index: SearchIndex):
        """Search should find documents containing query terms."""
        results = index.search("documentation")

        assert len(results) >= 1
        paths = [r.path for r in results]
        assert "/docs/readme.txt" in paths

    def test_search_no_results(self, index: SearchIndex):
        """Search for non-existent terms should return empty results."""
        results = index.search("xyznonexistent")

        assert len(results) == 0

    def test_search_multiple_results(self, index: SearchIndex):
        """Search should return multiple matching documents ranked by relevance."""
        results = index.search("report")

        assert len(results) >= 1
        # quarterly_report.txt should be a top result
        assert any(r.file_name == "quarterly_report.txt" for r in results)


class TestRenameHandling:
    """Tests for index update on file rename/move."""

    # FAILING: BUG #1 - Index not updated on rename
    def test_rename_updates_index(self, index: SearchIndex):
        """After renaming, old path should not appear and new path should be searchable."""
        index.rename_document("/docs/readme.txt", "/docs/overview.txt")

        # Search for old name should NOT return old path
        results_old = index.search("readme")
        old_paths = [r.path for r in results_old]
        assert "/docs/readme.txt" not in old_paths, (
            "Old path still appears in search results after rename"
        )

        # Search for new name should return new path
        results_new = index.search("overview")
        new_paths = [r.path for r in results_new]
        assert "/docs/overview.txt" in new_paths, (
            "New path not found in search results after rename"
        )


class TestSearchRanking:
    """Tests for search result ranking."""

    # FAILING: BUG #2 - Exact file name match not boosted
    def test_exact_filename_match_ranks_first(self, index: SearchIndex):
        """A file whose name exactly matches the query should rank highest."""
        # Add a file whose name is exactly the query
        index.index_document(
            "/reports/report.txt",
            "This is a generic file with minimal content",
        )

        results = index.search("report")

        # "report.txt" should rank higher than "quarterly_report.txt"
        # because its name is an exact match
        assert len(results) >= 2
        assert results[0].file_name == "report.txt", (
            f"Expected 'report.txt' to rank first, got '{results[0].file_name}'"
        )


class TestTokenizer:
    """Tests for the tokenizer."""

    def test_basic_tokenization(self):
        """Basic text should be split into lowercase tokens."""
        tokens = Tokenizer.tokenize("Hello World 123")
        assert tokens == ["hello", "world", "123"]

    # FAILING: BUG #3 - Tokenizer doesn't split CamelCase
    def test_camel_case_splitting(self):
        """CamelCase identifiers should be split into individual words."""
        tokens = Tokenizer.tokenize("getUserName processFileUpload")

        assert "get" in tokens
        assert "user" in tokens
        assert "name" in tokens
        assert "process" in tokens
        assert "file" in tokens
        assert "upload" in tokens

    # FAILING: BUG #3 - Tokenizer doesn't split snake_case properly
    def test_snake_case_splitting(self):
        """snake_case identifiers should be split into individual words."""
        tokens = Tokenizer.tokenize("file_upload_manager user_name")

        assert "file" in tokens
        assert "upload" in tokens
        assert "manager" in tokens
        assert "user" in tokens
        assert "name" in tokens


class TestSearchFilters:
    """Tests for search result filtering."""

    def test_filter_by_extension(self, index: SearchIndex):
        """Filtering by extension should only return matching file types."""
        results = index.search("def", filters=SearchFilter(extension=".py"))

        assert all(r.file_name.endswith(".py") for r in results)

    # TODO: Implement fuzzy search
    def test_fuzzy_search(self, index: SearchIndex):
        """Fuzzy search should find results despite typos."""
        pytest.skip("TODO: Implement fuzzy search with edit distance")

    # TODO: Implement search result highlighting
    def test_search_highlighting(self, index: SearchIndex):
        """Search results should have matched terms highlighted in snippets."""
        pytest.skip("TODO: Implement search result term highlighting")
