# Project interview case study — FlowAssist — Rule-Based Lead Routing, SLA Triage & AI Briefings

## 1. Business problem

Sales operations teams need consistent lead ownership, fast follow-ups, auditable rerouting decisions, and rapid management updates that do not overwrite legitimate CRM activity.

## 2. Stakeholders

Sales/Revenue Operations leadership, Business Development teams, cross-functional marketing and operations managers, and analysts maintaining trusted reporting.

## 3. My technical approach

1. Apply a deterministic territory + segment assignment rule to eligible unowned New leads
2. Balance routing by current assigned workload and explicit rep capacity; reject duplicate identities or incomplete lead records
3. Flag response SLA breaches, overdue follow-ups, ownership mismatches and duplicate contact records
4. Support manual reassignment with server-side eligibility validation and one-click escalation
5. Persist the lead queue and all routing/escalation actions in SQLite with exportable audit logs
6. Generate management briefings from verified aggregate facts: offline rule-based text always works; optional API-backed LLM summarization with a user key

## 4. Demonstration

Inspect the exception-first queue and note the response SLA and ownership mismatch counts. Click **Run deterministic routing**; verify the unassigned count drops and new audit entries appear; run it again to confirm no duplicate routing. Escalate a problematic lead, assign an eligible representative, export the audit, and generate the offline management briefing. Use **Reset demo** to restart.

## 5. The outcome I can describe

The project implements an operational tool against original synthetic data. I can demonstrate working code, repeatable test results, usable reports and the decisions it would enable. **No ROI, adoption, employer usage, or real sales improvement is claimed.**

### Potential resume bullet AFTER verifying it runs locally

> Developed a rule-based sales operations automation application using Python and SQLite to assign leads by territory, segment and capacity, identify follow-up SLA exceptions, log auditable actions, and produce verified management briefings with optional LLM summarization.

## 6. Important limitations

No real lead messages, email sending, production CRM mutations or PII; assignment rules intentionally simplified; the LLM is optional and is never responsible for routing. All activity is simulated at a fixed scenario date.

## 7. Questions a hiring manager may ask

- What is the source of truth for each field and how do you reconcile disagreement?
- Which numerical metrics are descriptive versus causal?
- Why are these particular data-quality rules / SLA thresholds defensible?
- How do you test behavior, handle missing data and audit exceptions?
- What would change when moving from static CSV inputs to authenticated production systems?
- What are the trade-offs among speed, interpretability, reliability and privacy?

## 8. Why it fits sales operations roles

Directly maps to lead routing, queue ownership, SLA monitoring, recurring operational requests, AI augmentation, and manager communications.
