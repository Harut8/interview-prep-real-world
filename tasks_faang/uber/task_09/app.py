"""
Promo Code Service
Manages promotional codes with rules and applies them to fares.
"""

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Promo Code Service")


class PromoType(Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"


class PromoStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    EXHAUSTED = "exhausted"
    DISABLED = "disabled"


@dataclass
class PromoCode:
    code: str
    promo_type: PromoType
    value: int  # Percentage (e.g., 20 for 20%) or fixed amount in cents
    max_discount_cents: Optional[int] = None  # Cap for percentage promos
    expires_at: Optional[float] = None  # Unix timestamp
    usage_limit: Optional[int] = None  # Max total uses
    usage_count: int = 0
    min_fare_cents: int = 0  # Minimum fare to apply
    status: PromoStatus = PromoStatus.ACTIVE
    stackable: bool = False
    first_ride_only: bool = False
    created_at: float = field(default_factory=time.time)


@dataclass
class PromoUsage:
    code: str
    user_id: str
    fare_cents: int
    discount_cents: int
    applied_at: float = field(default_factory=time.time)


@dataclass
class FareDetails:
    base_fare_cents: int  # base + distance + time (surged)
    tip_cents: int = 0
    tolls_cents: int = 0
    booking_fee_cents: int = 175  # $1.75


# --- In-memory storage ---
promos: dict[str, PromoCode] = {}
usage_log: list[PromoUsage] = []
user_ride_count: dict[str, int] = {}  # user_id -> number of completed rides


def is_promo_expired(promo: PromoCode) -> bool:
    """
    Check if a promo code has expired.

    BUG: Comparison is wrong — allows expired promos and rejects active ones.
    """
    if promo.expires_at is None:
        return False
    # BUG: Should be `time.time() > promo.expires_at` to check if expired
    # Currently returns True (expired) when current time is BEFORE expiry
    return time.time() < promo.expires_at


def check_usage_limit(promo: PromoCode) -> bool:
    """
    Check if the promo has remaining uses.

    BUG: Not atomic — concurrent requests can bypass the limit.
    Returns True if the promo can still be used.
    """
    if promo.usage_limit is None:
        return True
    # BUG: This check + increment in apply_promo is not atomic
    return promo.usage_count < promo.usage_limit


def calculate_discount(promo: PromoCode, fare: FareDetails) -> int:
    """
    Calculate the discount amount in cents.

    BUG: Percentage discount is calculated on total (including tips/tolls)
    instead of just the base fare.
    """
    if promo.promo_type == PromoType.FIXED_AMOUNT:
        discount = promo.value
    elif promo.promo_type == PromoType.PERCENTAGE:
        # BUG: Should only apply to base_fare_cents, but includes tips/tolls
        total = (fare.base_fare_cents + fare.tip_cents +
                 fare.tolls_cents + fare.booking_fee_cents)
        discount = int(total * promo.value / 100)
    else:
        return 0

    # Apply max discount cap
    if promo.max_discount_cents is not None:
        discount = min(discount, promo.max_discount_cents)

    # Don't let discount exceed the base fare
    discount = min(discount, fare.base_fare_cents)

    return discount


def apply_promo(code: str, user_id: str, fare: FareDetails) -> dict:
    """Apply a promo code to a fare and return the discount details."""
    promo = promos.get(code.upper())
    if promo is None:
        raise ValueError(f"Promo code '{code}' not found")

    if promo.status == PromoStatus.DISABLED:
        raise ValueError("Promo code is disabled")

    if is_promo_expired(promo):
        raise ValueError("Promo code has expired")

    if not check_usage_limit(promo):
        raise ValueError("Promo code usage limit reached")

    if fare.base_fare_cents < promo.min_fare_cents:
        raise ValueError(
            f"Fare must be at least {promo.min_fare_cents} cents"
        )

    discount = calculate_discount(promo, fare)

    # BUG: Increment is not atomic with the check above
    promo.usage_count += 1

    # Log usage
    usage = PromoUsage(
        code=code.upper(),
        user_id=user_id,
        fare_cents=fare.base_fare_cents,
        discount_cents=discount,
    )
    usage_log.append(usage)

    final_fare = fare.base_fare_cents - discount + fare.tip_cents + fare.tolls_cents + fare.booking_fee_cents

    return {
        "code": code.upper(),
        "discount_cents": discount,
        "original_fare_cents": fare.base_fare_cents + fare.tip_cents + fare.tolls_cents + fare.booking_fee_cents,
        "final_fare_cents": final_fare,
    }


# --- API Endpoints ---

class PromoCreate(BaseModel):
    code: str
    promo_type: str  # "percentage" or "fixed_amount"
    value: int
    max_discount_cents: Optional[int] = None
    expires_at: Optional[float] = None
    usage_limit: Optional[int] = None
    min_fare_cents: int = 0
    stackable: bool = False
    first_ride_only: bool = False


class ApplyPromoRequest(BaseModel):
    code: str
    user_id: str
    base_fare_cents: int
    tip_cents: int = 0
    tolls_cents: int = 0


@app.post("/promos")
def create_promo(data: PromoCreate):
    promo = PromoCode(
        code=data.code.upper(),
        promo_type=PromoType(data.promo_type),
        value=data.value,
        max_discount_cents=data.max_discount_cents,
        expires_at=data.expires_at,
        usage_limit=data.usage_limit,
        min_fare_cents=data.min_fare_cents,
        stackable=data.stackable,
        first_ride_only=data.first_ride_only,
    )
    promos[data.code.upper()] = promo
    return {"status": "created", "code": data.code.upper()}


@app.post("/promos/apply")
def api_apply_promo(data: ApplyPromoRequest):
    fare = FareDetails(
        base_fare_cents=data.base_fare_cents,
        tip_cents=data.tip_cents,
        tolls_cents=data.tolls_cents,
    )
    try:
        result = apply_promo(data.code, data.user_id, fare)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@app.get("/promos/{code}")
def get_promo(code: str):
    promo = promos.get(code.upper())
    if promo is None:
        raise HTTPException(status_code=404, detail="Promo not found")
    return {
        "code": promo.code,
        "type": promo.promo_type.value,
        "value": promo.value,
        "usage_count": promo.usage_count,
        "usage_limit": promo.usage_limit,
        "expires_at": promo.expires_at,
        "status": promo.status.value,
    }


@app.get("/promos")
def list_promos():
    return [
        {
            "code": p.code,
            "type": p.promo_type.value,
            "value": p.value,
            "usage_count": p.usage_count,
            "status": p.status.value,
        }
        for p in promos.values()
    ]
