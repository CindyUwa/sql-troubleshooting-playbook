# SQL Troubleshooting Playbook — Capital Markets

Production diagnostic runbook for trading application support.
Detects common data anomalies in trading databases:
duplicate trades, sequence gaps, settlement failures,
and latency anomalies.

![Diagnostic Output](![img_7.png](img_7.png))

## Business Context

Application support engineers at banks run daily diagnostics
to catch data issues before they impact traders or regulators.

This playbook simulates that morning check:
pull the trading database, run diagnostic queries,
identify anomalies, and escalate appropriately.

## Scenarios Covered

| Scenario | Issue | Business Impact |
| Duplicate trades | Same trade booked twice | Double position, regulatory risk |
| Sequence gaps | Missing trade messages | Lost orders, reconciliation failure |
| Settlement failures | Trades not settled T+2 | Counterparty risk, regulatory penalty |
| Latency anomaly | Execution > 1000ms | Slippage, SLA breach, client impact |

## Architecture

```
setup.py    →  creates SQLite DB with realistic trade data + intentional bugs
playbook.py →  SQL diagnostic queries (one function per scenario)
main.py     →  runs all scenarios, generates incident report
```

## Run

```bash
python main.py
```

No dependencies — pure Python + SQLite (built-in).

## Sample Output

```
SCENARIO 1 — Duplicate Trade Detection
⚠️ 1 duplicate found:
  Sequence : 5
  Count    : 2 occurrences
  Trade IDs: TRD-0005, TRD-0005-DUP
  Action   : Investigate double submission

SCENARIO 3 — Settlement Failure Detection
⚠️ 2 settlement issues:
  TRD-0011 | GBP/USD SELL | $2,530,000 | PENDING_SETTLEMENT
  TRD-0012 | AAPL BUY | $92,750,000 | FAILED_SETTLEMENT
  Action   : Escalate to settlement desk immediately
```

## Design Decisions

**Why SQLite instead of PostgreSQL?**
Zero setup — runs immediately without Docker.
Same SQL syntax applies to PostgreSQL/Oracle in production.

**Why intentional bugs in the dataset?**
Mirrors real production data quality issues.
The diagnostic value comes from detecting known anomalies.

**Why separate playbook.py from main.py?**
Queries can be imported and reused independently.
Each function is a standalone runbook entry.

## Screenshots

![Full diagnostic output](![img_5.png](img_5.png))
![Duplicate detection](![img_4.png](img_4.png))
![Settlement failures](![img_6.png](img_6.png))
![Latency anomaly](![img_3.png](img_3.png))

## Possible Improvements

- Add PostgreSQL support via psycopg2
- Export report to JSON for ELK ingestion
- Add threshold configuration via config file
- Schedule daily runs via cron
- Add email alerting for critical issues