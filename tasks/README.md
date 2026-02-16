# Yandex Python Coding Interview — Practice Tasks

20 practice tasks matching the Yandex interview format:
- You get an **existing codebase with bugs**
- You must **fix bugs** and **add new features**
- You must **write pytest tests**
- Time limit: **60 minutes per task**

## How to Practice

```bash
cd tasks/task_01
pip install -r requirements.txt
# 1. Read README.md (the task description)
# 2. Read app.py (understand the codebase — ~10 min)
# 3. Run existing tests: pytest tests/ -v
# 4. Fix failing tests by fixing bugs in app.py (~25 min)
# 5. Implement new features (~20 min)
# 6. Write tests for new features (~15 min)
```

## Task List

| # | Task | Skills Tested | Difficulty |
|---|------|---------------|------------|
| 01 | **URL Shortener** — Fix bugs & add stats endpoint | FastAPI, validation, HTTP status codes | Easy |
| 02 | **User Auth Service** — Fix security issues & add token refresh | Security, JWT, password hashing, SQL injection | Medium |
| 03 | **Async Data Aggregator** — Fix concurrency bugs & add caching | asyncio, aiohttp, error handling, performance | Medium |
| 04 | **Task Queue Processor** — Fix race conditions & add priority | Threading, enums, mutable defaults, error handling | Medium |
| 05 | **Book Library CRUD** — Fix pagination & add search | SQL, pagination, FastAPI, query efficiency | Easy |
| 06 | **Rate Limiter** — Fix implementation & add sliding window | Thread safety, algorithms, decorators, testability | Medium |
| 07 | **CSV Data Pipeline** — Fix processing bugs & add validation | File I/O, generators, data parsing, edge cases | Easy |
| 08 | **Key-Value Store with TTL** — Fix expiration & add persistence | Time logic, file I/O, context managers | Medium |
| 09 | **Event System** — Fix observer pattern & add async support | Observer pattern, async/sync, iterator safety | Medium |
| 10 | **HTTP Client Wrapper** — Fix retry logic & add circuit breaker | HTTP patterns, resilience, security, httpx | Hard |
| 11 | **Config Manager** — Fix validation & add env override | Pydantic, YAML, security (secrets), validation | Medium |
| 12 | **Async Web Scraper** — Fix resource leaks & add rate limiting | aiohttp, semaphore, async resource management | Hard |
| 13 | **LRU Cache** — Fix implementation & add size eviction | OrderedDict, decorators, thread safety, memory | Medium |
| 14 | **Session Manager** — Fix concurrency & add expiration | Security, data structures, FastAPI middleware | Medium |
| 15 | **JSON Schema Validator** — Fix validation & add custom rules | Recursion, error accumulation, regex, API design | Medium |
| 16 | **Product API Pagination** — Fix queries & add sorting | SQL, API design, pagination, filtering | Easy |
| 17 | **Job Scheduler** — Fix timing bugs & add dependencies | Threading, time management, error isolation | Hard |
| 18 | **Middleware Pipeline** — Fix ordering & add auth/logging | Chain of responsibility, error handling, immutability | Medium |
| 19 | **Connection Pool** — Fix resources & add health checks | Resource management, context managers, threading | Hard |
| 20 | **Notification Service** — Fix delivery & add templating | Strategy pattern, priority queues, templating | Medium |

## Skills Coverage

- **Web Frameworks**: FastAPI (01, 05, 14, 16), Flask (02)
- **Async/Await**: asyncio, aiohttp (03, 09, 12)
- **Threading**: Race conditions, locks, thread safety (04, 06, 13, 17, 19)
- **Testing**: pytest fixtures, mocking, parametrize (all tasks)
- **Databases**: SQLite, SQL queries (02, 05, 16)
- **Security**: SQL injection, password hashing, JWT, secrets (02, 11, 14)
- **Design Patterns**: Observer (09), Strategy (20), Chain of Responsibility (18), Circuit Breaker (10)
- **Data Structures**: OrderedDict, queues, linked lists (04, 08, 13, 19)
- **Pydantic**: Validation, models, settings (01, 11, 16)
- **Error Handling**: Exception patterns, error accumulation (03, 04, 15, 17)
- **File I/O**: CSV, JSON, YAML (07, 08, 11)
- **Performance**: O(n²) optimization, generators, caching (03, 07, 13)

## Common Bug Patterns Across Tasks

1. Mutable default arguments (Task 04)
2. Bare except / swallowed exceptions (Task 04, 17)
3. Missing await / blocking in async (Task 03)
4. Resource leaks — unclosed connections/sessions (Task 03, 12, 19)
5. Race conditions — no locks (Task 04, 06)
6. Off-by-one errors — pagination, counting (Task 05, 06)
7. SQL injection (Task 02)
8. Iterator modification during iteration (Task 06, 09)
9. Bool is subclass of int in Python (Task 15)
10. Secrets in logs/repr (Task 10, 11)
