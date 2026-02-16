# Task 04: Task Queue Processor — Fix Race Conditions & Add Priority Queue

**Time limit: 60 minutes**

## Existing Codebase
A simple in-memory task queue that processes jobs. Workers consume tasks from the queue and process them.

## Problems to Fix
1. Race condition: multiple workers can pick up the same task.
2. The `TaskStatus` enum is used inconsistently — some places use strings instead of enum values.
3. `process_task` swallows all exceptions with bare `except:` — fix error handling.
4. Mutable default argument bug in `create_task`.

## Features to Implement
1. Add task priority support (HIGH, MEDIUM, LOW). Higher priority tasks should be processed first.
2. Add a `get_queue_stats()` function returning counts per status and per priority.
3. Write comprehensive tests including concurrent access scenarios.

## What We Evaluate
- Thread safety awareness
- Proper use of Python enums
- Error handling patterns
- Testing concurrent code
