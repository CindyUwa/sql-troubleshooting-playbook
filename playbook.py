"""
playbook.py — SQL diagnostic queries for trading production support.

Each function is a runbook entry:
- what to look for
- the SQL query
- how to interpret the results

In production at SocGen/Talan:
these queries are run when investigating incidents.
"""

import sqlite3
from datetime import datetime, timedelta

DB_NAME = "trades.db"


def get_connection():
    return sqlite3.connect(DB_NAME)


# ── Scenario 1 — Duplicate Trades ────────────────────────────────
def find_duplicate_trades():
    """
    Detect trades submitted multiple times.
    Detection method: same sequence_num appears more than once.
    """
    conn = get_connection()
    query = """
    SELECT
        sequence_num,
        COUNT(*) AS occurrence_count,
        GROUP_CONCAT(trade_id, ', ') AS trade_ids,
        symbol,
        side,
        quantity
    FROM trades
    GROUP BY sequence_num
    HAVING COUNT(*) > 1
    ORDER BY occurrence_count DESC
    """
    results = conn.execute(query).fetchall()
    conn.close()
    return results
# ── Scenario 2 — Missing Sequence Numbers ────────────────────────

def find_sequence_gaps():
    """
    Detect gaps in trade sequence numbers.

    In production: gaps indicate lost messages,
    system failures, or network issues.

    Method: compare expected sequence range
    with actual sequence numbers present.
    """
    conn = get_connection()

    # Get all sequence numbers
    sequences = conn.execute(
        "SELECT DISTINCT sequence_num FROM trades ORDER BY sequence_num"
    ).fetchall()
    conn.close()

    sequences = [row[0] for row in sequences]

    if not sequences:
        return []

    # Find gaps
    gaps = []
    for i in range(min(sequences), max(sequences) + 1):
        if i not in sequences:
            gaps.append(i)

    return gaps


# ── Scenario 3 — Failed Settlement ───────────────────────────────

def find_settlement_failures():
    """
    Find trades that failed or are pending settlement.

    In production: settlement failures cause:
    - counterparty risk
    - regulatory penalties
    - cash flow issues

    Standard settlement: T+2 for FX, T+1 for ETD.
    Any trade unsettled after that window is a problem.
    """
    conn = get_connection()
    query = """
    SELECT
        trade_id,
        symbol,
        side,
        quantity,
        price,
        status,
        trader_id,
        submitted_at,
        settled_at,
        ROUND(quantity * price, 2) AS notional_usd
    FROM trades
    WHERE status IN ('PENDING_SETTLEMENT', 'FAILED_SETTLEMENT')
    ORDER BY submitted_at
    """
    results = conn.execute(query).fetchall()
    conn.close()
    return results


# ── Scenario 4 — Latency Anomaly ─────────────────────────────────

def find_latency_anomalies(threshold_ms=1000):
    """
    Find trades with abnormally high execution latency.

    In production: high latency impacts:
    - trade execution quality (slippage)
    - SLA compliance
    - client satisfaction

    Threshold: 1000ms (1 second) — typical SLA in FX trading.
    """
    conn = get_connection()
    query = f"""
    SELECT
        trade_id,
        symbol,
        side,
        quantity,
        latency_ms,
        submitted_at,
        executed_at,
        CASE
            WHEN latency_ms > 3000 THEN 'CRITICAL'
            WHEN latency_ms > 1000 THEN 'HIGH'
            ELSE 'MEDIUM'
        END AS severity
    FROM trades
    WHERE latency_ms > {threshold_ms}
    ORDER BY latency_ms DESC
    """
    results = conn.execute(query).fetchall()
    conn.close()
    return results


# ── Bonus — Trade Summary by Trader ──────────────────────────────

def get_trader_summary():
    """
    Summary of trading activity per trader.
    Useful for daily reconciliation reports.
    """
    conn = get_connection()
    query = """
    SELECT
        trader_id,
        COUNT(*)                    AS total_trades,
        SUM(quantity * price)       AS total_notional,
        AVG(latency_ms)             AS avg_latency_ms,
        SUM(CASE WHEN status = 'SETTLED' THEN 1 ELSE 0 END) AS settled,
        SUM(CASE WHEN status LIKE '%FAIL%'
                  OR status LIKE '%PENDING%' THEN 1 ELSE 0 END) AS issues
    FROM trades
    GROUP BY trader_id
    ORDER BY total_notional DESC
    """
    results = conn.execute(query).fetchall()
    conn.close()
    return results