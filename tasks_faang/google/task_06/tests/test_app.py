"""Tests for the Log Aggregator & Analyzer."""

import pytest
from datetime import datetime, timezone
from app import LogAggregator, LogLevel, AlertRule


@pytest.fixture
def aggregator() -> LogAggregator:
    agg = LogAggregator()
    logs = [
        {"timestamp": "2024-01-15T10:00:00Z", "level": "INFO", "message": "Request started", "service": "api", "latency_ms": 45.0},
        {"timestamp": "2024-01-15T10:00:01Z", "level": "INFO", "message": "Request completed", "service": "api", "latency_ms": 120.0},
        {"timestamp": "2024-01-15T10:00:02Z", "level": "ERROR", "message": "Connection timeout to 10.0.0.1", "service": "api", "latency_ms": 5000.0},
        {"timestamp": "2024-01-15T10:00:03Z", "level": "WARNING", "message": "High memory usage", "service": "worker", "latency_ms": None},
        {"timestamp": "2024-01-15T10:00:04Z", "level": "INFO", "message": "Request completed", "service": "api", "latency_ms": 89.0},
        {"timestamp": "2024-01-15T10:00:05Z", "level": "ERROR", "message": "Connection timeout to 10.0.0.2", "service": "api", "latency_ms": 5001.0},
    ]
    for log in logs:
        agg.ingest(log)
    return agg


class TestIngestion:
    """Tests for log ingestion — some fail due to timestamp bug."""

    def test_ingest_iso_timestamp(self, aggregator: LogAggregator) -> None:
        """ISO 8601 timestamps should be parsed correctly."""
        assert len(aggregator.entries) == 6

    def test_ingest_unix_timestamp(self) -> None:
        """Unix timestamp (integer) should be parsed correctly.
        FAILING: Bug #1 — only ISO string timestamps are handled.
        """
        agg = LogAggregator()
        entry = agg.ingest({
            "timestamp": 1705312800,  # Unix timestamp
            "level": "INFO",
            "message": "test",
        })
        assert entry is not None, (
            "Unix timestamp 1705312800 was not parsed. "
            "Add support for int/float timestamps."
        )
        assert isinstance(entry.timestamp, datetime)

    def test_ingest_unix_float_timestamp(self) -> None:
        """Unix timestamp as float should also work.
        FAILING: Bug #1 — float timestamps not handled.
        """
        agg = LogAggregator()
        entry = agg.ingest({
            "timestamp": 1705312800.123,
            "level": "INFO",
            "message": "test",
        })
        assert entry is not None


class TestLevelFiltering:
    """Tests for log level filtering — FAILING due to Bug #3."""

    def test_filter_exact_level(self, aggregator: LogAggregator) -> None:
        """Filter by exact level should return matching entries."""
        errors = aggregator.filter_by_level(LogLevel.ERROR)
        assert len(errors) == 2

    def test_case_insensitive_level_parsing(self) -> None:
        """Log levels should be parsed case-insensitively.
        FAILING: Bug #3 — 'error' and 'Error' don't match LogLevel enum.
        """
        agg = LogAggregator()
        entry1 = agg.ingest({"timestamp": "2024-01-15T10:00:00Z", "level": "error", "message": "test1"})
        entry2 = agg.ingest({"timestamp": "2024-01-15T10:00:01Z", "level": "Error", "message": "test2"})

        assert entry1 is not None
        assert entry1.level == LogLevel.ERROR, (
            f"Level 'error' should parse as ERROR, got {entry1.level}. "
            f"Level parsing should be case-insensitive."
        )
        assert entry2.level == LogLevel.ERROR


class TestPercentiles:
    """Tests for percentile calculation — FAILING due to Bug #2."""

    def test_p50_basic(self) -> None:
        """P50 (median) of [10, 20, 30, 40, 50] should be 30."""
        agg = LogAggregator()
        result = agg.compute_percentile([10, 20, 30, 40, 50], 50)
        assert abs(result - 30.0) < 1.0

    def test_p95_interpolation(self) -> None:
        """P95 should use linear interpolation for correct results.
        FAILING: Bug #2 — integer index without interpolation.
        """
        agg = LogAggregator()
        values = list(range(1, 101))  # 1 to 100
        p95 = agg.compute_percentile(values, 95)
        # Correct P95 with interpolation: 95.05 (or very close to 95)
        assert abs(p95 - 95.05) < 1.0, (
            f"P95 of [1..100] should be ~95.05, got {p95}. "
            f"Check interpolation formula."
        )

    def test_p99_latency(self, aggregator: LogAggregator) -> None:
        """P99 latency should be computed correctly."""
        percentiles = aggregator.get_latency_percentiles(service="api")
        assert percentiles["p99"] > percentiles["p50"]


class TestErrorRate:
    """Tests for error rate calculation."""

    def test_error_rate(self, aggregator: LogAggregator) -> None:
        """Error rate should be correct."""
        rate = aggregator.get_error_rate()
        # 2 errors out of 6 logs = 0.333...
        assert abs(rate - 2 / 6) < 0.01

    def test_error_rate_by_service(self, aggregator: LogAggregator) -> None:
        """Error rate per service should be correct."""
        rate = aggregator.get_error_rate(service="api")
        # api has 5 entries, 2 errors
        assert abs(rate - 2 / 5) < 0.01


class TestPatternDetection:
    """Tests for pattern detection — TODO: implement."""

    def test_similar_errors_grouped(self, aggregator: LogAggregator) -> None:
        """TODO: Similar error messages should be grouped into patterns."""
        patterns = aggregator.detect_patterns(min_count=2)
        # "Connection timeout to 10.0.0.1" and "Connection timeout to 10.0.0.2"
        # should be one pattern
        assert len(patterns) >= 1
        timeout_pattern = [p for p in patterns if "timeout" in p["pattern"].lower()]
        assert len(timeout_pattern) == 1
        assert timeout_pattern[0]["count"] == 2


class TestAlerting:
    """Tests for alerting — TODO: implement."""

    def test_alert_on_high_error_rate(self, aggregator: LogAggregator) -> None:
        """TODO: Alert should trigger when error rate exceeds threshold."""
        rule = AlertRule(
            name="high_error_rate",
            condition=lambda entries: sum(1 for e in entries if e.level.value in ("ERROR", "CRITICAL")) / max(len(entries), 1) > 0.1,
            message="Error rate exceeds 10%",
            window_seconds=300,
        )
        aggregator.add_alert_rule(rule)
        alerts = aggregator.check_alerts()
        assert len(alerts) >= 1
        assert alerts[0].rule_name == "high_error_rate"


class TestTimeWindowAggregation:
    """Tests for time-windowed aggregation — TODO: implement."""

    def test_count_per_second(self, aggregator: LogAggregator) -> None:
        """TODO: Should count logs per 1-second window."""
        windows = aggregator.aggregate_by_window(window_seconds=1, metric="count")
        assert len(windows) > 0
        total = sum(w["value"] for w in windows)
        assert total == 6  # Total logs
