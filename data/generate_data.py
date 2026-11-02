"""Deterministic synthetic lead queue: reproducible operational edge cases."""
from datetime import datetime,timedelta
from pathlib import Path
import random,csv,json
R=random.Random(7491)
AS_OF=datetime(2026,10,31,18,0,0)
OUT=Path(__file__).resolve().parent
TEAM=[
 {'name':'Amira Chen','regions':['East','Central'],'segments':['SMB','Mid-market'],'capacity':60},
 {'name':'Noah Brooks','regions':['East','Central'],'segments':['SMB','Enterprise'],'capacity':60},
 {'name':'Priya Shah','regions':['West'],'segments':['SMB','Mid-market'],'capacity':60},
 {'name':'Mateo Garcia','regions':['West'],'segments':['Mid-market','Enterprise'],'capacity':60},
 {'name':'Leah Patel','regions':['East','Central'],'segments':['Enterprise','Mid-market'],'capacity':60},
 {'name':'Ethan Wright','regions':['West'],'segments':['SMB','Enterprise'],'capacity':60},
]

def generate(n=220):
    rows=[]
    for i in range(1,n+1):
        lid=f'FL{i:05d}';created=AS_OF-timedelta(hours=R.randint(2,150))
        segment=R.choices(['SMB','Mid-market','Enterprise'],weights=[47,37,16])[0]
        region=R.choices(['East','Central','West'],weights=[42,27,31])[0]
        status=R.choices(['New','Contacted','Qualified'],weights=[70,24,6])[0]
        owner=R.choice(TEAM)['name'] if R.random()<.55 else ''
        # Deliberate invalid ownership to exercise exception triage.
        if i%27==0:owner='Unlisted User'
        email=f'contact{i:04d}@example.test'
        if i%31==0:email=''
        if i%47==0:email='contact0001@example.test'
        contacted=created+timedelta(hours=R.randint(2,65)) if status!='New' else None
        if contacted is not None and contacted>AS_OF:
            status='New';contacted=None
        follow=(contacted+timedelta(hours=R.randint(10,55))) if contacted else None
        rows.append({'lead_id':lid,'company':f'Example Business {i:03d}','email':email,'region':region,'segment':segment,'source':R.choice(['Demo request','Webinar','Outbound','Referral','Paid search']),'status':status,'owner':owner,'created_at':created.isoformat(timespec='seconds'),'first_contact_at':contacted.isoformat(timespec='seconds') if contacted else '', 'next_followup_at':follow.isoformat(timespec='seconds') if follow else '', 'priority':'High' if segment=='Enterprise' or i%13==0 else 'Normal','escalated':'0'})
    with (OUT/'raw/leads.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/'team.json').write_text(json.dumps(TEAM,indent=2)+'\n')
    (OUT/'routing_rules.json').write_text(json.dumps({'response_sla_hours':{'High':8,'Normal':24},'followup_sla_hours':36,'assign_only_statuses':['New'],'routing_strategy':'lowest_active_load_then_name','duplicate_key':'normalized_email','assignment_requires':['email','region','segment']},indent=2)+'\n')
    print(f'Generated {len(rows)} synthetic leads and {len(TEAM)} reps')
if __name__=='__main__':generate()
