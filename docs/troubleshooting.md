# Troubleshooting Guide — SQL Playbook

## Scenario 1: Duplicate Trades

**Detection query:**
Groups by sequence_num + symbol + side + quantity.
Any group with COUNT > 1 is a duplicate.

**Root causes:**
- FIX engine retry without idempotency check
- Network timeout causing double submission
- OMS bug during failover

**Resolution steps:**
1. Identify both trade IDs
2. Check timestamps — which arrived first?
3. Cancel the duplicate in the OMS
4. Notify settlement desk
5. File incident report

---

## Scenario 2: Sequence Gaps

**Detection method:**
Compare expected range (min to max seq) with actual sequences.
Any integer in the range not present = gap.

**Root causes:**
- FIX message lost in transit
- Network partition during trading session
- System restart during market hours

**Resolution steps:**
1. Note the gap sequence numbers
2. Check FIX engine logs at that timestamp
3. Check network logs for packet loss
4. Request resend from counterparty if needed

---

## Scenario 3: Settlement Failures

**Detection query:**
Filters status IN ('PENDING_SETTLEMENT', 'FAILED_SETTLEMENT').

**Root causes:**
- Insufficient funds at settlement
- Incorrect settlement instructions
- Counterparty default
- System outage at settlement time

**Resolution steps:**
1. Escalate to settlement desk immediately
2. Contact counterparty to confirm instructions
3. Check cash positions
4. Notify compliance if T+2 breached

---

## Scenario 4: Latency Anomalies

**Thresholds:**
- MEDIUM: > 1000ms
- HIGH: > 3000ms
- CRITICAL: > 5000ms

**Root causes:**
- System overload during peak trading
- Network congestion
- Database lock contention
- Vendor API slowness

**Resolution steps:**
1. Check system CPU/memory at execution time
2. Check network latency logs
3. Review concurrent trade volume
4. Escalate to infrastructure team if persistent