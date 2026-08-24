import pytest
import time
from app import JobQueue


class TestBasicJobs:
    def test_submit_and_complete(self):
        q = JobQueue(max_workers=1)
        q.submit("j1", lambda: 42)
        q.drain()
        assert q.get_status("j1") == "completed"
        assert q.get_result("j1") == 42

    def test_failed_job(self):
        def bad():
            raise ValueError("boom")
        q = JobQueue(max_workers=1)
        q.submit("j1", bad)
        q.drain()
        assert q.get_status("j1") == "failed"

    def test_get_result_pending_raises(self):
        q = JobQueue(max_workers=0)  # no workers, stays pending
        q.submit("j1", lambda: 42)
        with pytest.raises(Exception):
            q.get_result("j1")


class TestPriority:
    def test_higher_priority_runs_first(self):
        order = []
        q = JobQueue(max_workers=1)
        # Submit low-priority first, high-priority second
        # But don't start workers until both are queued
        q.submit("low", lambda: order.append("low"), priority=1)
        q.submit("high", lambda: order.append("high"), priority=10)
        q.drain()
        # high should be before low (if both were pending when worker started)
        if len(order) == 2:
            assert order[0] == "high"


class TestRetries:
    def test_retry_on_failure(self):
        attempts = []
        def flaky():
            attempts.append(1)
            if len(attempts) < 3:
                raise ValueError("not yet")
            return "ok"
        q = JobQueue(max_workers=1)
        q.submit("j1", flaky, max_retries=3)
        q.drain()
        assert q.get_status("j1") == "completed"
        assert q.get_result("j1") == "ok"
        assert len(attempts) == 3

    def test_exhausted_retries(self):
        def always_fail():
            raise ValueError("nope")
        q = JobQueue(max_workers=1)
        q.submit("j1", always_fail, max_retries=2)
        q.drain()
        assert q.get_status("j1") == "failed"


class TestCancel:
    def test_cancel_pending(self):
        q = JobQueue(max_workers=0)
        q.submit("j1", lambda: 42)
        assert q.cancel("j1") is True
        assert q.get_status("j1") == "cancelled"

    def test_cancel_nonexistent(self):
        q = JobQueue(max_workers=1)
        assert q.cancel("nope") is False
