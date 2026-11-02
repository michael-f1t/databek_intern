import tempfile
import unittest
from pathlib import Path

from orders_report import aggregate_orders


class AggregateOrdersTests(unittest.TestCase):
    def test_aggregates_by_customer_and_month(self):
        csv_text = (
            "order_id,customer_id,amount,created_at\n"
            "1,A,10.25,2026-01-01\n"
            "2,A,4.75,2026-01-15\n"
            "3,B,20.00,2026-01-20\n"
            "4,A,7.00,2026-02-01\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "orders.csv"
            path.write_text(csv_text, encoding="utf-8")
            totals, invalid = aggregate_orders(path)

        self.assertEqual(str(totals["2026-01"]["A"]), "15.00")
        self.assertEqual(str(totals["2026-01"]["B"]), "20.00")
        self.assertEqual(str(totals["2026-02"]["A"]), "7.00")
        self.assertEqual(invalid, [])

    def test_skips_and_reports_invalid_row(self):
        csv_text = (
            "order_id,customer_id,amount,created_at\n"
            "1,A,10.00,2026-01-01\n"
            "2,B,not-a-number,2026-01-02\n"
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "orders.csv"
            path.write_text(csv_text, encoding="utf-8")
            totals, invalid = aggregate_orders(path)

        self.assertEqual(str(totals["2026-01"]["A"]), "10.00")
        self.assertEqual(len(invalid), 1)
        self.assertIn("amount is not a valid number", invalid[0][1])


if __name__ == "__main__":
    unittest.main()
