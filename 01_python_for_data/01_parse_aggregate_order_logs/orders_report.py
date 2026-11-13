#!/usr/bin/env python3
"""Read orders.csv and print monthly revenue totals per customer."""

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = {"order_id", "customer_id", "amount", "created_at"}


def parse_created_at(value: str) -> str:
    """Return YYYY-MM from an ISO date or datetime string."""
    value = value.strip()
    if not value:
        raise ValueError("created_at is empty")

    # Support ISO dates, ISO datetimes, and timestamps ending in Z.
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("created_at is not a valid ISO date/datetime") from exc
        return parsed_date.strftime("%Y-%m")

    return parsed.strftime("%Y-%m")


def validate_row(row: dict) -> tuple[str, Decimal, str]:
    """Validate one CSV row and return (customer_id, amount, month)."""
    order_id = (row.get("order_id") or "").strip()
    customer_id = (row.get("customer_id") or "").strip()
    amount_text = (row.get("amount") or "").strip()
    created_at = row.get("created_at") or ""

    if not order_id:
        raise ValueError("order_id is empty")
    if not customer_id:
        raise ValueError("customer_id is empty")

    try:
        amount = Decimal(amount_text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("amount is not a valid number") from exc

    if not amount.is_finite():
        raise ValueError("amount must be finite")
    if amount < 0:
        raise ValueError("amount cannot be negative")

    month = parse_created_at(created_at)
    return customer_id, amount, month


def aggregate_orders(csv_path: Path):
    """Return monthly totals and a list of invalid-row reports."""
    totals = defaultdict(lambda: defaultdict(Decimal))
    invalid_rows = []

    with csv_path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty or has no header")

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            raise ValueError(f"Missing required column(s): {', '.join(sorted(missing))}")

        for row in reader:
            try:
                customer_id, amount, month = validate_row(row)
                totals[month][customer_id] += amount
            except ValueError as exc:
                invalid_rows.append((reader.line_num, str(exc)))

    return totals, invalid_rows


def print_report(totals):
    """Print each month's customers ordered by revenue, highest first."""
    if not totals:
        print("No valid orders found.")
        return

    for month in sorted(totals):
        print(f"\n{month}")
        print("-" * 36)
        print(f"{'Customer ID':<20}Revenue")
        print("-" * 36)

        ranked_customers = sorted(
            totals[month].items(),
            key=lambda item: (-item[1], item[0]),
        )
        for customer_id, revenue in ranked_customers:
            print(f"{customer_id:<20}{revenue:.2f}")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate order revenue per customer per month."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="orders.csv",
        help="Path to orders.csv (default: orders.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    if not csv_path.is_file():
        print(f"Error: file not found: {csv_path}", file=sys.stderr)
        return 1

    try:
        totals, invalid_rows = aggregate_orders(csv_path)
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print_report(totals)

    print(f"\nInvalid rows skipped: {len(invalid_rows)}")
    for line_number, reason in invalid_rows:
        print(f"  CSV line {line_number}: {reason}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
