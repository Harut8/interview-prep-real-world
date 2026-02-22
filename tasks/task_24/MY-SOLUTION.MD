# My Solution — Task 24

## Bug Fixes

### 1. `withdraw` doesn't check denomination availability

The code only checks `amount > self._cash_available` (total cash). But the ATM has specific bills ($100, $50, $20, $10, $5). If the ATM only has $100 bills and the user wants $30, it should fail — can't make change.

Fix: track denominations and use a greedy algorithm to check if the amount can be dispensed.

```python
def __init__(self):
    self.accounts: dict[str, Account] = {}
    self._authenticated_account: Optional[str] = None
    self._denominations: dict[int, int] = {
        100: 50, 50: 50, 20: 50, 10: 50, 5: 50
    }  # bill_value -> count

@property
def _cash_available(self) -> float:
    return sum(bill * count for bill, count in self._denominations.items())

def _can_dispense(self, amount: int) -> dict[int, int] | None:
    """Greedy: try to dispense using largest bills first. Returns bill breakdown or None."""
    if amount <= 0 or amount % 5 != 0:  # must be multiple of smallest bill
        return None
    remaining = amount
    dispensed = {}
    for bill in sorted(self._denominations.keys(), reverse=True):
        if remaining <= 0:
            break
        count_needed = remaining // bill
        count_available = self._denominations[bill]
        count_used = min(count_needed, count_available)
        if count_used > 0:
            dispensed[bill] = count_used
            remaining -= bill * count_used
    if remaining == 0:
        return dispensed
    return None  # can't make exact change

def withdraw(self, account_id: str, amount: float) -> bool:
    # ... auth check, account exists, balance check ...
    dispensed = self._can_dispense(int(amount))
    if dispensed is None:
        return False
    # Deduct bills
    for bill, count in dispensed.items():
        self._denominations[bill] -= count
    account.balance -= amount
    # ... record transaction ...
    return True
```

### 2. `authenticate` doesn't lock after failed PIN attempts

Line 60 increments `failed_attempts` but never checks it. After `MAX_PIN_ATTEMPTS` (3) failures, the account should be locked and all subsequent auth attempts rejected. The `Account` dataclass already has `locked: bool = False` but it's never set.

Fix: check `locked` at the start, set it when threshold is reached.

```python
def authenticate(self, account_id: str, pin: str) -> bool:
    account = self.accounts.get(account_id)
    if not account:
        return False

    if account.locked:
        return False  # account is locked, reject immediately

    if account.pin == pin:
        account.failed_attempts = 0
        self._authenticated_account = account_id
        return True
    else:
        account.failed_attempts += 1
        if account.failed_attempts >= self.MAX_PIN_ATTEMPTS:
            account.locked = True
        return False
```

### 3. `deposit` adds to balance before validating amount

Line 78 does `account.balance += amount` before any validation. A negative amount (e.g., `deposit("acc1", -500)`) would decrease the balance — effectively a free withdrawal.

Fix: validate `amount > 0` before modifying balance.

```python
def deposit(self, account_id: str, amount: float) -> bool:
    account = self.accounts.get(account_id)
    if not account:
        return False

    if amount <= 0:
        return False  # reject negative/zero deposits

    account.balance += amount
    transaction = Transaction(
        type=TransactionType.DEPOSIT,
        amount=amount,
        description=f"Deposit ${amount}",
    )
    account.transactions.append(transaction)
    return True
```

### 4. `get_balance` doesn't check authentication

Anyone can call `get_balance("any_account")` without being authenticated. Should verify the session.

Fix: check `self._authenticated_account == account_id`.

```python
def get_balance(self, account_id: str) -> float:
    if self._authenticated_account != account_id:
        raise PermissionError("Not authenticated for this account")
    account = self.accounts.get(account_id)
    if not account:
        raise ValueError(f"Account {account_id} not found")
    return account.balance
```

Same auth check should be added to `withdraw` and `deposit` too for consistency.

---

## Feature Implementation Plan

### Feature 1: Denomination management

Already covered in bug fix #1. The ATM tracks `_denominations: dict[int, int]` and uses a greedy algorithm (`_can_dispense`) to find the optimal bill combination, largest bills first. After dispensing, decrement the bill counts.

Edge cases:
- Amount not a multiple of $5 → reject
- Greedy fails (e.g., only $50 bills, want $30) → return None
- Could add a `load_cash(bill, count)` method for restocking

### Feature 2: `transfer(from_account, to_account, amount)`

Move funds between two accounts atomically.

```python
def transfer(self, from_id: str, to_id: str, amount: float) -> bool:
    if self._authenticated_account != from_id:
        return False
    from_acc = self.accounts.get(from_id)
    to_acc = self.accounts.get(to_id)
    if not from_acc or not to_acc:
        return False
    if amount <= 0 or from_acc.balance < amount:
        return False

    from_acc.balance -= amount
    to_acc.balance += amount

    # Record transaction on both accounts
    from_acc.transactions.append(Transaction(
        type=TransactionType.TRANSFER, amount=-amount,
        description=f"Transfer to {to_id}"
    ))
    to_acc.transactions.append(Transaction(
        type=TransactionType.TRANSFER, amount=amount,
        description=f"Transfer from {from_id}"
    ))
    return True
```

### Feature 3: `get_statement(account_id, n)`

Return last N transactions for an account.

```python
def get_statement(self, account_id: str, n: int = 10) -> list[Transaction]:
    if self._authenticated_account != account_id:
        raise PermissionError("Not authenticated")
    account = self.accounts.get(account_id)
    if not account:
        raise ValueError("Account not found")
    return account.transactions[-n:]  # last n transactions
```

### Feature 4: Daily withdrawal limit

Track daily withdrawals per account. Default $1000/day, configurable per account.

```python
from datetime import date

@dataclass
class Account:
    # ... existing fields ...
    daily_limit: float = 1000.0
    daily_withdrawn: float = 0.0
    last_withdrawal_date: Optional[str] = None  # ISO date string

def withdraw(self, account_id: str, amount: float) -> bool:
    # ... existing checks ...
    today = date.today().isoformat()
    if account.last_withdrawal_date != today:
        account.daily_withdrawn = 0.0
        account.last_withdrawal_date = today

    if account.daily_withdrawn + amount > account.daily_limit:
        return False  # daily limit exceeded

    # ... proceed with withdrawal ...
    account.daily_withdrawn += amount
    return True
```

### Feature 5: Session timeout (30 seconds)

Track last activity time. Auto-logout if idle > 30 seconds.

```python
class ATM:
    SESSION_TIMEOUT = 30  # seconds

    def __init__(self):
        # ... existing ...
        self._last_activity: float = 0.0

    def _check_session(self) -> bool:
        """Check if session is still valid. Auto-logout if expired."""
        if self._authenticated_account is None:
            return False
        if time.time() - self._last_activity > self.SESSION_TIMEOUT:
            self.logout()
            return False
        return True

    def _touch_session(self):
        """Update last activity timestamp."""
        self._last_activity = time.time()

    def authenticate(self, account_id: str, pin: str) -> bool:
        # ... existing logic ...
        if account.pin == pin:
            # ... set authenticated ...
            self._touch_session()
            return True
        # ...
```

Call `_check_session()` at the start of every operation (`get_balance`, `withdraw`, `deposit`, `transfer`). Call `_touch_session()` after every successful operation.

### Feature 6: Tests

- **Denomination check**: withdraw $30 when ATM only has $50 bills → fails. Withdraw $50 → succeeds, bill count decremented
- **Greedy dispensing**: withdraw $280 → verify it uses 2×$100 + 1×$50 + 1×$20 + 1×$10
- **Account lock**: 3 wrong PINs → account locked, correct PIN after lock → still fails
- **Negative deposit**: `deposit("acc", -100)` returns False, balance unchanged
- **Auth on get_balance**: call without authenticating → PermissionError
- **Transfer**: transfer $200 from A to B, verify both balances and transaction records
- **Transfer insufficient funds**: balance $100, transfer $200 → fails, both balances unchanged
- **Statement**: make 5 transactions, `get_statement(id, 3)` returns last 3
- **Daily limit**: withdraw $800, then try to withdraw $300 → fails (exceeds $1000 limit). Next day → resets
- **Session timeout**: authenticate, sleep 31 seconds (or mock time), call get_balance → PermissionError/auto-logout
- **Session touch**: authenticate, do operations within 30s each → session stays alive