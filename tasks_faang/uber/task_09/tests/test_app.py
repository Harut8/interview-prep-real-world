"""
Tests for Promo Code Service.

Some tests pass, some fail due to known bugs, some are TODOs.
"""

import pytest
import time
import threading
from app import (
    PromoCode,
    PromoType,
    PromoStatus,
    FareDetails,
    promos,
    usage_log,
    user_ride_count,
    apply_promo,
    calculate_discount,
    is_promo_expired,
    check_usage_limit,
)


@pytest.fixture(autouse=True)
def clear_state():
    """Clear all state before each test."""
    promos.clear()
    usage_log.clear()
    user_ride_count.clear()
    yield
    promos.clear()
    usage_log.clear()
    user_ride_count.clear()


def _create_promo(code: str = "SAVE20", promo_type: PromoType = PromoType.PERCENTAGE,
                  value: int = 20, max_discount: int = None,
                  expires_at: float = None, usage_limit: int = None,
                  **kwargs) -> PromoCode:
    promo = PromoCode(
        code=code.upper(),
        promo_type=promo_type,
        value=value,
        max_discount_cents=max_discount,
        expires_at=expires_at,
        usage_limit=usage_limit,
        **kwargs,
    )
    promos[code.upper()] = promo
    return promo


def _make_fare(base: int = 2000, tip: int = 0, tolls: int = 0) -> FareDetails:
    return FareDetails(base_fare_cents=base, tip_cents=tip, tolls_cents=tolls)


class TestPromoExpiration:
    def test_active_promo_not_expired(self):
        """
        FAILING: A promo expiring in the future should NOT be expired.
        Bug: is_promo_expired returns True when time is before expiration.
        """
        promo = _create_promo(
            expires_at=time.time() + 3600  # Expires in 1 hour
        )
        assert is_promo_expired(promo) is False, (
            "Active promo wrongly marked as expired"
        )

    def test_expired_promo_detected(self):
        """
        FAILING: A promo that expired 1 hour ago should be detected as expired.
        """
        promo = _create_promo(
            expires_at=time.time() - 3600  # Expired 1 hour ago
        )
        assert is_promo_expired(promo) is True, (
            "Expired promo not detected"
        )

    def test_no_expiration_is_valid(self):
        """This test should PASS — promo with no expiration is always valid."""
        promo = _create_promo(expires_at=None)
        assert is_promo_expired(promo) is False


class TestUsageLimit:
    def test_within_limit(self):
        """This test should PASS — usage under limit."""
        promo = _create_promo(usage_limit=100)
        promo.usage_count = 50
        assert check_usage_limit(promo) is True

    def test_concurrent_usage_exceeds_limit(self):
        """
        FAILING: Under concurrent requests, usage limit can be exceeded
        because check and increment are not atomic.
        """
        promo = _create_promo(code="LIMITED", usage_limit=5,
                              promo_type=PromoType.FIXED_AMOUNT, value=100)

        errors = []

        def use_promo():
            try:
                fare = _make_fare(base=2000)
                apply_promo("LIMITED", f"user_{threading.current_thread().name}", fare)
            except ValueError:
                errors.append(1)

        threads = [threading.Thread(target=use_promo) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert promo.usage_count <= 5, (
            f"Usage count {promo.usage_count} exceeds limit of 5"
        )


class TestPercentageDiscount:
    def test_percentage_on_base_fare_only(self):
        """
        FAILING: 20% discount should be on base fare only, not total with tips/tolls.
        Base fare: $20, tip: $5, tolls: $3.
        Correct: 20% of $20 = $4. Bug: 20% of ($20+$5+$3+$1.75) = $5.95.
        """
        promo = _create_promo(value=20)
        fare = _make_fare(base=2000, tip=500, tolls=300)
        discount = calculate_discount(promo, fare)
        expected = int(2000 * 20 / 100)  # $4.00 = 400 cents
        assert discount == expected, (
            f"Discount {discount} != expected {expected} — "
            f"percentage applied to wrong base"
        )

    def test_fixed_amount_discount(self):
        """This test should PASS — fixed $5 off."""
        promo = _create_promo(promo_type=PromoType.FIXED_AMOUNT, value=500)
        fare = _make_fare(base=2000)
        discount = calculate_discount(promo, fare)
        assert discount == 500

    def test_max_discount_cap(self):
        """This test should PASS — discount capped at max."""
        promo = _create_promo(value=50, max_discount=500)  # 50% off, max $5
        fare = _make_fare(base=2000)
        discount = calculate_discount(promo, fare)
        assert discount <= 500


class TestApplyPromo:
    def test_apply_valid_promo(self):
        """This test should PASS — basic promo application."""
        _create_promo(promo_type=PromoType.FIXED_AMOUNT, value=500)
        fare = _make_fare(base=2000)
        result = apply_promo("SAVE20", "user1", fare)
        assert result["discount_cents"] == 500


class TestStackablePromos:
    # TODO: Implement stackable promo logic
    # def test_stackable_promos_combine(self):
    #     """Two stackable promos should be applied together."""
    #     pass

    # TODO: Non-stackable rejection
    # def test_non_stackable_promo_rejects_combo(self):
    #     """Non-stackable promo should reject if another promo already applied."""
    #     pass

    # TODO: Stack ordering
    # def test_percentage_before_fixed(self):
    #     """When stacking, percentage promos apply first, then fixed amount."""
    #     pass
    pass


class TestFirstRideOnly:
    # TODO: Implement first-ride-only restriction
    # def test_first_ride_promo_works_for_new_user(self):
    #     """First-ride-only promo should work for user with 0 rides."""
    #     pass

    # TODO: Rejects returning users
    # def test_first_ride_promo_rejects_returning_user(self):
    #     """First-ride-only promo should fail for users with ride history."""
    #     pass
    pass


class TestPromoAnalytics:
    # TODO: Implement promo analytics
    # def test_total_discount_given(self):
    #     """Should track total discount amount given per promo."""
    #     pass

    # TODO: Most popular promos
    # def test_most_used_promo(self):
    #     """Should return promos ranked by usage count."""
    #     pass
    pass
