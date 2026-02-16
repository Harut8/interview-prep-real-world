import pytest
import threading
from app import TaskQueue, TaskStatus, process_task, worker


def test_create_task():
    queue = TaskQueue()
    task = queue.create_task("test-task", {"key": "value"})
    assert task.name == "test-task"
    assert task.status == TaskStatus.PENDING


def test_get_next_task():
    queue = TaskQueue()
    queue.create_task("task-1", {})
    task = queue.get_next_task()
    assert task is not None
    assert task.name == "task-1"
    assert task.status == TaskStatus.RUNNING


# This test demonstrates the race condition — fix get_next_task to make it pass
def test_concurrent_workers_no_duplicate_processing():
    queue = TaskQueue()
    for i in range(10):
        queue.create_task(f"task-{i}", {})

    processed_tasks = []
    lock = threading.Lock()

    original_get_next = queue.get_next_task

    def tracking_get_next():
        task = original_get_next()
        if task:
            with lock:
                processed_tasks.append(task.id)
        return task

    queue.get_next_task = tracking_get_next

    threads = []
    for i in range(5):
        t = threading.Thread(target=worker, args=(queue, i))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Each task should appear exactly once
    assert len(processed_tasks) == len(set(processed_tasks))


# TODO: Add test for mutable default argument bug
# TODO: Add test for enum consistency
# TODO: Add test for proper error handling (not bare except)
# TODO: Add tests for priority queue feature
# TODO: Add tests for get_queue_stats
