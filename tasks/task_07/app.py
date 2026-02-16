import csv
import io
from datetime import datetime, date
from dataclasses import dataclass


@dataclass
class Transaction:
    id: str
    date: date
    category: str
    amount: float
    description: str


def parse_date(date_str: str) -> date | None:
    """Parse a date string in various formats."""
    formats = ["%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%m-%d-%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    # BUG: silently returns None instead of raising error
    return None


def parse_amount(amount_str: str) -> float:
    """Parse amount string to float."""
    # BUG: doesn't handle European format "1.234,56"
    cleaned = amount_str.strip().replace("$", "").replace("€", "")
    return float(cleaned)


def read_transactions(file_content: str) -> list[Transaction]:
    """Read transactions from CSV content."""
    # BUG: loads everything into memory at once
    # BUG: doesn't handle BOM
    reader = csv.DictReader(io.StringIO(file_content))
    transactions = []
    for row in reader:
        tx = Transaction(
            id=row["id"],
            date=parse_date(row["date"]),
            category=row["category"],
            amount=parse_amount(row["amount"]),
            description=row.get("description", ""),
        )
        transactions.append(tx)
    return transactions


def process_transactions(transactions: list[Transaction]) -> list[dict]:
    """Process and transform transactions."""
    results = []
    for tx in transactions:
        results.append({
            "id": tx.id,
            "date": tx.date.isoformat() if tx.date else "UNKNOWN",
            "category": tx.category.upper(),
            "amount": round(tx.amount, 2),
            "description": tx.description,
        })
    return results


SAMPLE_CSV = """id,date,category,amount,description
1,2024-01-15,food,25.50,Lunch
2,2024-01-16,transport,12.00,Bus ticket
3,2024-01-16,food,8.75,Coffee
4,15/01/2024,entertainment,45.00,Movie
5,2024-01-17,food,1.234,56,European amount
"""

# TODO: Add validation (reject negative amounts, future dates)
# TODO: Add summary report generator
# TODO: Refactor to use generators instead of loading everything into memory
