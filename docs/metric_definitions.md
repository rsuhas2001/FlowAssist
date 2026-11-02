# SLA and routing metrics

- **Unassigned:** leads with no designated owner, including contacted leads that are not eligible for automatic routing.
- **Response SLA breach:** `New` leads with elapsed time from creation to the fixed demo clock exceeding 8 hours if High priority or 24 hours otherwise.
- **Follow-up overdue:** contacted or qualified leads with a `next_followup_at` earlier than the fixed clock.
- **Ownership mismatch:** nonblank owner not in the valid team roster or not eligible for the lead region/segment.
- **Duplicate email:** number of lead records whose nonblank normalized email appears more than once.
- **Escalated:** records manually marked for review in the SQLite queue; no message is sent.
- **Auto-routing:** unowned New leads are assigned only if both email and eligibility constraints pass, rep has capacity, and no duplicate normalized email exists. Ties resolved alphabetically after load.

The scenario clock is fixed at `2026-10-31 18:00`. This means a sample lead does not become overdue just because the reviewer opens the demo months later. Change the seed data or clock explicitly to model another scenario. Existing ownership mismatches are surfaced for review but not automatically overwritten.
