"""
Business Logic Module for Learning Pytest
==========================================
Organized in 3 levels: EASY, MEDIUM, HARD

Each section has real-world business logic patterns that teach
different pytest concepts.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum
from typing import Any

# =============================================================================
# LEVEL 1: EASY — Pure functions, basic classes, simple validation
# Concepts: basic assertions, parametrize, expected exceptions
# =============================================================================


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    if not isinstance(celsius, (int, float)):
        raise TypeError("Temperature must be a number")
    return celsius * 9 / 5 + 32


def fahrenheit_to_celsius(fahrenheit: float) -> float:
    """Convert Fahrenheit to Celsius."""
    if not isinstance(fahrenheit, (int, float)):
        raise TypeError("Temperature must be a number")
    return (fahrenheit - 32) * 5 / 9


def is_palindrome(text: str) -> bool:
    """Check if text is a palindrome (ignoring case/spaces/punctuation)."""
    if not isinstance(text, str):
        raise TypeError("Input must be a string")
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", text).lower()
    return cleaned == cleaned[::-1]


def fizzbuzz(n: int) -> str:
    """Return FizzBuzz result for a number."""
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError("Input must be an integer")
    if n <= 0:
        raise ValueError("Input must be a positive integer")
    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    return str(n)


def validate_email(email: str) -> bool:
    """Basic email validation."""
    if not isinstance(email, str):
        raise TypeError("Email must be a string")
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def flatten_list(nested: list) -> list:
    """Flatten a nested list of arbitrary depth."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


class Stack:
    """Simple stack implementation."""

    def __init__(self, max_size: int | None = None):
        self._items: list = []
        self._max_size = max_size

    def push(self, item: Any) -> None:
        if self._max_size is not None and len(self._items) >= self._max_size:
            raise OverflowError("Stack is full")
        self._items.append(item)

    def pop(self) -> Any:
        if not self._items:
            raise IndexError("Pop from empty stack")
        return self._items.pop()

    def peek(self) -> Any:
        if not self._items:
            raise IndexError("Peek at empty stack")
        return self._items[-1]

    @property
    def size(self) -> int:
        return len(self._items)

    @property
    def is_empty(self) -> bool:
        return len(self._items) == 0


# =============================================================================
# LEVEL 2: MEDIUM — Stateful classes, dependency injection, side effects
# Concepts: fixtures, mocking, monkeypatch, tmp_path, parametrize with ids,
#           setup/teardown, conftest patterns, marker usage
# =============================================================================


class PasswordPolicy:
    """Configurable password validation with policy rules."""

    def __init__(
        self,
        min_length: int = 8,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        max_consecutive_chars: int = 3,
        blacklisted_passwords: list[str] | None = None,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.max_consecutive_chars = max_consecutive_chars
        self.blacklisted_passwords = [p.lower() for p in (blacklisted_passwords or [])]

    def validate(self, password: str) -> tuple[bool, list[str]]:
        """Returns (is_valid, list_of_errors)."""
        errors = []

        if len(password) < self.min_length:
            errors.append(f"Must be at least {self.min_length} characters")

        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Must contain an uppercase letter")

        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Must contain a lowercase letter")

        if self.require_digit and not re.search(r"\d", password):
            errors.append("Must contain a digit")

        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Must contain a special character")

        # Check consecutive characters
        for i in range(len(password) - self.max_consecutive_chars + 1):
            chunk = password[i : i + self.max_consecutive_chars]
            if len(set(chunk)) == 1:
                errors.append("Too many consecutive identical characters")
                break

        if password.lower() in self.blacklisted_passwords:
            errors.append("Password is blacklisted")

        return (len(errors) == 0, errors)


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"


@dataclass
class Money:
    """Precise monetary calculations using Decimal."""

    amount: Decimal
    currency: Currency

    def __post_init__(self):
        if isinstance(self.amount, float):
            raise TypeError("Use str or Decimal for amount, not float (precision loss)")
        if isinstance(self.amount, (int, str)):
            self.amount = Decimal(str(self.amount))
        self.amount = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot add {self.currency.value} and {other.currency.value}"
            )
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError(
                f"Cannot subtract {other.currency.value} from {self.currency.value}"
            )
        return Money(self.amount - other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> Money:
        if isinstance(factor, float):
            raise TypeError("Use int or Decimal as multiplier")
        return Money(self.amount * Decimal(str(factor)), self.currency)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        return self.amount == other.amount and self.currency == other.currency

    def split(self, parts: int) -> list[Money]:
        """Split money into N parts without losing cents."""
        if parts <= 0:
            raise ValueError("Parts must be positive")
        base = (self.amount / parts).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_base = base * parts
        remainder_cents = int((self.amount - total_base) * 100)

        result = [Money(base, self.currency) for _ in range(parts)]
        # Distribute remainder cents
        for i in range(abs(remainder_cents)):
            if remainder_cents > 0:
                result[i] = Money(result[i].amount + Decimal("0.01"), self.currency)
            else:
                result[i] = Money(result[i].amount - Decimal("0.01"), self.currency)
        return result


class FileProcessor:
    """Processes files — good for testing with tmp_path and mocking."""

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self._processed_count = 0

    def read_csv_data(self, filename: str) -> list[dict[str, str]]:
        """Read a CSV file and return list of row dicts."""
        import csv
        from pathlib import Path

        filepath = Path(self.base_dir) / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        if not filename.endswith(".csv"):
            raise ValueError("Only CSV files are supported")

        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            data = list(reader)
        self._processed_count += 1
        return data

    def write_report(self, filename: str, data: list[dict]) -> str:
        """Write a JSON report file. Returns the file path."""
        import json
        from pathlib import Path

        filepath = Path(self.base_dir) / filename
        with open(filepath, "w") as f:
            json.dump(
                {"generated_at": datetime.now().isoformat(), "data": data}, f, indent=2
            )
        return str(filepath)

    @property
    def processed_count(self) -> int:
        return self._processed_count


class RateLimiter:
    """Token bucket rate limiter — good for testing time-dependent logic."""

    def __init__(self, max_tokens: int, refill_rate: float, time_fn=None):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self._tokens = float(max_tokens)
        self._time_fn = time_fn or time.monotonic
        self._last_refill = self._time_fn()

    def _refill(self):
        now = self._time_fn()
        elapsed = now - self._last_refill
        self._tokens = min(self.max_tokens, self._tokens + elapsed * self.refill_rate)
        self._last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if allowed."""
        if tokens > self.max_tokens:
            raise ValueError(f"Cannot acquire {tokens} tokens (max: {self.max_tokens})")
        self._refill()
        if self._tokens >= tokens:
            self._tokens -= tokens
            return True
        return False

    @property
    def available_tokens(self) -> float:
        self._refill()
        return self._tokens


class UserService:
    """Service with external dependency — good for mocking."""

    def __init__(self, db_client, email_client):
        self._db = db_client
        self._email = email_client

    def register_user(self, username: str, email: str, password: str) -> dict:
        """Register a new user."""
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not validate_email(email):
            raise ValueError("Invalid email address")

        existing = self._db.find_user_by_email(email)
        if existing:
            raise ValueError("Email already registered")

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user = {
            "id": secrets.token_hex(16),
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now().isoformat(),
        }

        self._db.save_user(user)
        self._email.send_welcome(email, username)
        return user

    def reset_password(self, email: str) -> str:
        """Initiate password reset. Returns reset token."""
        user = self._db.find_user_by_email(email)
        if not user:
            # Don't reveal whether email exists (security)
            return "If the email exists, a reset link has been sent."

        token = secrets.token_urlsafe(32)
        self._db.save_reset_token(
            user["id"], token, expires=datetime.now() + timedelta(hours=1)
        )
        self._email.send_reset_link(email, token)
        return "If the email exists, a reset link has been sent."


# =============================================================================
# LEVEL 3: HARD — Complex state machines, async-like patterns, concurrency,
#           database integration, property-based testing, advanced fixtures
# Concepts: conftest hierarchies, factory fixtures, parametrize matrices,
#           hypothesis/property-based testing, database fixtures,
#           context managers as fixtures, monkey-patching internals,
#           testing state machines, coverage edge cases
# =============================================================================


class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


# Valid state transitions
ORDER_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED, OrderStatus.CANCELLED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: {OrderStatus.REFUNDED},
    OrderStatus.CANCELLED: set(),
    OrderStatus.REFUNDED: set(),
}


@dataclass
class OrderItem:
    product_id: str
    name: str
    quantity: int
    unit_price: Decimal

    def __post_init__(self):
        if isinstance(self.unit_price, (int, str)):
            self.unit_price = Decimal(str(self.unit_price))
        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if self.unit_price < 0:
            raise ValueError("Unit price cannot be negative")

    @property
    def subtotal(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )


@dataclass
class DiscountRule:
    code: str
    discount_type: str  # "percentage" or "fixed"
    value: Decimal
    min_order_amount: Decimal = Decimal("0")
    max_uses: int | None = None
    valid_until: datetime | None = None
    applicable_products: list[str] | None = None  # None means all products

    _uses: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.value, (int, str)):
            self.value = Decimal(str(self.value))
        if isinstance(self.min_order_amount, (int, str)):
            self.min_order_amount = Decimal(str(self.min_order_amount))

    def is_valid(self, now: datetime | None = None) -> bool:
        now = now or datetime.now()
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses is not None and self._uses >= self.max_uses:
            return False
        return True

    def apply(self, amount: Decimal, product_ids: list[str] | None = None) -> Decimal:
        """Calculate the discount amount."""
        if amount < self.min_order_amount:
            return Decimal("0")

        if self.discount_type == "percentage":
            discount = (amount * self.value / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        elif self.discount_type == "fixed":
            discount = min(self.value, amount)
        else:
            raise ValueError(f"Unknown discount type: {self.discount_type}")

        self._uses += 1
        return discount


class Order:
    """Complex order with state machine, discounts, and business rules."""

    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.status = OrderStatus.PENDING
        self.items: list[OrderItem] = []
        self.discounts: list[DiscountRule] = []
        self._status_history: list[tuple[OrderStatus, datetime]] = [
            (OrderStatus.PENDING, datetime.now())
        ]
        self._notes: list[str] = []

    def add_item(self, item: OrderItem) -> None:
        if self.status != OrderStatus.PENDING:
            raise RuntimeError("Can only add items to pending orders")
        # Merge if same product
        for existing in self.items:
            if existing.product_id == item.product_id:
                existing.quantity += item.quantity
                return
        self.items.append(item)

    def remove_item(self, product_id: str) -> None:
        if self.status != OrderStatus.PENDING:
            raise RuntimeError("Can only remove items from pending orders")
        self.items = [i for i in self.items if i.product_id != product_id]

    def apply_discount(self, discount: DiscountRule) -> None:
        if self.status != OrderStatus.PENDING:
            raise RuntimeError("Can only apply discounts to pending orders")
        if not discount.is_valid():
            raise ValueError(f"Discount code '{discount.code}' is expired or exhausted")
        # Check for duplicate codes
        if any(d.code == discount.code for d in self.discounts):
            raise ValueError(f"Discount '{discount.code}' already applied")
        self.discounts.append(discount)

    @property
    def subtotal(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def total_discount(self) -> Decimal:
        total = Decimal("0")
        remaining = self.subtotal
        for discount in self.discounts:
            d = discount.apply(remaining)
            total += d
            remaining -= d
        return total

    @property
    def total(self) -> Decimal:
        result = self.subtotal - self.total_discount
        return max(result, Decimal("0"))

    def transition_to(self, new_status: OrderStatus) -> None:
        """Transition order to new status following the state machine rules."""
        allowed = ORDER_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise RuntimeError(
                f"Cannot transition from {self.status.value} to {new_status.value}. "
                f"Allowed: {[s.value for s in allowed]}"
            )

        if new_status == OrderStatus.CONFIRMED and not self.items:
            raise RuntimeError("Cannot confirm an order with no items")

        if new_status == OrderStatus.CANCELLED:
            self._notes.append(f"Order cancelled from {self.status.value} state")

        if new_status == OrderStatus.REFUNDED:
            self._notes.append(f"Refund initiated for {self.total}")

        self.status = new_status
        self._status_history.append((new_status, datetime.now()))

    @property
    def status_history(self) -> list[tuple[OrderStatus, datetime]]:
        return list(self._status_history)


class EventBus:
    """Pub/sub event system — tests observer pattern, callbacks, ordering."""

    def __init__(self):
        self._handlers: dict[str, list[tuple[int, Callable[..., Any]]]] = {}
        self._event_log: list[dict] = []

    def subscribe(
        self, event_type: str, handler: Callable[..., Any], priority: int = 0
    ) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append((priority, handler))
        self._handlers[event_type].sort(key=lambda x: -x[0])  # Higher priority first

    def unsubscribe(self, event_type: str, handler: Callable[..., Any]) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [
                (p, h) for p, h in self._handlers[event_type] if h is not handler
            ]

    def publish(self, event_type: str, data: dict | None = None) -> list[Any]:
        """Publish event, return list of handler results."""
        data = data or {}
        self._event_log.append(
            {
                "event_type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
        )
        results = []
        for _, handler in self._handlers.get(event_type, []):
            result = handler(event_type, data)
            results.append(result)
            # If handler returns {"stop_propagation": True}, stop
            if isinstance(result, dict) and result.get("stop_propagation"):
                break
        return results

    @property
    def event_log(self) -> list[dict]:
        return list(self._event_log)


class RetryPolicy:
    """Configurable retry with exponential backoff — tests time manipulation."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        retryable_exceptions: tuple = (Exception,),
        sleep_fn=None,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        self._sleep_fn = sleep_fn or time.sleep
        self._attempts: list[dict] = []

    def execute(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute fn with retries. Returns result or raises last exception."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                result = fn(*args, **kwargs)
                self._attempts.append(
                    {
                        "attempt": attempt + 1,
                        "status": "success",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                return result
            except self.retryable_exceptions as e:
                last_exception = e
                self._attempts.append(
                    {
                        "attempt": attempt + 1,
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                if attempt < self.max_retries:
                    delay = min(
                        self.base_delay * (self.exponential_base**attempt),
                        self.max_delay,
                    )
                    self._sleep_fn(delay)
            except Exception as e:
                # Non-retryable exception
                self._attempts.append(
                    {
                        "attempt": attempt + 1,
                        "status": "fatal",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                raise

        raise last_exception  # type: ignore

    @property
    def attempts(self) -> list[dict]:
        return list(self._attempts)


class CacheEntry:
    """Single cache entry with TTL."""

    def __init__(self, value: Any, ttl: float, created_at: float):
        self.value = value
        self.ttl = ttl
        self.created_at = created_at

    def is_expired(self, now: float) -> bool:
        return (now - self.created_at) >= self.ttl


class LRUCache:
    """LRU cache with TTL, max size, and eviction callbacks."""

    def __init__(
        self,
        max_size: int = 100,
        default_ttl: float = 300.0,
        on_evict: Callable[..., Any] | None = None,
        time_fn=None,
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._on_evict = on_evict
        self._time_fn = time_fn or time.monotonic
        self._store: dict[str, CacheEntry] = {}
        self._access_order: list[str] = []
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}

    def get(self, key: str) -> Any | None:
        if key in self._store:
            entry = self._store[key]
            if entry.is_expired(self._time_fn()):
                self._remove(key)
                self._stats["misses"] += 1
                return None
            # Move to end (most recently used)
            self._access_order.remove(key)
            self._access_order.append(key)
            self._stats["hits"] += 1
            return entry.value
        self._stats["misses"] += 1
        return None

    def put(self, key: str, value: Any, ttl: float | None = None) -> None:
        ttl = ttl if ttl is not None else self.default_ttl

        if key in self._store:
            self._access_order.remove(key)
        elif len(self._store) >= self.max_size:
            self._evict_lru()

        self._store[key] = CacheEntry(value, ttl, self._time_fn())
        self._access_order.append(key)

    def delete(self, key: str) -> bool:
        if key in self._store:
            self._remove(key)
            return True
        return False

    def _remove(self, key: str) -> None:
        if key in self._store:
            del self._store[key]
            self._access_order.remove(key)

    def _evict_lru(self) -> None:
        if self._access_order:
            oldest_key = self._access_order[0]
            entry = self._store[oldest_key]
            if self._on_evict:
                self._on_evict(oldest_key, entry.value)
            self._remove(oldest_key)
            self._stats["evictions"] += 1

    @property
    def stats(self) -> dict:
        return dict(self._stats)

    @property
    def size(self) -> int:
        return len(self._store)

    def clear(self) -> None:
        self._store.clear()
        self._access_order.clear()


class InMemoryDB:
    """In-memory database with transactions, rollback, and indexing.
    Great for testing context managers, transaction isolation, and error recovery.
    """

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        self._indexes: dict[
            str, dict[str, dict]
        ] = {}  # table -> field -> {value: [rows]}
        self._transaction_stack: list[dict[str, list[dict]]] = []
        self._in_transaction = False

    def create_table(self, name: str) -> None:
        if name in self._tables:
            raise ValueError(f"Table '{name}' already exists")
        self._tables[name] = []

    def create_index(self, table: str, field: str) -> None:
        """Create an index on a field for faster lookups."""
        if table not in self._tables:
            raise ValueError(f"Table '{table}' does not exist")
        if table not in self._indexes:
            self._indexes[table] = {}
        index: dict[str, list] = {}
        for row in self._tables[table]:
            val = row.get(field)
            if val is not None:
                key = str(val)
                index.setdefault(key, []).append(row)
        self._indexes[table][field] = index

    def insert(self, table: str, row: dict) -> dict:
        if table not in self._tables:
            raise ValueError(f"Table '{table}' does not exist")
        row = dict(row)  # Copy
        if "id" not in row:
            row["id"] = secrets.token_hex(8)
        self._tables[table].append(row)
        # Update indexes
        if table in self._indexes:
            for field, index in self._indexes[table].items():
                val = row.get(field)
                if val is not None:
                    index.setdefault(str(val), []).append(row)
        return row

    def find(self, table: str, **criteria) -> list[dict]:
        if table not in self._tables:
            raise ValueError(f"Table '{table}' does not exist")
        results = self._tables[table]
        for key, value in criteria.items():
            results = [r for r in results if r.get(key) == value]
        return results

    def find_one(self, table: str, **criteria) -> dict | None:
        results = self.find(table, **criteria)
        return results[0] if results else None

    def update(self, table: str, criteria: dict, updates: dict) -> int:
        """Update matching rows. Returns count of updated rows."""
        if table not in self._tables:
            raise ValueError(f"Table '{table}' does not exist")
        count = 0
        for row in self._tables[table]:
            if all(row.get(k) == v for k, v in criteria.items()):
                row.update(updates)
                count += 1
        return count

    def delete(self, table: str, **criteria) -> int:
        """Delete matching rows. Returns count of deleted rows."""
        if table not in self._tables:
            raise ValueError(f"Table '{table}' does not exist")
        before = len(self._tables[table])
        self._tables[table] = [
            r
            for r in self._tables[table]
            if not all(r.get(k) == v for k, v in criteria.items())
        ]
        return before - len(self._tables[table])

    @contextmanager
    def transaction(self):
        """Context manager for transactions with rollback on error."""
        import copy

        snapshot = copy.deepcopy(self._tables)
        self._transaction_stack.append(snapshot)
        self._in_transaction = True
        try:
            yield self
            self._transaction_stack.pop()
        except Exception:
            self._tables = self._transaction_stack.pop()
            self._in_transaction = len(self._transaction_stack) > 0
            raise
        finally:
            if not self._transaction_stack:
                self._in_transaction = False

    @property
    def in_transaction(self) -> bool:
        return self._in_transaction


class CircuitBreaker:
    """Circuit breaker pattern — tests state transitions and timing."""

    class State(Enum):
        CLOSED = "closed"  # Normal operation
        OPEN = "open"  # Failing, reject calls
        HALF_OPEN = "half_open"  # Testing if service recovered

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
        time_fn=None,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self._time_fn = time_fn or time.monotonic
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._call_log: list[dict] = []

    @property
    def state(self) -> State:
        if self._state == self.State.OPEN:
            if (
                self._last_failure_time is not None
                and (self._time_fn() - self._last_failure_time) >= self.recovery_timeout
            ):
                self._state = self.State.HALF_OPEN
                self._success_count = 0
        return self._state

    def call(self, fn: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        current_state = self.state

        if current_state == self.State.OPEN:
            self._call_log.append({"status": "rejected", "state": "open"})
            raise RuntimeError("Circuit breaker is OPEN — call rejected")

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _on_success(self):
        self._call_log.append({"status": "success", "state": self._state.value})
        if self._state == self.State.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.success_threshold:
                self._state = self.State.CLOSED
                self._failure_count = 0
        else:
            self._failure_count = 0

    def _on_failure(self):
        self._call_log.append({"status": "failure", "state": self._state.value})
        self._failure_count += 1
        self._last_failure_time = self._time_fn()

        if (
            self._state == self.State.HALF_OPEN
            or self._failure_count >= self.failure_threshold
        ):
            self._state = self.State.OPEN

    @property
    def call_log(self) -> list[dict]:
        return list(self._call_log)

    def reset(self) -> None:
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._call_log.clear()


class Pipeline:
    """Data transformation pipeline — tests composition, error handling, partial results."""

    def __init__(self):
        self._steps: list[tuple[str, Callable[..., Any]]] = []
        self._error_handler: Callable[..., Any] | None = None

    def add_step(self, name: str, fn: Callable[..., Any]) -> Pipeline:
        self._steps.append((name, fn))
        return self

    def on_error(self, handler: Callable[..., Any]) -> Pipeline:
        self._error_handler = handler
        return self

    def execute(self, data: Any) -> dict:
        """Execute all pipeline steps. Returns result with metadata."""
        results = {
            "input": data,
            "steps_completed": [],
            "steps_failed": [],
            "output": data,
            "success": True,
        }

        current = data
        for name, fn in self._steps:
            try:
                current = fn(current)
                results["steps_completed"].append(name)
                results["output"] = current
            except Exception as e:
                results["steps_failed"].append({"step": name, "error": str(e)})
                results["success"] = False
                if self._error_handler:
                    try:
                        current = self._error_handler(name, e, current)
                        results["output"] = current
                        continue
                    except Exception:
                        break
                else:
                    break

        return results

    def __len__(self) -> int:
        return len(self._steps)
