# Vending Machine

**Classic OOP warmup — clean state management + money handling.**

## Interface

```python
class VendingMachine:
    def __init__(self) -> None: ...
    def add_product(self, name: str, price: float, quantity: int) -> None: ...
    def insert_money(self, amount: float) -> None: ...
    def select_product(self, name: str) -> str: ...
    def get_change(self) -> float: ...
    def get_inventory(self) -> dict[str, dict]: ...
```

## Requirements

- `add_product` stocks the machine. Same product can be restocked (adds to quantity).
- `insert_money` accumulates a balance for the current transaction.
- `select_product` dispenses if in stock and balance sufficient. Returns a status message. Deducts the price from balance.
- `get_change` returns remaining balance and resets to 0.
- Handle: out of stock, insufficient funds, invalid product.

## Extensions

- **Coin denominations**: accept only valid coins (0.25, 0.50, 1.00), reject others.
- **Admin mode**: refill, collect revenue, view sales stats (protected by PIN).
- **Combo deals**: buy 2+ items in one transaction with discount.

## Time Target: 30 minutes
