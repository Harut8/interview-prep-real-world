import pytest
import time
import threading
from app import Scheduler, JobStatus


@pytest.fixture
def scheduler():
    s = Scheduler()
    yield s
    s.stop()


def test_add_job(scheduler):
    job_id = scheduler.add_job(lambda: None, interval=1.0, name="test")
    assert job_id in scheduler.jobs


def test_job_executes(scheduler):
    results = []
    scheduler.add_job(lambda: results.append(1), interval=0.2)
    scheduler.start()
    time.sleep(0.5)
    scheduler.stop()
    assert len(results) >= 2


# Tests that a failing job doesn't kill the scheduler
def test_failing_job_doesnt_crash_scheduler(scheduler):
    results = []

    def good_job():
        results.append(1)

    def bad_job():
        raise ValueError("boom")

    scheduler.add_job(bad_job, interval=0.2, name="bad")
    scheduler.add_job(good_job, interval=0.2, name="good")
    scheduler.start()
    time.sleep(0.5)
    scheduler.stop()
    # Good job should still have executed despite bad job failing
    assert len(results) >= 1


def test_cancel_job(scheduler):
    job_id = scheduler.add_job(lambda: None, interval=0.1)
    assert scheduler.cancel_job(job_id) is True
    assert scheduler.jobs[job_id].status == JobStatus.CANCELLED


# TODO: Add tests for job dependencies
# TODO: Add tests for max_retries
# TODO: Add tests for job history
# TODO: Add test for scheduler drift
