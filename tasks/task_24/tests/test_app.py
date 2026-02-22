import pytest
from app import ATM, TransactionType


@pytest.fixture
def atm():
    machine = ATM()
    machine.create_account("acc1", "1234", initial_balance=1000.0)
    machine.create_account("acc2", "5678", initial_balance=500.0)
    return machine


def test_create_account(atm):
    atm.create_account("acc3", "0000", 100.0)
    assert "acc3" in atm.accounts
    assert atm.accounts["acc3"].balance == 100.0


def test_authenticate_success(atm):
    assert atm.authenticate("acc1", "1234") is True


def test_authenticate_wrong_pin(atm):
    assert atm.authenticate("acc1", "0000") is False


# FAILS — fix: should lock account after MAX_PIN_ATTEMPTS
def test_account_locks_after_failed_attempts(atm):
    for _ in range(3):
        atm.authenticate("acc1", "0000")

    # Account should be locked now — even correct PIN should fail
    assert atm.authenticate("acc1", "1234") is False
    assert atm.accounts["acc1"].locked is True


# FAILS — fix: get_balance should require authentication
def test_balance_requires_authentication(atm):
    with pytest.raises(PermissionError):
        atm.get_balance("acc1")


def test_deposit(atm):
    atm.authenticate("acc1", "1234")
    assert atm.deposit("acc1", 500.0) is True
    assert atm.accounts["acc1"].balance == 1500.0


# FAILS — fix: negative deposit should be rejected
def test_deposit_negative_rejected(atm):
    atm.authenticate("acc1", "1234")
    assert atm.deposit("acc1", -100.0) is False
    assert atm.accounts["acc1"].balance == 1000.0


def test_withdraw(atm):
    atm.authenticate("acc1", "1234")
    assert atm.withdraw("acc1", 200.0) is True
    assert atm.accounts["acc1"].balance == 800.0


def test_withdraw_insufficient_funds(atm):
    atm.authenticate("acc1", "1234")
    assert atm.withdraw("acc1", 5000.0) is False
    assert atm.accounts["acc1"].balance == 1000.0


def test_withdraw_negative(atm):
    atm.authenticate("acc1", "1234")
    assert atm.withdraw("acc1", -50.0) is False


# TODO: Add tests for denomination dispensing
# TODO: Add tests for transfer between accounts
# TODO: Add tests for get_statement
# TODO: Add tests for daily withdrawal limit
# TODO: Add tests for session timeout
