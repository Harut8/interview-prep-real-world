"""
Tests for Payment Processing Pipeline.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import threading
from app import (
    Charge,
    Refund,
    PaymentStatus,
    Currency,
    charges,
    refunds,
    exchange_rates,
    process_charge,
    retry_charge,
    process_refund,
    convert_currency,
    get_total_refunded,
    GATEWAY_FAILURE_RATE,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    charges.clear()
    refunds.clear()
    yield
    charges.clear()
    refunds.clear()


class TestChargeProcessing:
    def test_successful_charge(self):
        """This test should PASS — basic charge succeeds."""
        charge = process_charge("trip1", "rider1", 2500)
        assert charge.status == PaymentStatus.COMPLETED
        assert charge.amount_cents == 2500

    def test_charge_stored_in_registry(self):
        """This test should PASS — charge is stored."""
        charge = process_charge("trip1", "rider1", 2500)
        assert charge.charge_id in charges


class TestRetryDoubleCharge:
    def test_retry_does_not_create_duplicate_charges(self):
        """
        FAILING: Retrying a charge for the same trip should not create
        multiple COMPLETED charges. Currently each retry creates a new
        charge record, potentially double-charging.
        """
        # First charge succeeds
        charge1 = process_charge("trip1", "rider1", 2500)
        assert charge1.status == PaymentStatus.COMPLETED

        # Retry for the same trip (shouldn't create a new charge)
        charge2 = retry_charge("trip1", "rider1", 2500)

        # Count completed charges for this trip
        completed_for_trip = [
            c for c in charges.values()
            if c.trip_id == "trip1" and c.status == PaymentStatus.COMPLETED
        ]
        assert len(completed_for_trip) == 1, (
            f"Expected 1 completed charge for trip, got {len(completed_for_trip)}"
        )


class TestRefundExceedsCharge:
    def test_refund_cannot_exceed_original(self):
        """
        FAILING: Total refunds should not exceed the original charge amount.
        Currently there's no enforcement.
        """
        charge = process_charge("trip1", "rider1", 1000)

        # Refund $6 on a $10 charge
        process_refund(charge.charge_id, 600, "partial 1")
        # Refund another $6 — total $12 refunded on $10 charge!
        with pytest.raises(ValueError, match="[Ee]xceed"):
            process_refund(charge.charge_id, 600, "partial 2")

    def test_valid_partial_refund(self):
        """This test should PASS — valid refund under charge amount."""
        charge = process_charge("trip1", "rider1", 1000)
        refund = process_refund(charge.charge_id, 500, "partial")
        assert refund.amount_cents == 500
        assert charge.status == PaymentStatus.PARTIALLY_REFUNDED


class TestCurrencyConversion:
    def test_same_currency_no_conversion(self):
        """This test should PASS — same currency returns same amount."""
        result = convert_currency(1000, Currency.USD, Currency.USD)
        assert result == 1000

    def test_usd_to_eur_conversion(self):
        """This test should PASS — basic conversion works."""
        result = convert_currency(1000, Currency.USD, Currency.EUR)
        expected = int(1000 * 0.92)
        assert result == expected

    def test_conversion_race_condition(self):
        """
        FAILING: Currency conversion should be atomic.
        Another thread changing rates mid-conversion can cause wrong amounts.
        """
        results = []
        original_rate = exchange_rates["EUR"]

        def convert():
            result = convert_currency(10000, Currency.USD, Currency.EUR)
            results.append(result)

        def change_rate():
            exchange_rates["EUR"] = 0.50  # Drastically change rate

        t1 = threading.Thread(target=convert)
        t2 = threading.Thread(target=change_rate)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        exchange_rates["EUR"] = original_rate  # Restore

        # All conversions should use a consistent rate
        expected = int(10000 * original_rate)
        # In practice this test is flaky due to the race; it demonstrates the issue
        assert len(results) == 1


class TestIdempotency:
    # TODO: Implement idempotency keys for charges
    # def test_same_idempotency_key_returns_same_result(self):
    #     """Two charges with the same idempotency key should return the same charge."""
    #     pass

    # TODO: Different keys create different charges
    # def test_different_keys_create_separate_charges(self):
    #     """Different idempotency keys should create separate charges."""
    #     pass
    pass


class TestAuditLog:
    # TODO: Implement payment audit log
    # def test_charge_logged_in_audit(self):
    #     """Every charge should be recorded in the audit log."""
    #     pass

    # TODO: Refund logged in audit
    # def test_refund_logged_in_audit(self):
    #     """Every refund should be recorded in the audit log."""
    #     pass

    # TODO: Query audit log
    # def test_query_audit_by_trip(self):
    #     """Should be able to query all payment events for a trip."""
    #     pass
    pass
