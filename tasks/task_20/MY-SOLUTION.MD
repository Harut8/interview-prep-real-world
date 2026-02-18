1. Duplicate sending bug (line 130-133) — break after first success
    - add `break` after `success = True`
    - try channels in order, stop on first successful delivery
    - record each attempt (success or failure) before breaking

2. Store failure history (line 135-137)
    - collect in `self._attempts: dict[str, list]`
    - each attempt: `{"channel": channel, "status": "delivered"/"failed", "error": str|None, "at": timestamp}`
    - record both successes and failures for the audit trail

3. Priority ordering (line 146) — add `reverse=True`
    - `pending.sort(key=lambda n: n.priority.value, reverse=True)`
    - HIGH=3 should come before LOW=1

4. Template rendering — use `format_map(SafeDict)`, NOT Jinja2
    - Jinja2 is not in requirements.txt, don't add unnecessary dependencies
    - fix with stdlib:
        ```
        class SafeDict(dict):
            def __missing__(self, key):
                return f"{{{key}}}"  # leaves {key} as placeholder

        return template.format_map(SafeDict(context))
        ```
    - missing keys stay as `{key}` in output instead of crashing

5. NotificationQueue with priority
    - simple list with `heapq` or sorted insertion is sufficient (no threading here)
    - sort key: `(-priority.value, created_at)` — higher priority first, FIFO within same priority
    - no need for `queue.PriorityQueue` (thread safety not required)

6. Delivery status tracking — state transitions with timestamps
    - track: `pending -> sending -> delivered / failed`
    - each transition should record a timestamp
    - structured report from `get_delivery_report(notification_id)`:
        ```
        {
            "notification_id": "abc123",
            "status": "delivered",
            "created_at": ...,
            "delivered_at": ...,
            "attempts": [
                {"channel": "email", "status": "failed", "error": "...", "at": ...},
                {"channel": "sms", "status": "delivered", "error": None, "at": ...},
            ]
        }
        ```

7. Strategy pattern inconsistency — sender interfaces are not uniform
    - `EmailSender.send(recipient, subject, body)` — 3 args
    - `SMSSender.send(recipient, body)` — 2 args
    - `PushSender.send(recipient, title, body)` — 3 args
    - `send()` method uses channel-specific `if/elif` (lines 123-128) which defeats strategy pattern
    - fix: uniform interface `send(recipient, subject, body)` for all senders

8. Retry mechanism — not addressed in original code
    - on failure: retry same channel N times with backoff, or try next channel
    - track attempt count per channel
    - max retries configurable per notification or globally

9. Tests to write
    - break after first success: mock senders, verify second channel not called
    - failure recorded in attempt history
    - priority ordering: HIGH before MEDIUM before LOW
    - template with missing keys doesn't crash, keeps placeholders
    - delivery report returns structured data with all attempts
    - retry: failed channel retried N times before moving to next
    - queue: same-priority notifications ordered by creation time (FIFO)
    - status transitions: pending → sending → delivered/failed
