import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    TRANSFER = "transfer"
    BALANCE_CHECK = "balance_check"


@dataclass
class Transaction:
    type: TransactionType
    amount: float
    timestamp: float = field(default_factory=time.time)
    description: str = ""


@dataclass
class Account:
    id: str
    pin: str
    balance: float = 0.0
    transactions: list[Transaction] = field(default_factory=list)
    failed_attempts: int = 0
    locked: bool = False


class ATM:
    """Simulated ATM machine."""

    MAX_PIN_ATTEMPTS = 3

    def __init__(self):
        self.accounts: dict[str, Account] = {}
        self._authenticated_account: Optional[str] = None
        self._cash_available: float = 10000.0

    def create_account(self, account_id: str, pin: str, initial_balance: float = 0.0) -> Account:
        """Create a new account."""
        account = Account(id=account_id, pin=pin, balance=initial_balance)
        self.accounts[account_id] = account
        return account

    def authenticate(self, account_id: str, pin: str) -> bool:
        """Authenticate a user with account ID and PIN."""
        account = self.accounts.get(account_id)
        if not account:
            return False

        # BUG: doesn't lock account after MAX_PIN_ATTEMPTS failed tries
        if account.pin == pin:
            account.failed_attempts = 0
            self._authenticated_account = account_id
            return True
        else:
            account.failed_attempts += 1
            return False

    def get_balance(self, account_id: str) -> float:
        """Get account balance."""
        # BUG: doesn't check if session is authenticated
        account = self.accounts.get(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        return account.balance

    def deposit(self, account_id: str, amount: float) -> bool:
        """Deposit money into an account."""
        account = self.accounts.get(account_id)
        if not account:
            return False

        # BUG: adds to balance before validating amount
        account.balance += amount

        transaction = Transaction(
            type=TransactionType.DEPOSIT,
            amount=amount,
            description=f"Deposit ${amount}",
        )
        account.transactions.append(transaction)
        return True

    def withdraw(self, account_id: str, amount: float) -> bool:
        """Withdraw money from an account."""
        account = self.accounts.get(account_id)
        if not account:
            return False

        if amount <= 0:
            return False

        if account.balance < amount:
            return False

        # BUG: doesn't check if ATM has enough cash or correct denominations
        if amount > self._cash_available:
            return False

        account.balance -= amount
        self._cash_available -= amount

        transaction = Transaction(
            type=TransactionType.WITHDRAWAL,
            amount=amount,
            description=f"Withdrawal ${amount}",
        )
        account.transactions.append(transaction)
        return True

    def logout(self) -> None:
        """End the current session."""
        self._authenticated_account = None


# TODO: Add denomination management (bills: $100, $50, $20, $10, $5)
# TODO: Add transfer(from_account, to_account, amount)
# TODO: Add get_statement(account_id, n) for transaction history
# TODO: Add daily withdrawal limit
# TODO: Add session timeout (30 seconds)
