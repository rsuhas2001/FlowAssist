# FlowAssist data dictionary

## `data/raw/leads.csv` / SQLite `leads`

| Column | Business meaning |
|---|---|
| lead_id | Unique synthetic lead key |
| company, email | Fictional prospect account and `example.test` email |
| region, segment | Territory/segment routing dimensions |
| source | Campaign/lead origin |
| status | New, Contacted or Qualified |
| owner | Current assignment; blank means unassigned |
| created_at, first_contact_at | Event timestamps against a fixed scenario date |
| next_followup_at | Planned outreach deadline |
| priority | High or Normal, determines SLA hours |
| escalated | `0` or `1` flag for human operational review |

## `data/team.json` / `data/routing_rules.json`

`team.json` specifies six eligible reps, territory coverage, segments, and capacity. `routing_rules.json` specifies 8h/24h response thresholds, identity and eligibility requirements, and assignment strategy.

## SQLite `audit`

`event_at`, `lead_id`, `event`, `before_value`, `after_value`, `explanation`. Used for ROUTE, MANUAL_REASSIGN and ESCALATE events. These operations do not contact real customers.
