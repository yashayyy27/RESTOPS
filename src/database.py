"""Load cleaned facts and dimensions into an integrity-checked SQLite database."""

import sqlite3

import pandas as pd

from .common import PROCESSED, ROOT

TABLE_ORDER = [
    "restaurants",
    "products",
    "calendar",
    "manager_assignments",
    "promotions",
    "targets",
    "operating_costs",
    "orders",
    "transactions",
    "labour",
    "customer_feedback",
    "loyalty",
    "waste",
    "delivery",
    "store_month_kpis",
]


def run():
    """Rebuild only this generated database; preserve raw source exports."""
    path = PROCESSED / "restops.sqlite"
    with sqlite3.connect(path) as connection:
        # Existing project tables are replaced in reverse FK order.
        connection.execute("PRAGMA foreign_keys = OFF")
        for name in reversed(TABLE_ORDER):
            connection.execute(f'DROP TABLE IF EXISTS "{name}"')
        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript((ROOT / "sql/schema.sql").read_text())
        for name in TABLE_ORDER:
            for frame in pd.read_csv(
                PROCESSED / f"{name}.csv", chunksize=50000, low_memory=False
            ):
                frame.to_sql(
                    name, connection, if_exists="append", index=False, chunksize=1000
                )
        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"Foreign-key violations: {violations[:5]}")
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_store_date ON transactions(restaurant_id, business_date)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_tx_order ON transactions(order_id)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id, business_date)"
        )
    print("SQLite loaded and foreign keys checked.", flush=True)


if __name__ == "__main__":
    run()
