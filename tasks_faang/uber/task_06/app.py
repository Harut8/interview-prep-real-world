"""
Payment Processing Pipeline
Processes ride payments with retries, refunds, and currency conversion.
"""

import time
import uuid
import random
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Payment Processing Pipeline")


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class Currency(Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    MXN = "MXN"


@dataclass
class Charge:
    charge_id: str
    trip_id: str
    rider_id: str
    amount_cents: int
    currency: Currency
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: float = field(default_factory=time.time)
    retry_count: int = 0


@dataclass
class Refund:
    refund_id: str
    charge_id: str
    amount_cents: int
    reason: str = ""
    created_at: float = field(default_factory=time.time)


# --- In-memory storage ---
charges: dict[str, Charge] = {}
refunds: dict[str, Refund] = {}

# Exchange rates relative to USD (how many units per 1 USD)
exchange_rates: dict[str, float] = {
    "USD": 1.0,
    "EUR": 0.92,
    "GBP": 0.79,
    "MXN": 17.15,
}

# Simulated gateway failure rate
GATEWAY_FAILURE_RATE = 0.0  # Set > 0 for testing retries


def simulate_gateway_charge(amount_cents: int) -> bool:
    """Simulate a payment gateway. Returns True if charge succeeds."""
    if random.random() < GATEWAY_FAILURE_RATE:
        return False
    return True


def convert_currency(amount_cents: int, from_currency: Currency,
                     to_currency: Currency) -> int:
    """
    Convert amount between currencies.

    BUG: Race condition — rate is fetched, then used in a separate step.
    Between fetch and use, the rate could change (simulated by the mutable dict).
    """
    if from_currency == to_currency:
        return amount_cents

    # Step 1: Read rates (not atomic with step 2)
    from_rate = exchange_rates[from_currency.value]
    to_rate = exchange_rates[to_currency.value]

    # BUG: Another thread could modify exchange_rates between these reads
    # and the actual conversion below
    usd_amount = amount_cents / from_rate
    converted = int(usd_amount * to_rate)

    return converted


def process_charge(trip_id: str, rider_id: str, amount_cents: int,
                   currency: Currency = Currency.USD) -> Charge:
    """
    Process a payment charge for a trip.

    BUG: On retry, creates a brand new charge without checking if a previous
    attempt for the same trip already succeeded (no idempotency).
    """
    charge_id = str(uuid.uuid4())[:8]
    charge = Charge(
        charge_id=charge_id,
        trip_id=trip_id,
        rider_id=rider_id,
        amount_cents=amount_cents,
        currency=currency,
    )

    success = simulate_gateway_charge(amount_cents)
    if success:
        charge.status = PaymentStatus.COMPLETED
    else:
        charge.status = PaymentStatus.FAILED

    # BUG: Always stores a new charge — retrying the same trip creates duplicates
    charges[charge_id] = charge
    return charge


def retry_charge(trip_id: str, rider_id: str, amount_cents: int,
                 currency: Currency = Currency.USD, max_retries: int = 3) -> Charge:
    """
    Retry a failed charge up to max_retries times.

    BUG: Doesn't check if a charge for this trip already succeeded.
    Could result in double-charging.
    """
    last_charge = None
    for attempt in range(max_retries):
        # BUG: Calls process_charge each time, which creates a new charge record
        # even if a previous attempt succeeded
        charge = process_charge(trip_id, rider_id, amount_cents, currency)
        last_charge = charge
        charge.retry_count = attempt

        if charge.status == PaymentStatus.COMPLETED:
            return charge

    return last_charge


def process_refund(charge_id: str, amount_cents: int, reason: str = "") -> Refund:
    """
    Process a refund against a charge.

    BUG: Doesn't track total refunded amount per charge.
    Multiple refunds can exceed the original charge amount.
    """
    charge = charges.get(charge_id)
    if charge is None:
        raise ValueError(f"Charge {charge_id} not found")

    if charge.status == PaymentStatus.FAILED:
        raise ValueError("Cannot refund a failed charge")

    # BUG: No check that total refunds <= original charge amount
    refund_id = str(uuid.uuid4())[:8]
    refund = Refund(
        refund_id=refund_id,
        charge_id=charge_id,
        amount_cents=amount_cents,
        reason=reason,
    )
    refunds[refund_id] = refund

    if amount_cents >= charge.amount_cents:
        charge.status = PaymentStatus.REFUNDED
    else:
        charge.status = PaymentStatus.PARTIALLY_REFUNDED

    return refund


def get_total_refunded(charge_id: str) -> int:
    """Calculate total amount refunded for a charge."""
    return sum(
        r.amount_cents for r in refunds.values() if r.charge_id == charge_id
    )


# --- API Endpoints ---

class ChargeRequest(BaseModel):
    trip_id: str
    rider_id: str
    amount_cents: int
    currency: str = "USD"


class RefundRequest(BaseModel):
    charge_id: str
    amount_cents: int
    reason: str = ""


@app.post("/charges")
def api_create_charge(data: ChargeRequest):
    charge = process_charge(
        data.trip_id, data.rider_id, data.amount_cents,
        Currency(data.currency)
    )
    return {
        "charge_id": charge.charge_id,
        "status": charge.status.value,
        "amount_cents": charge.amount_cents,
    }


@app.post("/charges/{charge_id}/retry")
def api_retry_charge(charge_id: str):
    charge = charges.get(charge_id)
    if charge is None:
        raise HTTPException(status_code=404, detail="Charge not found")

    result = retry_charge(
        charge.trip_id, charge.rider_id,
        charge.amount_cents, charge.currency
    )
    return {
        "charge_id": result.charge_id,
        "status": result.status.value,
        "retry_count": result.retry_count,
    }


@app.post("/refunds")
def api_create_refund(data: RefundRequest):
    try:
        refund = process_refund(data.charge_id, data.amount_cents, data.reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "refund_id": refund.refund_id,
        "charge_id": refund.charge_id,
        "amount_cents": refund.amount_cents,
    }


@app.get("/charges/{charge_id}")
def api_get_charge(charge_id: str):
    charge = charges.get(charge_id)
    if charge is None:
        raise HTTPException(status_code=404, detail="Charge not found")
    return {
        "charge_id": charge.charge_id,
        "trip_id": charge.trip_id,
        "rider_id": charge.rider_id,
        "amount_cents": charge.amount_cents,
        "currency": charge.currency.value,
        "status": charge.status.value,
        "total_refunded": get_total_refunded(charge.charge_id),
    }
