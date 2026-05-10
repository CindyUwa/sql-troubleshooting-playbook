"""
setup.py — Creates SQLite database with realistic trade data.

Simulates a trading database with intentional bugs:
- duplicate trades
- missing sequence numbers
- failed settlements
- latency anomalies

In production: this would be PostgreSQL or Oracle.
Same SQL patterns apply.
"""

import sqlite3
from datetime import datetime, timedelta
import random

DB_NAME = "trades.db"


def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # ── Trades table ──────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_id        TEXT PRIMARY KEY,
        sequence_num    INTEGER,
        symbol          TEXT,
        side            TEXT,
        quantity        REAL,
        price           REAL,
        status          TEXT,
        trader_id       TEXT,
        submitted_at    TEXT,
        executed_at     TEXT,
        settled_at      TEXT,
        latency_ms      INTEGER
    )
    """)

    # ── Positions table ───────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS positions (
        position_id     TEXT PRIMARY KEY,
        trader_id       TEXT,
        symbol          TEXT,
        quantity        REAL,
        avg_price       REAL,
        updated_at      TEXT
    )
    """)

    conn.commit()
    return conn


def insert_trade_data(conn):
    c = conn.cursor()
    base_time = datetime(2026, 5, 8, 8, 0, 0)

    trades = []

    # Normal trades
    for i in range(1, 11):
        submitted = base_time + timedelta(minutes=i * 3)
        latency = random.randint(50, 200)
        executed = submitted + timedelta(milliseconds=latency)
        settled = submitted + timedelta(days=2)

        trades.append((
            f"TRD-{i:04d}",
            i,
            random.choice(["EUR/USD", "GBP/USD", "AAPL", "SPX"]),
            random.choice(["BUY", "SELL"]),
            random.randint(100000, 5000000),
            round(random.uniform(1.05, 1.15), 4),
            "SETTLED",
            f"TRADER-{random.randint(1, 3):02d}",
            submitted.isoformat(),
            executed.isoformat(),
            settled.isoformat(),
            latency
        ))

    # Bug 1 — Duplicate trade (TRD-0005 submitted twice)
    trades.append((
        "TRD-0005-DUP",
        5,
        "EUR/USD",
        "BUY",
        1000000,
        1.0823,
        "SETTLED",
        "TRADER-01",
        (base_time + timedelta(minutes=15)).isoformat(),
        (base_time + timedelta(minutes=15, milliseconds=120)).isoformat(),
        (base_time + timedelta(days=2, minutes=15)).isoformat(),
        120
    ))

    # Bug 2 — Missing sequence (gap: 7 and 9 exist, 8 missing)
    # sequence 8 intentionally skipped in the data above

    # Bug 3 — Failed settlement (trade not settled after T+2)
    trades.append((
        "TRD-0011",
        11,
        "GBP/USD",
        "SELL",
        2000000,
        1.2650,
        "PENDING_SETTLEMENT",
        "TRADER-02",
        (base_time + timedelta(minutes=33)).isoformat(),
        (base_time + timedelta(minutes=33, milliseconds=180)).isoformat(),
        None,
        180
    ))

    trades.append((
        "TRD-0012",
        12,
        "AAPL",
        "BUY",
        500000,
        185.50,
        "FAILED_SETTLEMENT",
        "TRADER-03",
        (base_time + timedelta(minutes=36)).isoformat(),
        (base_time + timedelta(minutes=36, milliseconds=95)).isoformat(),
        None,
        95
    ))

    # Bug 4 — Latency anomaly (extremely slow execution)
    trades.append((
        "TRD-0013",
        13,
        "SPX",
        "BUY",
        1000000,
        5200.00,
        "SETTLED",
        "TRADER-01",
        (base_time + timedelta(minutes=39)).isoformat(),
        (base_time + timedelta(minutes=39, milliseconds=4500)).isoformat(),
        (base_time + timedelta(days=2, minutes=39)).isoformat(),
        4500  # 4.5 seconds — way above normal
    ))

    c.executemany("""
    INSERT INTO trades VALUES
    (?,?,?,?,?,?,?,?,?,?,?,?)
    """, trades)

    # Positions
    positions = [
        ("POS-001", "TRADER-01", "EUR/USD", 2000000, 1.0823,
         base_time.isoformat()),
        ("POS-002", "TRADER-02", "GBP/USD", -2000000, 1.2650,
         base_time.isoformat()),
        ("POS-003", "TRADER-03", "AAPL", 500000, 185.50,
         base_time.isoformat()),
    ]
    c.executemany("""
    INSERT OR IGNORE INTO positions VALUES (?,?,?,?,?,?)
    """, positions)

    conn.commit()
    print(f"Database created: {DB_NAME}")
    print(f"Trades inserted: {len(trades)}")