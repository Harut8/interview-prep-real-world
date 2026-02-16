import json
from collections import Counter
from datetime import datetime


class LogProcessor:
    """
    Current implementation only counts total errors by type.
    TASK: Implement windowed aggregation.
    Add a method `get_errors_in_window(window_seconds)` that returns
    counts for the last N seconds.
    """

    def __init__(self):
        self.logs = []

    def process_line(self, line: str):
        try:
            data = json.loads(line)
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
            self.logs.append(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    def get_total_counts(self):
        return Counter(log["level"] for log in self.logs)


# Example usage:
# processor.process_line('{"timestamp": "2024-02-13T12:00:00", "level": "ERROR", "msg": "failed"}')
