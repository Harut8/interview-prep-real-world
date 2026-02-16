"""
Log Aggregator & Analyzer

Aggregate structured logs and compute metrics like percentiles, error rates,
and time-windowed statistics.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Optional


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """A structured log entry."""
    timestamp: datetime
    level: LogLevel
    message: str
    service: str = ""
    latency_ms: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertRule:
    """A threshold-based alerting rule."""
    name: str
    condition: Callable[[list[LogEntry]], bool]
    message: str
    window_seconds: int = 300  # 5 minutes default


@dataclass
class Alert:
    """A triggered alert."""
    rule_name: str
    message: str
    triggered_at: datetime
    entries_count: int


class LogAggregator:
    """Aggregates and analyzes structured logs."""

    def __init__(self) -> None:
        self.entries: list[LogEntry] = []
        self.alert_rules: list[AlertRule] = []

    def ingest(self, raw_log: dict[str, Any]) -> Optional[LogEntry]:
        """Parse a raw log dict and add it to the aggregator."""
        try:
            timestamp = self._parse_timestamp(raw_log["timestamp"])
            if timestamp is None:
                return None

            level = self._parse_level(raw_log.get("level", "INFO"))
            entry = LogEntry(
                timestamp=timestamp,
                level=level,
                message=raw_log.get("message", ""),
                service=raw_log.get("service", ""),
                latency_ms=raw_log.get("latency_ms"),
                metadata=raw_log.get("metadata", {}),
            )
            self.entries.append(entry)
            return entry
        except (KeyError, ValueError) as e:
            return None

    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse a timestamp from various formats."""
        # BUG #1: Only handles ISO 8601 string format.
        # Unix timestamps (int/float) are not handled and return None.
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        # Missing: handling for int/float Unix timestamps
        # Should convert Unix timestamp to datetime
        return None

    def _parse_level(self, value: str) -> LogLevel:
        """Parse log level string into LogLevel enum."""
        # BUG #3: Case-sensitive comparison. "error" or "Error" won't match.
        try:
            return LogLevel(value)
        except ValueError:
            return LogLevel.INFO

    def filter_by_level(self, level: LogLevel) -> list[LogEntry]:
        """Filter entries by log level (exact match)."""
        return [e for e in self.entries if e.level == level]

    def filter_by_level_min(self, min_level: LogLevel) -> list[LogEntry]:
        """Filter entries with level >= min_level."""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4,
        }
        min_val = level_order[min_level]
        return [e for e in self.entries if level_order[e.level] >= min_val]

    def compute_percentile(self, values: list[float], percentile: float) -> float:
        """Compute the given percentile of a list of values.
        Uses linear interpolation between closest ranks.
        """
        if not values:
            return 0.0

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        # BUG #2: Wrong percentile calculation.
        # The index calculation is incorrect — it should use (percentile/100) * (n-1)
        # for proper interpolation. Instead, it uses integer division which
        # just picks a value without interpolating.
        idx = int(percentile / 100 * n)
        if idx >= n:
            idx = n - 1
        return sorted_vals[idx]

    def get_latency_percentiles(
        self, service: Optional[str] = None
    ) -> dict[str, float]:
        """Compute P50, P95, P99 latency percentiles."""
        entries = self.entries
        if service:
            entries = [e for e in entries if e.service == service]

        latencies = [e.latency_ms for e in entries if e.latency_ms is not None]
        if not latencies:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0}

        return {
            "p50": self.compute_percentile(latencies, 50),
            "p95": self.compute_percentile(latencies, 95),
            "p99": self.compute_percentile(latencies, 99),
        }

    def get_error_rate(self, service: Optional[str] = None) -> float:
        """Compute the fraction of ERROR + CRITICAL logs."""
        entries = self.entries
        if service:
            entries = [e for e in entries if e.service == service]

        if not entries:
            return 0.0

        error_count = sum(
            1 for e in entries
            if e.level in (LogLevel.ERROR, LogLevel.CRITICAL)
        )
        return error_count / len(entries)

    # -------------------------------------------------------------------------
    # TODO: Implement log pattern detection
    # -------------------------------------------------------------------------
    def detect_patterns(self, min_count: int = 2) -> list[dict[str, Any]]:
        """Group similar log messages into patterns.
        Replace variable parts (IPs, numbers, UUIDs) with placeholders.
        Return list of {"pattern": str, "count": int, "examples": list[str]}.
        """
        raise NotImplementedError("Pattern detection not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement alerting rules
    # -------------------------------------------------------------------------
    def add_alert_rule(self, rule: AlertRule) -> None:
        """Register an alerting rule."""
        raise NotImplementedError("Alerting not implemented")

    def check_alerts(self) -> list[Alert]:
        """Evaluate all alert rules against recent logs and return triggered alerts."""
        raise NotImplementedError("Alert checking not implemented")

    # -------------------------------------------------------------------------
    # TODO: Implement time-windowed aggregation
    # -------------------------------------------------------------------------
    def aggregate_by_window(
        self,
        window_seconds: int,
        metric: str = "count",
    ) -> list[dict[str, Any]]:
        """Aggregate metrics into fixed time windows.
        Returns list of {"window_start": datetime, "window_end": datetime, "value": float}.
        Supported metrics: "count", "error_rate", "p95_latency".
        """
        raise NotImplementedError("Time-windowed aggregation not implemented")
