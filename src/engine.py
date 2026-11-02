"""Lead routing decision engine and auditable SQLite state store."""
from pathlib import Path
import sqlite3,json,csv
from datetime import datetime,timedelta
from collections import Counter
from contextlib import contextmanager

ROOT=Path(__file__).resolve().parents[1]
AS_OF=datetime(2026,10,31,18,0,0) # fixed scenario clock for reproducibility
DB=ROOT/'runtime/flowassist.sqlite3'
TEAM=json.loads((ROOT/'data/team.json').read_text())
RULES=json.loads((ROOT/'data/routing_rules.json').read_text())

@contextmanager
def connect(db=None):
    with sqlite3.connect(str(db or DB)) as conn:
        conn.row_factory=sqlite3.Row
        yield conn
        conn.commit()

def init_db(db=None,reset=False):
    target=Path(db or DB);target.parent.mkdir(exist_ok=True,parents=True)
    if reset and target.exists():target.unlink()
    with connect(target) as c:
        c.execute('''CREATE TABLE IF NOT EXISTS leads (lead_id TEXT PRIMARY KEY, company TEXT, email TEXT, region TEXT, segment TEXT, source TEXT, status TEXT, owner TEXT, created_at TEXT, first_contact_at TEXT, next_followup_at TEXT, priority TEXT, escalated TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, event_at TEXT, lead_id TEXT, event TEXT, before_value TEXT, after_value TEXT, explanation TEXT)''')
        count=c.execute('SELECT COUNT(*) FROM leads').fetchone()[0]
        if count==0:
            with (ROOT/'data/raw/leads.csv').open(newline='',encoding='utf-8') as f:
                rows=list(csv.DictReader(f))
            fields=list(rows[0]);c.executemany('INSERT INTO leads ('+','.join(fields)+') VALUES ('+','.join(['?']*len(fields))+')',[tuple(row.values()) for row in rows])
    return target

def load(db=None):
    init_db(db)
    with connect(db) as c:return [dict(x) for x in c.execute('SELECT * FROM leads ORDER BY created_at DESC')]

def audit(db=None):
    init_db(db)
    with connect(db) as c:return [dict(x) for x in c.execute('SELECT * FROM audit ORDER BY id DESC')]

def duplicate_emails(leads):
    counts=Counter(str(x['email']).strip().lower() for x in leads if x['email'].strip())
    return {k for k,v in counts.items() if v>1}

def issue_tags(lead,dupes):
    issues=[]
    email=lead['email'].strip().lower()
    if not email:issues.append('Missing email')
    elif email in dupes:issues.append('Duplicate email')
    owner=lead['owner']; rep=next((r for r in TEAM if r['name']==owner),None)
    if owner and (rep is None or lead['region'] not in rep['regions'] or lead['segment'] not in rep['segments']):issues.append('Ownership mismatch')
    created=datetime.fromisoformat(lead['created_at']);prio=lead['priority']
    if lead['status']=='New' and (AS_OF-created).total_seconds()/3600>RULES['response_sla_hours'][prio]:issues.append('Response SLA breached')
    if lead['status']!='New' and lead['next_followup_at'] and datetime.fromisoformat(lead['next_followup_at'])<AS_OF:issues.append('Follow-up overdue')
    return issues

def analyze(leads):
    duplicates=duplicate_emails(leads)
    enriched=[]
    for l in leads:enriched.append({**l,'issues':issue_tags(l,duplicates)})
    c=Counter(issue for l in enriched for issue in l['issues'])
    return {'total':len(enriched),'unassigned':sum(not l['owner'] for l in enriched),'sla_breaches':c['Response SLA breached'],'followups_overdue':c['Follow-up overdue'],'mismatched':c['Ownership mismatch'],'missing_email':c['Missing email'],'duplicates':c['Duplicate email'],'escalated':sum(l['escalated']=='1' for l in enriched),'issue_counts':dict(c),'leads':enriched}

def route_unassigned(db=None):
    leads=load(db)
    dupes=duplicate_emails(leads)
    active=Counter(x['owner'] for x in leads if x['owner'] and x['status']!='Qualified')
    changes=[]
    for lead in sorted(leads,key=lambda x:(x['created_at'],x['lead_id'])):
        if lead['owner'] or lead['status'] not in RULES['assign_only_statuses']:continue
        if not lead['email'].strip() or lead['email'].strip().lower() in dupes:continue
        candidates=[r for r in TEAM if lead['region'] in r['regions'] and lead['segment'] in r['segments'] and active[r['name']]<r['capacity']]
        if not candidates:continue
        rep=min(candidates,key=lambda r:(active[r['name']],r['name']))
        active[rep['name']]+=1
        changes.append((rep['name'],lead['lead_id']))
    with connect(db) as c:
        for owner,lid in changes:
            c.execute("UPDATE leads SET owner=? WHERE lead_id=? AND owner=''",(owner,lid))
            c.execute('INSERT INTO audit(event_at,lead_id,event,before_value,after_value,explanation) VALUES(?,?,?,?,?,?)',(AS_OF.isoformat(),lid,'ROUTE','',owner,'Matched region and segment; assigned to lowest-load eligible rep'))
    return len(changes)

def update_owner(lead_id,owner,db=None):
    valid={x['name'] for x in TEAM}
    if owner not in valid:raise ValueError('Unknown owner')
    init_db(db)
    with connect(db) as c:
        lead=c.execute('SELECT * FROM leads WHERE lead_id=?',(lead_id,)).fetchone()
        if not lead:raise KeyError(lead_id)
        rep=next(x for x in TEAM if x['name']==owner)
        if lead['region'] not in rep['regions'] or lead['segment'] not in rep['segments']:raise ValueError('Owner ineligible for lead segment/region')
        before=lead['owner'];c.execute('UPDATE leads SET owner=? WHERE lead_id=?',(owner,lead_id))
        c.execute('INSERT INTO audit(event_at,lead_id,event,before_value,after_value,explanation) VALUES(?,?,?,?,?,?)',(AS_OF.isoformat(),lead_id,'MANUAL_REASSIGN',before,owner,'Manual assignment with territory/segment validation'))

def escalate(lead_id,db=None):
    init_db(db)
    with connect(db) as c:
        if not c.execute('SELECT 1 FROM leads WHERE lead_id=?',(lead_id,)).fetchone():raise KeyError(lead_id)
        c.execute("UPDATE leads SET escalated='1' WHERE lead_id=?",(lead_id,))
        c.execute('INSERT INTO audit(event_at,lead_id,event,before_value,after_value,explanation) VALUES(?,?,?,?,?,?)',(AS_OF.isoformat(),lead_id,'ESCALATE','0','1','Flagged for human operational follow-up'))

def briefing_facts(summary):
    return {'sample_clock':AS_OF.isoformat(),'total_leads':summary['total'],'unassigned_leads':summary['unassigned'],'response_sla_breaches':summary['sla_breaches'],'overdue_followups':summary['followups_overdue'],'ownership_mismatches':summary['mismatched'],'duplicate_email_records':summary['duplicates'],'missing_email_records':summary['missing_email']}

def deterministic_briefing(s):
    return f"As of {AS_OF:%Y-%m-%d}, the synthetic queue contains {s['total']} leads; {s['unassigned']} remain unassigned. The audit flags {s['sla_breaches']} response SLA breaches and {s['followups_overdue']} overdue follow-ups. Prioritize response breaches and incomplete ownership first; verify {s['mismatched']} ownership mismatches before changing routing rules. This is a rules-based briefing, not an LLM result."

def optional_llm_briefing(summary):
    import os
    key=os.environ.get('OPENAI_API_KEY','').strip()
    if not key:return deterministic_briefing(summary),'Rules-based fallback (no API key)'
    from openai import OpenAI
    try:
        client=OpenAI(api_key=key,timeout=15,max_retries=0)
        response=client.responses.create(model=os.environ.get('OPENAI_MODEL','gpt-4o-mini'),instructions='You are a sales operations analyst. Use ONLY the aggregated numerical facts provided. Write 3 concise management sentences, include uncertainty, recommend actions; do not invent trends or CRM interventions. No personally identifying lead data are supplied.',input=json.dumps(briefing_facts(summary)))
        return response.output_text,'LLM-generated from aggregated synthetic queue facts; verify before use'
    except Exception as ex:return deterministic_briefing(summary),'Fallback: LLM request unavailable; rules-based summary shown'
