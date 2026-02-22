# My Solution — Task 22

## Bug Fixes

### 1. `add_message` doesn't detect duplicates

`self.messages[message.id] = message` silently overwrites. The `is_duplicate` method exists but is never called — it's dead code.

Fix: call `is_duplicate` at the top of `add_message`.

```python
def add_message(self, message: Message) -> bool:
    if self.is_duplicate(message.id):
        return False
    self.messages[message.id] = message
    # ... rest unchanged
```

### 2. `get_ordered_messages` sorts on every call

`messages.sort()` is O(n log n) on every read. Should maintain sorted order on insertion instead.

Fix: use `bisect.insort` when adding messages so the list stays sorted. Then `get_ordered_messages` just returns the list directly.

```python
import bisect

def add_message(self, message: Message) -> bool:
    # ... duplicate check ...
    self.messages[message.id] = message
    channel = message.channel
    if channel not in self.channels:
        self.channels[channel] = []
        self._next_expected_seq[channel] = 0

    # Insert in sorted position instead of append
    queue = self.channels[channel]
    bisect.insort(queue, message)  # requires __lt__ on Message
    message.status = MessageStatus.BUFFERED
    return True

def get_ordered_messages(self, channel: str = "default") -> list[Message]:
    if channel not in self.channels:
        return []
    return list(self.channels[channel])  # already sorted
```

Need to add `__lt__` to Message:
```python
def __lt__(self, other):
    return (self.sequence_num, self.timestamp) < (other.sequence_num, other.timestamp)
```

Alternative: use `heapq` with tuples `(sequence_num, timestamp, message)` — O(log n) insert, O(n log n) to read all ordered but O(log n) to pop next.

### 3. `deliver_next` doesn't handle gaps in sequence numbers

Current code delivers whatever buffered message comes first, even if there's a gap. E.g., if seq 0 is delivered and seq 2 arrives before seq 1, it would deliver seq 2 — skipping seq 1.

Fix: only deliver if `msg.sequence_num == expected_seq`, otherwise return `None` (wait for the missing message).

```python
def deliver_next(self, channel: str = "default") -> Optional[Message]:
    if channel not in self.channels:
        return None

    expected_seq = self._next_expected_seq.get(channel, 0)
    ordered = self.get_ordered_messages(channel)

    for msg in ordered:
        if msg.status == MessageStatus.BUFFERED:
            if msg.sequence_num == expected_seq:
                msg.status = MessageStatus.DELIVERED
                self._delivered.append(msg.id)
                self._next_expected_seq[channel] = expected_seq + 1
                return msg
            else:
                # Gap detected — wait for the missing message
                return None

    return None
```

### 4. Float timestamp comparison with `==`

`t1 == t2` on floats fails due to precision (e.g., `0.1 + 0.2 != 0.3`).

Fix: use epsilon tolerance.

```python
EPSILON = 1e-6

def compare_timestamps(self, t1: float, t2: float) -> int:
    if abs(t1 - t2) < EPSILON:
        return 0
    return -1 if t1 < t2 else 1
```

Alternative: convert to integer milliseconds (`int(t * 1000)`) but this changes the data model — epsilon is less invasive.

---

## Feature Implementation Plan

### Feature 1: `MessageBuffer` with configurable timeout

A wrapper that holds messages for a configurable duration before releasing them for delivery. Allows out-of-order messages to arrive and be reordered within the timeout window.

```python
class MessageBuffer:
    def __init__(self, service: MessageOrderingService, timeout: float = 1.0):
        self._service = service
        self._timeout = timeout  # seconds to wait for reordering
        self._held: dict[str, float] = {}  # message_id -> buffered_at timestamp

    def buffer_message(self, message: Message) -> bool:
        added = self._service.add_message(message)
        if added:
            self._held[message.id] = time.time()
        return added

    def flush_ready(self, channel: str = "default") -> list[Message]:
        """Deliver messages that have waited long enough."""
        now = time.time()
        delivered = []
        while True:
            msg = self._service.deliver_next(channel)
            if msg is None:
                # Check if we should force-deliver due to timeout
                if self._should_force_deliver(channel, now):
                    self._skip_missing(channel)
                    continue
                break
            delivered.append(msg)
        return delivered

    def _should_force_deliver(self, channel, now):
        # If the oldest buffered message in this channel has waited > timeout
        ...

    def _skip_missing(self, channel):
        # Increment _next_expected_seq to skip the gap
        ...
```

### Feature 2: `acknowledge(message_id)`

Mark a delivered message as successfully processed.

```python
def acknowledge(self, message_id: str) -> bool:
    if message_id not in self.messages:
        return False
    msg = self.messages[message_id]
    if msg.status != MessageStatus.DELIVERED:
        return False
    msg.status = MessageStatus.ACKNOWLEDGED
    return True
```

### Feature 3: `get_unacknowledged()`

Return messages that are delivered but not yet acknowledged — candidates for retry.

```python
def get_unacknowledged(self) -> list[Message]:
    return [
        self.messages[mid]
        for mid in self._delivered
        if self.messages[mid].status == MessageStatus.DELIVERED
    ]
```

### Feature 4: Causal ordering (`depends_on` support)

Messages can declare `depends_on: list[str]` — IDs that must be delivered first. A message is only deliverable when all its dependencies have status `DELIVERED` or `ACKNOWLEDGED`.

Modify `deliver_next`:

```python
def _dependencies_met(self, message: Message) -> bool:
    for dep_id in message.depends_on:
        if dep_id not in self.messages:
            return False  # dependency not even received yet
        dep = self.messages[dep_id]
        if dep.status not in (MessageStatus.DELIVERED, MessageStatus.ACKNOWLEDGED):
            return False
    return True

def deliver_next(self, channel: str = "default") -> Optional[Message]:
    # ... existing logic ...
    for msg in ordered:
        if msg.status == MessageStatus.BUFFERED:
            if msg.sequence_num == expected_seq and self._dependencies_met(msg):
                # deliver
                ...
            else:
                return None
```

### Feature 5: `get_delivery_stats()`

Track metrics across the service lifetime. Add counters in `__init__` and increment in relevant methods.

```python
def __init__(self):
    # ... existing ...
    self._stats = {
        "total_received": 0,
        "delivered": 0,
        "duplicates_dropped": 0,
        "total_reorder_delay": 0.0,  # sum of (deliver_time - receive_time)
    }

def get_delivery_stats(self) -> dict:
    pending = sum(self.get_pending_count(ch) for ch in self.channels)
    delivered = self._stats["delivered"]
    avg_delay = (
        self._stats["total_reorder_delay"] / delivered if delivered > 0 else 0.0
    )
    return {
        "total_received": self._stats["total_received"],
        "delivered": delivered,
        "pending": pending,
        "duplicates_dropped": self._stats["duplicates_dropped"],
        "avg_reorder_delay": avg_delay,
    }
```

Increment `total_received` in `add_message`, `duplicates_dropped` when duplicate detected, `delivered` and `total_reorder_delay` in `deliver_next`.

### Feature 6: Tests

- **Duplicates**: add same message ID twice, second returns False, count stays 1
- **Sorted structure**: add messages out of order, `get_ordered_messages` returns correct order without explicit sort
- **Gap handling**: add seq 0 and seq 2, deliver returns seq 0 then None (waits for seq 1), add seq 1, deliver returns seq 1 then seq 2
- **Float comparison**: `compare_timestamps(0.1 + 0.2, 0.3)` returns 0
- **MessageBuffer timeout**: buffer messages, verify they're held until timeout, verify force-delivery after timeout
- **acknowledge**: deliver then acknowledge, status changes to ACKNOWLEDGED
- **get_unacknowledged**: deliver 3 messages, ack 1, unacknowledged returns the other 2
- **Causal ordering**: msg B depends on msg A, deliver B first — blocked, deliver A — succeeds, then B succeeds
- **Stats**: run a sequence of operations, verify all counters are correct
