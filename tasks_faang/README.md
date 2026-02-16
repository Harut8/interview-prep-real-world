# FAANG-Style Python Coding Interview — Practice Tasks (Middle/Senior)

40 practice tasks inspired by real interview patterns at Uber, Meta, Dropbox, and Google.
Each task gives you an **existing codebase with bugs** to fix and **features to implement**.

## How to Practice

```bash
cd tasks_faang/uber/task_01
pip install -r requirements.txt
# 1. Read README.md (task description) — 5 min
# 2. Read app.py (understand the codebase) — 10 min
# 3. Run tests: pytest tests/ -v
# 4. Fix failing tests by fixing bugs — 25 min
# 5. Implement new features — 20 min
# 6. Write tests for new features — 15 min
```

---

## Uber (10 tasks) — `uber/task_01` to `task_10`

Focus: ride-sharing, real-time systems, pricing, geospatial, payments

| # | Task | Key Skills |
|---|------|------------|
| 01 | Ride Matching Service | Haversine distance, atomic updates, timeouts |
| 02 | Surge Pricing Calculator | Division by zero, price caps, zone boundaries |
| 03 | Trip Fare Calculator | Float rounding, money, minimum fares |
| 04 | Real-time ETA Service | Dijkstra, graph algorithms, caching |
| 05 | Driver Location Tracker | Geohashing, timestamp ordering, stale data |
| 06 | Payment Processing Pipeline | Idempotency, double-charge, currency conversion |
| 07 | Rating & Review System | Average calculation, caching, time windows |
| 08 | Ride Event Stream Processor | Event ordering, deduplication, schema validation |
| 09 | Promo Code Service | Expiration logic, atomic limits, discount calculation |
| 10 | Fleet Analytics Dashboard | Moving averages, timezones, utilization metrics |

---

## Meta (10 tasks) — `meta/task_01` to `task_10`

Focus: social graph, news feed, content moderation, messaging, caching

| # | Task | Key Skills |
|---|------|------------|
| 01 | News Feed Ranker | Ranking algorithms, recency decay, pagination |
| 02 | Social Graph Service | BFS, cycle detection, bidirectional relationships |
| 03 | Content Moderation Pipeline | Rule priority, regex performance, immutability |
| 04 | Messaging Service | Message ordering, read receipts, soft delete |
| 05 | Post Engagement Tracker | Race conditions, negative counts, nested comments |
| 06 | User Privacy Settings | Permission inheritance, blocking, GDPR |
| 07 | Media Upload Service | File validation, MIME types, concurrent uploads |
| 08 | Notification Aggregator | Time bucketing, preference checks, digests |
| 09 | Feature Flags Service | Deterministic hashing, rollout logic, dependencies |
| 10 | Content Cache Service | Cache stampede, stale-while-revalidate, key collision |

---

## Dropbox (10 tasks) — `dropbox/task_01` to `task_10`

Focus: file sync, versioning, permissions, deduplication, search

| # | Task | Key Skills |
|---|------|------------|
| 01 | File Sync Engine | Timezone bugs, deletion tracking, rename detection |
| 02 | Chunked File Upload | Off-by-one, checksum verification, concurrency |
| 03 | File Version Control | Atomic versioning, binary diffs, restore logic |
| 04 | Sharing & Permissions | Permission inheritance, cascade revoke, symlinks |
| 05 | File Search Index | Index consistency, ranking, tokenization |
| 06 | Storage Quota Manager | Trash accounting, shared files, race conditions |
| 07 | File Deduplication | Full-file hashing, reference counting, collisions |
| 08 | Collaborative Lock Manager | Lock expiry, atomic acquisition, owner identity |
| 09 | File Activity Feed | Shared folder visibility, dedup, pagination |
| 10 | Trash & Recovery | Parent folder check, timezone, permission restore |

---

## Google (10 tasks) — `google/task_01` to `task_10`

Focus: search, distributed systems, MapReduce, load balancing, pipelines

| # | Task | Key Skills |
|---|------|------------|
| 01 | Text Search Engine | TF-IDF, stop words, document indexing |
| 02 | Consistent Hashing Ring | Virtual nodes, key distribution, replication |
| 03 | MapReduce Framework | Combiner logic, partitioning, sorting |
| 04 | URL Router / API Gateway | Route matching, path params, middleware |
| 05 | Task DAG Executor | Cycle detection, parallel execution, dependencies |
| 06 | Log Aggregator & Analyzer | Timestamp parsing, percentiles, log levels |
| 07 | Load Balancer | Round-robin, health checks, circuit breaker |
| 08 | Pub/Sub Message Broker | Message ordering, subscriber isolation, dead letters |
| 09 | Distributed Counter (CRDT) | Merge semantics, eventual consistency, tombstones |
| 10 | Data Pipeline Orchestrator | Diamond dependencies, error propagation, retry |

---

## Skills Covered Across All 40 Tasks

- **Algorithms**: Dijkstra, BFS, topological sort, TF-IDF, consistent hashing
- **Concurrency**: Race conditions, locks, atomic operations, thread safety
- **Data Structures**: Graphs, hash rings, DAGs, priority queues, inverted indexes
- **Error Handling**: Idempotency, retry logic, circuit breakers, dead letter queues
- **API Design**: REST endpoints, pagination, filtering, rate limiting
- **Security**: Permission models, input validation, GDPR compliance
- **Performance**: Caching, deduplication, batch processing, moving averages
- **Testing**: pytest fixtures, mocking, parametrize, edge cases
