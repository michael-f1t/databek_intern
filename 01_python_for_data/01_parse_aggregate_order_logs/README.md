# Monthly Customer Revenue Report

A small Python script that reads `orders.csv`, skips and reports invalid rows, and prints total revenue for each customer in each month.

## Requirements

- Python 3.9+
- No third-party packages are required.

## CSV format

The input CSV must contain these columns:

```csv
order_id,customer_id,amount,created_at
1001,C001,120.50,2026-01-05
1002,C002,80.00,2026-01-12
1003,C001,40.00,2026-02-01
```

`created_at` should be an ISO date or datetime, for example `2026-01-05` or `2026-01-05T14:30:00Z`.

## Run

Put `orders.csv` in the project root, then run:

```bash
python orders_report.py
```

Or provide a different CSV path:

```bash
python orders_report.py data/orders.csv
```

The report is grouped by month. Within each month, customers are sorted by revenue from highest to lowest. Ties are sorted by customer ID.

Invalid rows are skipped and reported with their CSV line number and reason. The script checks for missing IDs, invalid/negative amounts, and invalid dates.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Design notes

- Uses Python's built-in `csv` module to read the file.
- Uses `Decimal` for reliable money calculations.
- Uses dictionaries to aggregate each customer's revenue by month.
- Separates validation, aggregation, and report printing into small functions.
