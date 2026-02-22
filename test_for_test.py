"""
Pytest Learning Guide — From Easy to Hard
==========================================

Run all tests:       pytest test_for_test.py -v
Run by marker:       pytest test_for_test.py -m easy -v
Run specific class:  pytest test_for_test.py::TestStack -v
Run specific test:   pytest test_for_test.py::TestStack::test_push_and_pop -v
Show print output:   pytest test_for_test.py -v -s
"""

import time
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

import pytest

from for_test import (
    # Easy
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    is_palindrome,
    fizzbuzz,
    validate_email,
    flatten_list,
    Stack,
    # Medium
    PasswordPolicy,
    Money,
    Currency,
    FileProcessor,
    RateLimiter,
    UserService,
    # Hard
    Order,
    OrderItem,
    OrderStatus,
    DiscountRule,
    EventBus,
    RetryPolicy,
    LRUCache,
    InMemoryDB,
    CircuitBreaker,
    Pipeline,
)


# =============================================================================
# LEVEL 1: EASY
# Concepts you'll learn:
#   - Basic assertions (==, !=, is, in, not)
#   - pytest.raises for exception testing
#   - @pytest.mark.parametrize for running same test with different data
#   - Simple test organization with classes
# =============================================================================


# --- 1. Simple function tests with parametrize ---

class TestTemperatureConversion:
    """
    CONCEPT: @pytest.mark.parametrize
    Runs the same test with multiple inputs. Avoids copy-pasting test functions.
    """

    @pytest.mark.parametrize("celsius, expected", [
        (0, 32),
        (100, 212),
        (-40, -40),       # The crossover point!
        (37, 98.6),       # Body temperature
    ])
    def test_celsius_to_fahrenheit(self, celsius, expected):
        result = celsius_to_fahrenheit(celsius)
        assert result == pytest.approx(expected)
        #                   ^^^^^^^^^^^^^^
        # pytest.approx handles floating point comparison
        # Without it: 0.1 + 0.2 != 0.3 (floating point issue)

    @pytest.mark.parametrize("fahrenheit, expected", [
        (32, 0),
        (212, 100),
        (-40, -40),
        (98.6, 37),
    ])
    def test_fahrenheit_to_celsius(self, fahrenheit, expected):
        assert fahrenheit_to_celsius(fahrenheit) == pytest.approx(expected)

    def test_roundtrip(self):
        """Convert C->F->C and verify we get back the original."""
        original = 25.0
        converted = fahrenheit_to_celsius(celsius_to_fahrenheit(original))
        assert converted == pytest.approx(original)

    def test_invalid_type_raises_error(self):
        """
        CONCEPT: pytest.raises
        Test that the function raises the correct exception.
        """
        with pytest.raises(TypeError, match="must be a number"):
            celsius_to_fahrenheit("hot")

        with pytest.raises(TypeError):
            fahrenheit_to_celsius(None)


# --- 2. Testing string functions ---

class TestIsPalindrome:

    @pytest.mark.parametrize("text, expected", [
        ("racecar", True),
        ("hello", False),
        ("A man a plan a canal Panama", True),  # Ignores spaces/case
        ("Was it a car or a cat I saw?", True),  # Ignores punctuation
        ("", True),                               # Edge case: empty string
        ("a", True),                              # Single char
        ("ab", False),
        ("12321", True),                           # Numbers work too
    ], ids=[
        "simple-palindrome",
        "not-palindrome",
        "with-spaces",
        "with-punctuation",
        "empty-string",
        "single-char",
        "two-chars",
        "numeric",
    ])
    #  ^^^^
    # CONCEPT: ids= gives each test case a readable name in output
    # Instead of: test_palindrome[racecar-True]
    # You see:    test_palindrome[simple-palindrome]
    def test_palindrome(self, text, expected):
        assert is_palindrome(text) == expected

    def test_type_error(self):
        with pytest.raises(TypeError):
            is_palindrome(123)


# --- 3. FizzBuzz — classic parametrize ---

class TestFizzBuzz:

    @pytest.mark.parametrize("n, expected", [
        (1, "1"),
        (2, "2"),
        (3, "Fizz"),
        (5, "Buzz"),
        (15, "FizzBuzz"),
        (30, "FizzBuzz"),
        (9, "Fizz"),
        (25, "Buzz"),
    ])
    def test_fizzbuzz_values(self, n, expected):
        assert fizzbuzz(n) == expected

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            fizzbuzz(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            fizzbuzz(-5)

    def test_bool_raises(self):
        """bool is subclass of int in Python — make sure we reject it."""
        with pytest.raises(TypeError):
            fizzbuzz(True)


# --- 4. Email validation ---

class TestEmailValidation:

    @pytest.mark.parametrize("email", [
        "user@example.com",
        "first.last@company.org",
        "test+tag@gmail.com",
        "user123@sub.domain.co",
    ])
    def test_valid_emails(self, email):
        assert validate_email(email) is True

    @pytest.mark.parametrize("email", [
        "",
        "not-an-email",
        "@missing-local.com",
        "missing-domain@",
        "missing@.com",
        "spaces in@email.com",
        "user@com",           # No TLD dot
    ])
    def test_invalid_emails(self, email):
        assert validate_email(email) is False


# --- 5. Nested list flattening ---

class TestFlattenList:

    def test_already_flat(self):
        assert flatten_list([1, 2, 3]) == [1, 2, 3]

    def test_one_level_deep(self):
        assert flatten_list([1, [2, 3], 4]) == [1, 2, 3, 4]

    def test_deeply_nested(self):
        assert flatten_list([1, [2, [3, [4, [5]]]]]) == [1, 2, 3, 4, 5]

    def test_empty(self):
        assert flatten_list([]) == []

    def test_mixed_types(self):
        assert flatten_list([1, ["a", [True, [None]]]]) == [1, "a", True, None]


# --- 6. Stack class — testing stateful objects ---

class TestStack:
    """
    CONCEPT: Testing stateful objects
    Each test starts with a fresh stack (no shared state between tests).
    """

    def test_push_and_pop(self):
        s = Stack()
        s.push(1)
        s.push(2)
        assert s.pop() == 2  # LIFO
        assert s.pop() == 1

    def test_peek_does_not_remove(self):
        s = Stack()
        s.push(42)
        assert s.peek() == 42
        assert s.size == 1  # Still there

    def test_is_empty(self):
        s = Stack()
        assert s.is_empty is True
        s.push("x")
        assert s.is_empty is False

    def test_pop_empty_raises(self):
        with pytest.raises(IndexError, match="empty"):
            Stack().pop()

    def test_peek_empty_raises(self):
        with pytest.raises(IndexError, match="empty"):
            Stack().peek()

    def test_max_size(self):
        """Test that stack respects max_size limit."""
        s = Stack(max_size=2)
        s.push(1)
        s.push(2)
        with pytest.raises(OverflowError, match="full"):
            s.push(3)


# =============================================================================
# LEVEL 2: MEDIUM
# Concepts you'll learn:
#   - Fixtures (setup reusable test objects)
#   - @pytest.fixture with scope and params
#   - Mocking with unittest.mock (MagicMock, patch)
#   - monkeypatch (pytest's built-in mocking)
#   - tmp_path for file system tests
#   - Testing time-dependent code
#   - Nested parametrize (test matrices)
# =============================================================================


# --- 7. Password Policy with fixtures ---

class TestPasswordPolicy:
    """
    CONCEPT: Fixtures
    Fixtures provide reusable setup for tests. They're functions decorated
    with @pytest.fixture that tests can request by parameter name.
    """

    @pytest.fixture
    def default_policy(self):
        """A fixture that provides a default PasswordPolicy."""
        return PasswordPolicy()

    @pytest.fixture
    def strict_policy(self):
        """A stricter policy for testing."""
        return PasswordPolicy(
            min_length=12,
            max_consecutive_chars=2,
            blacklisted_passwords=["password123", "admin123"],
        )

    def test_valid_password(self, default_policy):
        #                       ^^^^^^^^^^^^^^
        # pytest sees this parameter name matches a fixture and auto-injects it
        is_valid, errors = default_policy.validate("MyStr0ng!Pass")
        assert is_valid is True
        assert errors == []

    def test_too_short(self, default_policy):
        is_valid, errors = default_policy.validate("Ab1!")
        assert is_valid is False
        assert any("at least 8" in e for e in errors)

    def test_missing_uppercase(self, default_policy):
        is_valid, errors = default_policy.validate("lowercase1!")
        assert is_valid is False
        assert "uppercase" in errors[0].lower()

    def test_missing_digit(self, default_policy):
        is_valid, errors = default_policy.validate("NoDigits!Here")
        assert is_valid is False
        assert any("digit" in e for e in errors)

    def test_consecutive_chars(self, default_policy):
        is_valid, errors = default_policy.validate("Passsword1!")
        #                                              ^^^  three 's' in a row
        assert is_valid is False
        assert any("consecutive" in e for e in errors)

    def test_blacklisted_password(self):
        """
        Blacklist comparison is case-insensitive and must be an exact match.
        We create a policy with a known blacklisted password to test.
        """
        policy = PasswordPolicy(
            min_length=8,
            blacklisted_passwords=["MyStr0ng!Pass"],
        )
        is_valid, errors = policy.validate("MyStr0ng!Pass")
        assert is_valid is False
        assert any("blacklisted" in e.lower() for e in errors)

    def test_multiple_errors_returned(self, default_policy):
        """A terrible password should return multiple errors."""
        is_valid, errors = default_policy.validate("aa")
        assert is_valid is False
        assert len(errors) >= 3  # Too short + missing uppercase + missing digit + ...


# --- 8. Money class — testing value objects ---

class TestMoney:
    """
    CONCEPT: Testing value objects and operator overloading
    """

    def test_create_from_string(self):
        m = Money("10.50", Currency.USD)
        assert m.amount == Decimal("10.50")

    def test_create_from_int(self):
        m = Money(10, Currency.USD)
        assert m.amount == Decimal("10.00")

    def test_float_rejected(self):
        """Floats cause precision loss — Money should reject them."""
        with pytest.raises(TypeError, match="not float"):
            Money(10.50, Currency.USD)

    def test_addition(self):
        a = Money("10.00", Currency.USD)
        b = Money("5.50", Currency.USD)
        result = a + b
        assert result == Money("15.50", Currency.USD)

    def test_add_different_currencies_raises(self):
        with pytest.raises(ValueError, match="Cannot add"):
            Money("10.00", Currency.USD) + Money("5.00", Currency.EUR)

    def test_subtraction(self):
        result = Money("20.00", Currency.EUR) - Money("7.50", Currency.EUR)
        assert result == Money("12.50", Currency.EUR)

    def test_multiplication(self):
        m = Money("10.00", Currency.USD)
        result = m * 3
        assert result == Money("30.00", Currency.USD)

    def test_multiply_by_float_rejected(self):
        with pytest.raises(TypeError):
            Money("10.00", Currency.USD) * 1.5

    def test_split_evenly(self):
        m = Money("30.00", Currency.USD)
        parts = m.split(3)
        assert len(parts) == 3
        assert all(p == Money("10.00", Currency.USD) for p in parts)

    def test_split_with_remainder(self):
        """$10 split 3 ways: two get $3.34, one gets $3.33 (or similar)."""
        m = Money("10.00", Currency.USD)
        parts = m.split(3)
        assert len(parts) == 3
        # The key invariant: total must equal original amount
        total = sum(p.amount for p in parts)
        assert total == Decimal("10.00")

    def test_rounding(self):
        """Verify banker's rounding to 2 decimal places."""
        m = Money("10.555", Currency.USD)
        assert m.amount == Decimal("10.56")  # Rounded up


# --- 9. File processing with tmp_path ---

class TestFileProcessor:
    """
    CONCEPT: tmp_path fixture
    pytest provides tmp_path (a pathlib.Path) that creates a unique
    temporary directory for each test. Automatically cleaned up.
    """

    @pytest.fixture
    def processor(self, tmp_path):
        """
        CONCEPT: Fixtures can use other fixtures!
        This fixture requests tmp_path (built-in) and uses it.
        """
        return FileProcessor(str(tmp_path))

    @pytest.fixture
    def sample_csv(self, tmp_path):
        """Create a sample CSV file for testing."""
        csv_file = tmp_path / "users.csv"
        csv_file.write_text("name,email,age\nAlice,alice@test.com,30\nBob,bob@test.com,25\n")
        return csv_file

    def test_read_csv(self, processor, sample_csv):
        data = processor.read_csv_data("users.csv")
        assert len(data) == 2
        assert data[0]["name"] == "Alice"
        assert data[1]["age"] == "25"

    def test_read_missing_file(self, processor):
        with pytest.raises(FileNotFoundError):
            processor.read_csv_data("nonexistent.csv")

    def test_read_non_csv(self, processor, tmp_path):
        (tmp_path / "data.txt").write_text("hello")
        with pytest.raises(ValueError, match="CSV"):
            processor.read_csv_data("data.txt")

    def test_write_report(self, processor, tmp_path):
        data = [{"name": "Test", "value": 42}]
        path = processor.write_report("report.json", data)
        import json
        with open(path) as f:
            report = json.load(f)
        assert "generated_at" in report
        assert report["data"] == data

    def test_processed_count(self, processor, sample_csv):
        assert processor.processed_count == 0
        processor.read_csv_data("users.csv")
        assert processor.processed_count == 1
        processor.read_csv_data("users.csv")
        assert processor.processed_count == 2


# --- 10. Rate limiter — testing time-dependent logic ---

class TestRateLimiter:
    """
    CONCEPT: Dependency injection for time
    Instead of mocking time.monotonic globally, we inject a fake
    time function. This is a cleaner pattern for testing time.
    """

    def test_allows_within_limit(self):
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        for _ in range(5):
            assert limiter.acquire() is True

    def test_blocks_when_exhausted(self):
        limiter = RateLimiter(max_tokens=2, refill_rate=1.0)
        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is False  # No tokens left

    def test_tokens_refill_over_time(self):
        """
        CONCEPT: Fake time function
        We control time progression without actually sleeping.
        """
        current_time = [0.0]  # Mutable container so inner fn can modify

        def fake_time():
            return current_time[0]

        limiter = RateLimiter(max_tokens=2, refill_rate=1.0, time_fn=fake_time)

        # Use all tokens
        limiter.acquire()
        limiter.acquire()
        assert limiter.acquire() is False

        # Advance time by 1 second (refill_rate=1.0 → 1 token/sec)
        current_time[0] += 1.0
        assert limiter.acquire() is True  # Got a token back!

    def test_cannot_exceed_max_tokens(self):
        current_time = [0.0]
        limiter = RateLimiter(max_tokens=3, refill_rate=10.0, time_fn=lambda: current_time[0])

        # Even after a long time, should cap at max_tokens
        current_time[0] += 1000.0
        assert limiter.available_tokens == pytest.approx(3.0)

    def test_acquire_more_than_max_raises(self):
        limiter = RateLimiter(max_tokens=5, refill_rate=1.0)
        with pytest.raises(ValueError, match="Cannot acquire"):
            limiter.acquire(tokens=10)


# --- 11. UserService — mocking external dependencies ---

class TestUserService:
    """
    CONCEPT: Mocking with MagicMock
    UserService depends on db_client and email_client.
    We create mock objects to test UserService in isolation.
    """

    @pytest.fixture
    def mock_db(self):
        """
        CONCEPT: MagicMock
        MagicMock creates an object that accepts any method call
        and records what was called with what arguments.
        """
        db = MagicMock()
        db.find_user_by_email.return_value = None  # No existing user by default
        return db

    @pytest.fixture
    def mock_email(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db, mock_email):
        return UserService(mock_db, mock_email)

    def test_register_success(self, service, mock_db, mock_email):
        user = service.register_user("alice", "alice@test.com", "secret123")

        # Verify user dict structure
        assert user["username"] == "alice"
        assert user["email"] == "alice@test.com"
        assert "password_hash" in user
        assert "id" in user

        # Verify mock interactions
        mock_db.find_user_by_email.assert_called_once_with("alice@test.com")
        mock_db.save_user.assert_called_once()
        mock_email.send_welcome.assert_called_once_with("alice@test.com", "alice")

    def test_register_duplicate_email(self, service, mock_db):
        mock_db.find_user_by_email.return_value = {"id": "existing"}
        #                                          ^^^^^^^^^^^^^^^^^
        # Simulate: user already exists in DB

        with pytest.raises(ValueError, match="already registered"):
            service.register_user("alice", "alice@test.com", "secret")

        # Verify we did NOT save a new user or send email
        mock_db.save_user.assert_not_called()

    def test_register_invalid_email(self, service):
        with pytest.raises(ValueError, match="Invalid email"):
            service.register_user("alice", "not-an-email", "secret")

    def test_register_short_username(self, service):
        with pytest.raises(ValueError, match="at least 3"):
            service.register_user("ab", "a@b.com", "secret")

    def test_password_is_hashed(self, service, mock_db):
        """Verify password is not stored in plaintext."""
        service.register_user("alice", "alice@test.com", "my_secret_password")

        saved_user = mock_db.save_user.call_args[0][0]
        assert saved_user["password_hash"] != "my_secret_password"
        assert len(saved_user["password_hash"]) == 64  # SHA-256 hex digest

    def test_reset_password_existing_user(self, service, mock_db, mock_email):
        mock_db.find_user_by_email.return_value = {"id": "user123", "email": "a@b.com"}
        result = service.reset_password("a@b.com")

        assert "reset link has been sent" in result
        mock_db.save_reset_token.assert_called_once()
        mock_email.send_reset_link.assert_called_once()

    def test_reset_password_nonexistent_user(self, service, mock_db, mock_email):
        """
        CONCEPT: Security testing
        Should return the SAME message whether user exists or not
        (prevents email enumeration attacks).
        """
        mock_db.find_user_by_email.return_value = None
        result = service.reset_password("nobody@test.com")

        assert "reset link has been sent" in result
        mock_db.save_reset_token.assert_not_called()
        mock_email.send_reset_link.assert_not_called()


# =============================================================================
# LEVEL 3: HARD
# Concepts you'll learn:
#   - Complex fixture patterns (factories, parametrized fixtures)
#   - Testing state machines (all transitions)
#   - Context managers as test subjects
#   - Testing callbacks and event ordering
#   - Testing retry/backoff logic
#   - Eviction/expiry testing in caches
#   - Parametrize matrices (multiple parametrize stacked)
#   - Testing pipelines with partial failures
#   - Testing concurrency-related patterns
# =============================================================================


# --- 12. Order state machine — exhaustive transition testing ---

class TestOrderStateMachine:
    """
    CONCEPT: Factory fixtures
    When tests need slightly different versions of the same object,
    use a factory fixture (a fixture that returns a function).
    """

    @pytest.fixture
    def make_item(self):
        """
        CONCEPT: Factory fixture
        Returns a function that creates OrderItems with defaults.
        Each test can customize what it needs.
        """
        def _make(product_id="PROD-1", name="Widget", quantity=1, unit_price="10.00"):
            return OrderItem(product_id, name, quantity, Decimal(unit_price))
        return _make

    @pytest.fixture
    def pending_order(self, make_item):
        order = Order("ORD-1", "CUST-1")
        order.add_item(make_item())
        return order

    @pytest.fixture
    def confirmed_order(self, pending_order):
        """
        CONCEPT: Fixture composition
        Build on top of other fixtures to create specific states.
        """
        pending_order.transition_to(OrderStatus.CONFIRMED)
        return pending_order

    # --- Valid transitions ---

    def test_pending_to_confirmed(self, pending_order):
        pending_order.transition_to(OrderStatus.CONFIRMED)
        assert pending_order.status == OrderStatus.CONFIRMED

    def test_pending_to_cancelled(self, pending_order):
        pending_order.transition_to(OrderStatus.CANCELLED)
        assert pending_order.status == OrderStatus.CANCELLED

    def test_confirmed_to_processing(self, confirmed_order):
        confirmed_order.transition_to(OrderStatus.PROCESSING)
        assert confirmed_order.status == OrderStatus.PROCESSING

    def test_full_happy_path(self, pending_order):
        """Test the complete lifecycle."""
        pending_order.transition_to(OrderStatus.CONFIRMED)
        pending_order.transition_to(OrderStatus.PROCESSING)
        pending_order.transition_to(OrderStatus.SHIPPED)
        pending_order.transition_to(OrderStatus.DELIVERED)
        assert pending_order.status == OrderStatus.DELIVERED
        assert len(pending_order.status_history) == 5

    def test_delivered_to_refunded(self, pending_order):
        pending_order.transition_to(OrderStatus.CONFIRMED)
        pending_order.transition_to(OrderStatus.PROCESSING)
        pending_order.transition_to(OrderStatus.SHIPPED)
        pending_order.transition_to(OrderStatus.DELIVERED)
        pending_order.transition_to(OrderStatus.REFUNDED)
        assert pending_order.status == OrderStatus.REFUNDED

    # --- Invalid transitions ---

    @pytest.mark.parametrize("invalid_target", [
        OrderStatus.PROCESSING,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.REFUNDED,
    ])
    def test_pending_invalid_transitions(self, pending_order, invalid_target):
        """
        CONCEPT: Parametrize over enum values
        Test that all invalid transitions from PENDING are rejected.
        """
        with pytest.raises(RuntimeError, match="Cannot transition"):
            pending_order.transition_to(invalid_target)

    def test_cannot_transition_from_cancelled(self, pending_order):
        pending_order.transition_to(OrderStatus.CANCELLED)
        for status in OrderStatus:
            if status != OrderStatus.CANCELLED:
                with pytest.raises(RuntimeError):
                    pending_order.transition_to(status)

    def test_confirm_empty_order_fails(self):
        order = Order("ORD-1", "CUST-1")  # No items
        with pytest.raises(RuntimeError, match="no items"):
            order.transition_to(OrderStatus.CONFIRMED)

    # --- Item management ---

    def test_add_item_merges_same_product(self, make_item):
        order = Order("ORD-1", "CUST-1")
        order.add_item(make_item(product_id="A", quantity=2))
        order.add_item(make_item(product_id="A", quantity=3))
        assert len(order.items) == 1
        assert order.items[0].quantity == 5

    def test_cannot_add_item_after_confirmed(self, confirmed_order, make_item):
        with pytest.raises(RuntimeError, match="pending"):
            confirmed_order.add_item(make_item())

    # --- Pricing with discounts ---

    def test_subtotal_calculation(self, make_item):
        order = Order("ORD-1", "CUST-1")
        order.add_item(make_item(unit_price="10.00", quantity=3))
        order.add_item(make_item(product_id="P2", unit_price="5.50", quantity=2))
        assert order.subtotal == Decimal("41.00")

    def test_percentage_discount(self, pending_order):
        discount = DiscountRule(code="SAVE10", discount_type="percentage", value=Decimal("10"))
        pending_order.apply_discount(discount)
        # 10% of $10.00 = $1.00
        assert pending_order.total == Decimal("9.00")

    def test_fixed_discount(self, pending_order):
        discount = DiscountRule(code="FIVE_OFF", discount_type="fixed", value=Decimal("5"))
        pending_order.apply_discount(discount)
        assert pending_order.total == Decimal("5.00")

    def test_discount_cannot_go_negative(self, pending_order):
        discount = DiscountRule(code="BIG", discount_type="fixed", value=Decimal("999"))
        pending_order.apply_discount(discount)
        assert pending_order.total == Decimal("0.00")

    def test_stacked_discounts(self, make_item):
        order = Order("ORD-1", "CUST-1")
        order.add_item(make_item(unit_price="100.00"))

        d1 = DiscountRule(code="FIRST", discount_type="percentage", value=Decimal("10"))
        d2 = DiscountRule(code="SECOND", discount_type="fixed", value=Decimal("5"))
        order.apply_discount(d1)
        order.apply_discount(d2)

        # $100 - 10% ($10) = $90, then - $5 = $85
        assert order.total == Decimal("85.00")

    def test_duplicate_discount_code_rejected(self, pending_order):
        d = DiscountRule(code="SAVE", discount_type="fixed", value=Decimal("1"))
        pending_order.apply_discount(d)
        with pytest.raises(ValueError, match="already applied"):
            pending_order.apply_discount(
                DiscountRule(code="SAVE", discount_type="fixed", value=Decimal("2"))
            )

    def test_expired_discount_rejected(self, pending_order):
        d = DiscountRule(
            code="OLD",
            discount_type="fixed",
            value=Decimal("5"),
            valid_until=datetime(2020, 1, 1),
        )
        with pytest.raises(ValueError, match="expired"):
            pending_order.apply_discount(d)


# --- 13. EventBus — testing callbacks, ordering, and stop propagation ---

class TestEventBus:
    """
    CONCEPT: Testing callbacks and side effects
    Use lists to capture call order and verify behavior.
    """

    @pytest.fixture
    def bus(self):
        return EventBus()

    def test_basic_publish_subscribe(self, bus):
        received = []
        bus.subscribe("user.created", lambda evt, data: received.append(data))

        bus.publish("user.created", {"name": "Alice"})
        assert received == [{"name": "Alice"}]

    def test_multiple_subscribers(self, bus):
        results = []
        bus.subscribe("click", lambda e, d: results.append("A"))
        bus.subscribe("click", lambda e, d: results.append("B"))

        bus.publish("click")
        assert results == ["A", "B"]

    def test_priority_ordering(self, bus):
        """Higher priority handlers run first."""
        order = []
        bus.subscribe("evt", lambda e, d: order.append("low"), priority=1)
        bus.subscribe("evt", lambda e, d: order.append("high"), priority=10)
        bus.subscribe("evt", lambda e, d: order.append("mid"), priority=5)

        bus.publish("evt")
        assert order == ["high", "mid", "low"]

    def test_stop_propagation(self, bus):
        """A handler can stop further handlers from running."""
        order = []
        bus.subscribe("evt", lambda e, d: (order.append("first"), {"stop_propagation": True})[1], priority=10)
        bus.subscribe("evt", lambda e, d: order.append("second"), priority=1)

        bus.publish("evt")
        assert order == ["first"]  # "second" was not called

    def test_unsubscribe(self, bus):
        called = []
        handler = lambda e, d: called.append(True)
        bus.subscribe("evt", handler)

        bus.publish("evt")
        assert len(called) == 1

        bus.unsubscribe("evt", handler)
        bus.publish("evt")
        assert len(called) == 1  # Not called again

    def test_event_log(self, bus):
        bus.subscribe("a", lambda e, d: None)
        bus.publish("a", {"x": 1})
        bus.publish("b", {"y": 2})

        log = bus.event_log
        assert len(log) == 2
        assert log[0]["event_type"] == "a"
        assert log[1]["data"] == {"y": 2}

    def test_no_subscribers_still_logs(self, bus):
        bus.publish("orphan_event", {"data": "test"})
        assert len(bus.event_log) == 1


# --- 14. RetryPolicy — testing exponential backoff ---

class TestRetryPolicy:
    """
    CONCEPT: Testing retry logic without real delays
    Inject a fake sleep function to verify backoff timing.
    """

    def test_success_first_try(self):
        policy = RetryPolicy(max_retries=3, sleep_fn=lambda x: None)
        result = policy.execute(lambda: "ok")
        assert result == "ok"
        assert len(policy.attempts) == 1
        assert policy.attempts[0]["status"] == "success"

    def test_success_after_retries(self):
        call_count = [0]

        def flaky():
            call_count[0] += 1
            if call_count[0] < 3:
                raise ConnectionError("fail")
            return "recovered"

        policy = RetryPolicy(max_retries=5, sleep_fn=lambda x: None)
        result = policy.execute(flaky)
        assert result == "recovered"
        assert len(policy.attempts) == 3

    def test_all_retries_exhausted(self):
        policy = RetryPolicy(max_retries=2, sleep_fn=lambda x: None)
        with pytest.raises(ConnectionError):
            policy.execute(lambda: (_ for _ in ()).throw(ConnectionError("down")))

    def test_exponential_backoff_delays(self):
        """Verify the sleep delays follow exponential backoff."""
        delays = []

        def capture_sleep(delay):
            delays.append(delay)

        def always_fail():
            raise ValueError("boom")

        policy = RetryPolicy(
            max_retries=4,
            base_delay=1.0,
            exponential_base=2.0,
            max_delay=60.0,
            sleep_fn=capture_sleep,
        )

        with pytest.raises(ValueError):
            policy.execute(always_fail)

        # Expected: 1.0, 2.0, 4.0, 8.0
        assert delays == [1.0, 2.0, 4.0, 8.0]

    def test_max_delay_cap(self):
        delays = []
        policy = RetryPolicy(
            max_retries=5,
            base_delay=10.0,
            exponential_base=3.0,
            max_delay=50.0,
            sleep_fn=lambda d: delays.append(d),
        )
        with pytest.raises(ValueError):
            policy.execute(lambda: (_ for _ in ()).throw(ValueError()))

        # All delays should be <= max_delay
        assert all(d <= 50.0 for d in delays)

    def test_non_retryable_exception_not_retried(self):
        """Only specified exceptions should be retried."""
        policy = RetryPolicy(
            max_retries=5,
            retryable_exceptions=(ConnectionError,),
            sleep_fn=lambda x: None,
        )

        with pytest.raises(TypeError):
            policy.execute(lambda: (_ for _ in ()).throw(TypeError("not retryable")))

        assert len(policy.attempts) == 1
        assert policy.attempts[0]["status"] == "fatal"


# --- 15. LRU Cache — testing eviction, TTL, and stats ---

class TestLRUCache:
    """
    CONCEPT: Complex stateful testing
    Test cache behavior: hits, misses, eviction order, TTL expiry.
    """

    @pytest.fixture
    def fake_time(self):
        """
        CONCEPT: Controllable time
        Returns a mutable time controller for deterministic tests.
        """
        class FakeTime:
            def __init__(self):
                self.now = 0.0

            def __call__(self):
                return self.now

            def advance(self, seconds: float):
                self.now += seconds

        return FakeTime()

    @pytest.fixture
    def cache(self, fake_time):
        return LRUCache(max_size=3, default_ttl=60.0, time_fn=fake_time)

    def test_put_and_get(self, cache):
        cache.put("key", "value")
        assert cache.get("key") == "value"

    def test_get_missing_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self, cache, fake_time):
        """Least recently used item is evicted when cache is full."""
        cache.put("a", 1)
        fake_time.advance(1)
        cache.put("b", 2)
        fake_time.advance(1)
        cache.put("c", 3)
        fake_time.advance(1)

        # Cache is full (max_size=3). Adding "d" should evict "a" (least recent)
        cache.put("d", 4)

        assert cache.get("a") is None  # Evicted
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4

    def test_access_updates_lru_order(self, cache, fake_time):
        """Accessing an item makes it 'recently used', so it's evicted later."""
        cache.put("a", 1)
        fake_time.advance(1)
        cache.put("b", 2)
        fake_time.advance(1)
        cache.put("c", 3)
        fake_time.advance(1)

        # Access "a" — now "b" is least recently used
        cache.get("a")
        fake_time.advance(1)

        cache.put("d", 4)  # Should evict "b", not "a"

        assert cache.get("a") == 1  # Still here (was accessed)
        assert cache.get("b") is None  # Evicted
        assert cache.get("d") == 4

    def test_ttl_expiry(self, cache, fake_time):
        cache.put("key", "value", ttl=10.0)
        assert cache.get("key") == "value"

        fake_time.advance(10.0)
        assert cache.get("key") is None  # Expired

    def test_stats_tracking(self, cache):
        cache.put("a", 1)
        cache.get("a")     # Hit
        cache.get("b")     # Miss
        cache.get("a")     # Hit

        stats = cache.stats
        assert stats["hits"] == 2
        assert stats["misses"] == 1

    def test_eviction_callback(self, fake_time):
        """
        CONCEPT: Testing callbacks
        Verify the on_evict callback is called with correct args.
        """
        evicted = []
        cache = LRUCache(
            max_size=2,
            on_evict=lambda k, v: evicted.append((k, v)),
            time_fn=fake_time,
        )

        cache.put("a", 1)
        fake_time.advance(1)
        cache.put("b", 2)
        fake_time.advance(1)
        cache.put("c", 3)  # Evicts "a"

        assert evicted == [("a", 1)]

    def test_delete(self, cache):
        cache.put("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None
        assert cache.delete("key") is False  # Already gone

    def test_clear(self, cache):
        cache.put("a", 1)
        cache.put("b", 2)
        cache.clear()
        assert cache.size == 0
        assert cache.get("a") is None


# --- 16. InMemoryDB — testing transactions and rollback ---

class TestInMemoryDB:
    """
    CONCEPT: Testing context managers and transactions
    Verify that failed transactions properly roll back all changes.
    """

    @pytest.fixture
    def db(self):
        db = InMemoryDB()
        db.create_table("users")
        return db

    def test_insert_and_find(self, db):
        db.insert("users", {"name": "Alice", "age": 30})
        results = db.find("users", name="Alice")
        assert len(results) == 1
        assert results[0]["name"] == "Alice"

    def test_auto_generated_id(self, db):
        row = db.insert("users", {"name": "Bob"})
        assert "id" in row
        assert len(row["id"]) > 0

    def test_find_with_multiple_criteria(self, db):
        db.insert("users", {"name": "Alice", "role": "admin"})
        db.insert("users", {"name": "Bob", "role": "user"})
        db.insert("users", {"name": "Charlie", "role": "admin"})

        admins = db.find("users", role="admin")
        assert len(admins) == 2

    def test_update(self, db):
        db.insert("users", {"name": "Alice", "age": 30})
        count = db.update("users", {"name": "Alice"}, {"age": 31})
        assert count == 1
        assert db.find_one("users", name="Alice")["age"] == 31

    def test_delete(self, db):
        db.insert("users", {"name": "Alice"})
        db.insert("users", {"name": "Bob"})
        deleted = db.delete("users", name="Alice")
        assert deleted == 1
        assert db.find_one("users", name="Alice") is None
        assert db.find_one("users", name="Bob") is not None

    def test_transaction_commit(self, db):
        """Successful transaction persists changes."""
        with db.transaction():
            db.insert("users", {"name": "Alice"})
            db.insert("users", {"name": "Bob"})

        assert len(db.find("users")) == 2

    def test_transaction_rollback(self, db):
        """
        CONCEPT: Testing context manager error handling
        Failed transactions should roll back ALL changes.
        """
        db.insert("users", {"name": "Existing"})

        with pytest.raises(ValueError):
            with db.transaction():
                db.insert("users", {"name": "New1"})
                db.insert("users", {"name": "New2"})
                raise ValueError("Something went wrong!")

        # Only "Existing" should remain — New1 and New2 rolled back
        results = db.find("users")
        assert len(results) == 1
        assert results[0]["name"] == "Existing"

    def test_nested_transactions(self, db):
        """
        CONCEPT: Nested context managers
        Inner transaction failure should not affect outer data
        that was committed before the nested transaction.
        """
        with db.transaction():
            db.insert("users", {"name": "Outer"})

            with pytest.raises(RuntimeError):
                with db.transaction():
                    db.insert("users", {"name": "Inner"})
                    raise RuntimeError("Inner fails")

            # "Outer" should still be pending in the outer transaction
            # "Inner" should be rolled back

        # After outer commits, we should have "Outer" but not "Inner"
        results = db.find("users")
        names = [r["name"] for r in results]
        assert "Outer" in names
        assert "Inner" not in names

    def test_create_duplicate_table_raises(self, db):
        with pytest.raises(ValueError, match="already exists"):
            db.create_table("users")

    def test_operations_on_nonexistent_table(self):
        db = InMemoryDB()
        with pytest.raises(ValueError, match="does not exist"):
            db.insert("nope", {"a": 1})


# --- 17. CircuitBreaker — testing state machine with timing ---

class TestCircuitBreaker:
    """
    CONCEPT: Combining state machine testing with time control
    Circuit breaker has 3 states with time-based transitions.
    """

    @pytest.fixture
    def fake_time(self):
        class FakeTime:
            def __init__(self):
                self.now = 0.0
            def __call__(self):
                return self.now
            def advance(self, s):
                self.now += s
        return FakeTime()

    @pytest.fixture
    def breaker(self, fake_time):
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=10.0,
            success_threshold=2,
            time_fn=fake_time,
        )

    def test_starts_closed(self, breaker):
        assert breaker.state == CircuitBreaker.State.CLOSED

    def test_opens_after_threshold_failures(self, breaker):
        for i in range(3):
            with pytest.raises(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert breaker.state == CircuitBreaker.State.OPEN

    def test_open_rejects_calls(self, breaker):
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        with pytest.raises(RuntimeError, match="OPEN"):
            breaker.call(lambda: "should not execute")

    def test_half_open_after_timeout(self, breaker, fake_time):
        # Trip the breaker
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        assert breaker.state == CircuitBreaker.State.OPEN

        # Wait for recovery timeout
        fake_time.advance(10.0)
        assert breaker.state == CircuitBreaker.State.HALF_OPEN

    def test_half_open_to_closed_on_successes(self, breaker, fake_time):
        # Trip it
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        fake_time.advance(10.0)
        assert breaker.state == CircuitBreaker.State.HALF_OPEN

        # Need success_threshold=2 successes to close
        breaker.call(lambda: "ok")
        assert breaker.state == CircuitBreaker.State.HALF_OPEN  # Not yet

        breaker.call(lambda: "ok")
        assert breaker.state == CircuitBreaker.State.CLOSED  # Recovered!

    def test_half_open_back_to_open_on_failure(self, breaker, fake_time):
        # Trip, wait, become half-open
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass
        fake_time.advance(10.0)

        # One failure in half-open → back to open
        with pytest.raises(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError()))

        assert breaker.state == CircuitBreaker.State.OPEN

    def test_success_resets_failure_count(self, breaker):
        """Successful calls should reset the failure counter."""
        # 2 failures (below threshold of 3)
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        # 1 success resets counter
        breaker.call(lambda: "ok")

        # 2 more failures — should NOT trip (counter was reset)
        for _ in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        assert breaker.state == CircuitBreaker.State.CLOSED

    def test_reset(self, breaker):
        for _ in range(3):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass
        assert breaker.state == CircuitBreaker.State.OPEN

        breaker.reset()
        assert breaker.state == CircuitBreaker.State.CLOSED
        assert breaker.call_log == []


# --- 18. Pipeline — testing composition and partial failures ---

class TestPipeline:
    """
    CONCEPT: Testing data transformation pipelines
    Test step execution, error handling, and partial results.
    """

    def test_simple_pipeline(self):
        p = Pipeline()
        p.add_step("double", lambda x: x * 2)
        p.add_step("add_one", lambda x: x + 1)

        result = p.execute(5)
        assert result["output"] == 11  # (5 * 2) + 1
        assert result["success"] is True
        assert result["steps_completed"] == ["double", "add_one"]

    def test_pipeline_failure_stops_execution(self):
        p = Pipeline()
        p.add_step("ok", lambda x: x + 1)
        p.add_step("fail", lambda x: 1 / 0)
        p.add_step("never_reached", lambda x: x * 100)

        result = p.execute(5)
        assert result["success"] is False
        assert result["steps_completed"] == ["ok"]
        assert result["steps_failed"][0]["step"] == "fail"
        assert result["output"] == 6  # Last successful output

    def test_error_handler_allows_recovery(self):
        """
        CONCEPT: Testing error recovery strategies
        Pipeline with error handler can skip failed steps.
        """
        p = Pipeline()
        p.add_step("parse", lambda x: int(x))
        p.add_step("risky", lambda x: x / 0)
        p.add_step("format", lambda x: f"Result: {x}")

        # Error handler: return last good value to continue
        p.on_error(lambda step, err, data: data)

        result = p.execute("42")
        assert result["success"] is False  # Had failures
        assert "format" in result["steps_completed"]  # But continued
        assert result["output"] == "Result: 42"

    def test_chaining_returns_pipeline(self):
        """add_step returns self for fluent API."""
        p = Pipeline().add_step("a", str).add_step("b", str)
        assert len(p) == 2

    def test_empty_pipeline(self):
        result = Pipeline().execute("data")
        assert result["output"] == "data"
        assert result["success"] is True

    @pytest.mark.parametrize("input_data, steps, expected_output", [
        (
            "hello world",
            [("upper", str.upper), ("split", str.split)],
            ["HELLO", "WORLD"],
        ),
        (
            [3, 1, 2],
            [("sort", sorted), ("reverse", lambda x: list(reversed(x)))],
            [3, 2, 1],
        ),
        (
            {"a": 1, "b": 2},
            [("keys", lambda d: list(d.keys())), ("join", lambda lst: ",".join(lst))],
            "a,b",
        ),
    ], ids=["string-processing", "list-processing", "dict-processing"])
    def test_various_data_types(self, input_data, steps, expected_output):
        """
        CONCEPT: Parametrize with complex data
        Each test case has different data types flowing through the pipeline.
        """
        p = Pipeline()
        for name, fn in steps:
            p.add_step(name, fn)
        result = p.execute(input_data)
        assert result["output"] == expected_output
        assert result["success"] is True
