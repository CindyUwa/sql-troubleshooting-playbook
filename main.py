"""
main.py — SQL Troubleshooting Playbook runner.

Runs all diagnostic scenarios and generates
a production-style incident report.

This simulates the daily support workflow
at SocGen or Talan application support:
morning check, anomaly detection, escalation.

Usage:
    python main.py
"""

import os
from setup import create_database, insert_trade_data
from playbook import (
    find_duplicate_trades,
    find_sequence_gaps,
    find_settlement_failures,
    find_latency_anomalies,
    get_trader_summary
)


def separator(char="─", width=65):
    print(char * width)


def print_header():
    print("\n" + "═" * 65)
    print("  SQL TROUBLESHOOTING PLAYBOOK")
    print("  Capital Markets — Daily Production Diagnostic")
    print("═" * 65 + "\n")


def run_scenario_1():
    separator()
    print("  SCENARIO 1 — Duplicate Trade Detection")
    separator()
    results = find_duplicate_trades()
    if results:
        print(f"  ⚠️  {len(results)} duplicate(s) found:\n")
        for row in results:
            seq, count, ids, symbol, side, qty = row
            print(f"  Sequence : {seq}")
            print(f"  Count    : {count} occurrences")
            print(f"  Trade IDs: {ids}")
            print(f"  Symbol   : {symbol} | {side} | {qty:,.0f}")
            print(f"  Action   : Investigate double submission, "
                  f"check idempotency keys\n")
    else:
        print("  ✅ No duplicates found\n")


def run_scenario_2():
    separator()
    print("  SCENARIO 2 — Sequence Gap Detection")
    separator()
    gaps = find_sequence_gaps()
    if gaps:
        print(f"  ⚠️  {len(gaps)} gap(s) in sequence:\n")
        print(f"  Missing sequence numbers: {gaps}")
        print(f"  Action: Check FIX engine logs for missing messages")
        print(f"          Verify network connectivity at gap timestamps\n")
    else:
        print("  ✅ No sequence gaps found\n")


def run_scenario_3():
    separator()
    print("  SCENARIO 3 — Settlement Failure Detection")
    separator()
    results = find_settlement_failures()
    if results:
        print(f"  ⚠️  {len(results)} settlement issue(s):\n")
        for row in results:
            tid, sym, side, qty, price, status, trader, submitted, settled, notional = row
            print(f"  Trade ID  : {tid}")
            print(f"  Symbol    : {sym} | {side} | {qty:,.0f}")
            print(f"  Notional  : ${notional:,.2f}")
            print(f"  Status    : {status}")
            print(f"  Trader    : {trader}")
            print(f"  Submitted : {submitted}")
            print(f"  Settled   : {settled or 'NOT SETTLED'}")
            print(f"  Action    : Escalate to settlement desk immediately\n")
    else:
        print("  ✅ No settlement failures\n")


def run_scenario_4():
    separator()
    print("  SCENARIO 4 — Latency Anomaly Detection")
    separator()
    results = find_latency_anomalies(threshold_ms=1000)
    if results:
        print(f"  ⚠️  {len(results)} latency anomaly(ies):\n")
        for row in results:
            tid, sym, side, qty, latency, submitted, executed, severity = row
            print(f"  Trade ID  : {tid}")
            print(f"  Symbol    : {sym} | {side}")
            print(f"  Latency   : {latency}ms [{severity}]")
            print(f"  Submitted : {submitted}")
            print(f"  Executed  : {executed}")
            print(f"  Action    : Check system load at execution time\n")
    else:
        print("  ✅ No latency anomalies\n")


def run_trader_summary():
    separator()
    print("  TRADER SUMMARY — Daily Reconciliation")
    separator()
    results = get_trader_summary()
    print(f"  {'Trader':<12} {'Trades':>8} "
          f"{'Notional':>18} {'Avg Latency':>14} "
          f"{'Settled':>9} {'Issues':>8}")
    separator("-")
    for row in results:
        trader, total, notional, avg_lat, settled, issues = row
        flag = "⚠️ " if issues > 0 else "✅"
        print(f"  {flag} {trader:<10} {total:>8} "
              f"${notional:>16,.0f} "
              f"{avg_lat:>12.0f}ms "
              f"{settled:>9} {issues:>8}")
    print()


def main():
    # Remove existing database to ensure clean run with all bugs
    if os.path.exists("trades.db"):
        os.remove("trades.db")

    # Setup fresh database
    conn = create_database()
    insert_trade_data(conn)
    conn.close()

    print_header()
    run_scenario_1()
    run_scenario_2()
    run_scenario_3()
    run_scenario_4()
    run_trader_summary()

    separator("═")
    print("  Diagnostic complete. Review alerts above.")
    separator("═")


if __name__ == "__main__":
    main()