# FlowAssist — Routing operations decision brief

**To:** Revenue Operations Manager  
**From:** Suhas Ramachandra, Portfolio Analyst  
**Scenario:** Synthetic sales queue as of October 31, 2026

## Observed queue health

The 220-record sample contains **93 unassigned leads**, **133 response SLA breaches**, **40 overdue follow-ups**, **87 ownership mismatches**, **5 duplicate-email records** and **7 missing-email records**.

The rule engine is designed to prioritize preserving correct ownership, not maximizing assignment count. One reproducible routing pass assigns **68** eligible unowned New leads, leaving **25** unassigned records requiring other handling. A second routing pass makes no additional assignments unless the underlying data or rules change.

## Recommended operational decisions

1. **Resolve identity exceptions first:** missing or duplicate email records are excluded from auto-routing.
2. **Route only unowned New leads:** existing assignments are reviewed for mismatches but not overwritten without a human decision.
3. **Escalate breaches:** prioritize high-priority SLA breaches and unowned leads reaching response thresholds.
4. **Use the management briefing as a summary, not a decision-maker:** the optional LLM sees only aggregate numbers, and humans verify the resulting text.

## Guardrails

The routing engine applies eligibility, capacity, and stable tie-breaking rules. All changes are written to a local SQLite audit log. No live CRM writes, outbound prospect contacts or production integrations occur.
