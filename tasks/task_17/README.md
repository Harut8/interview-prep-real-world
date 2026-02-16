# Task 17: Background Job Scheduler — Fix Timing Bugs & Add Job Dependencies

**Time limit: 60 minutes**

## Existing Codebase
A simple background job scheduler that executes functions at specified intervals or cron-like schedules.

## Problems to Fix
1. The scheduler drifts over time — uses `time.sleep(interval)` instead of calculating next run time.
2. If a job takes longer than its interval, jobs pile up (overlap).
3. The `cancel_job` method doesn't stop a currently running job.
4. Exception in one job's callback kills the scheduler thread.

## Features to Implement
1. Add job dependencies: Job B should only run after Job A completes successfully.
2. Add `max_retries` per job: failed jobs should be retried up to N times.
3. Add a `get_job_history(job_id)` returning last N runs with status and duration.
4. Write tests for scheduler behavior.

## What We Evaluate
- Time management
- Thread coordination
- Error isolation
- Dependency graph handling
