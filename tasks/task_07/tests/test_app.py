import pytest
from datetime import date
from app import parse_date, parse_amount, read_transactions, Transaction


def test_parse_date_iso():
    assert parse_date("2024-01-15") == date(2024, 1, 15)


def test_parse_date_european():
    assert parse_date("15/01/2024") == date(2024, 1, 15)


# FAILS — fix to raise error on invalid dates
def test_parse_date_invalid_raises():
    with pytest.raises(ValueError):
        parse_date("not-a-date")


# FAILS — fix European number format handling
def test_parse_amount_european():
    assert parse_amount("1.234,56") == 1234.56


def test_parse_amount_with_currency():
    assert parse_amount("$25.50") == 25.50


# FAILS — fix BOM handling
def test_read_csv_with_bom():
    bom_csv = '\ufeffid,date,category,amount,description\n1,2024-01-15,food,10.00,Test\n'
    transactions = read_transactions(bom_csv)
    assert len(transactions) == 1
    assert transactions[0].id == "1"


# TODO: Add test for empty CSV file
# TODO: Add test for validation (negative amounts, future dates)
# TODO: Add test for summary report
# TODO: Add test for generator-based reading (memory efficiency)
