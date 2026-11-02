from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src import engine as e
from src.app import app

def test_seed_and_exception_detection(tmp_path):
    db=tmp_path/'flow.sqlite3';e.init_db(db)
    leads=e.load(db);s=e.analyze(leads)
    assert len(leads)==220
    assert s['unassigned']>0 and s['sla_breaches']>0
    assert s['duplicates']>0 and s['missing_email']>0

def test_routing_is_idempotent_and_eligible(tmp_path):
    db=tmp_path/'flow.sqlite3';e.init_db(db)
    before=e.analyze(e.load(db))['unassigned']
    routed=e.route_unassigned(db)
    after=e.analyze(e.load(db))['unassigned']
    assert routed>0 and before-after==routed
    assert e.route_unassigned(db)==0
    for event in e.audit(db):
        if event['event']=='ROUTE':
            lead=next(x for x in e.load(db) if x['lead_id']==event['lead_id'])
            rep=next(x for x in e.TEAM if x['name']==event['after_value'])
            assert lead['region'] in rep['regions'] and lead['segment'] in rep['segments']

def test_manual_assignment_validation_and_audit(tmp_path):
    db=tmp_path/'flow.sqlite3';e.init_db(db)
    l=next(x for x in e.load(db) if x['region']=='East' and x['segment']=='Enterprise')
    with pytest.raises(ValueError):e.update_owner(l['lead_id'],'Unknown',db)
    e.update_owner(l['lead_id'],'Leah Patel',db)
    e.escalate(l['lead_id'],db)
    assert len(e.audit(db))==2
    assert next(x for x in e.load(db) if x['lead_id']==l['lead_id'])['escalated']=='1'

def test_briefing_no_key(monkeypatch,tmp_path):
    monkeypatch.delenv('OPENAI_API_KEY',raising=False)
    db=tmp_path/'flow.sqlite3';e.init_db(db)
    s=e.analyze(e.load(db));brief,mode=e.optional_llm_briefing(s)
    assert 'rules-based' in mode.lower()
    assert str(s['total']) in brief

def test_http_routes(monkeypatch,tmp_path):
    monkeypatch.setattr(e,'DB',tmp_path/'web.sqlite3')
    c=TestClient(app)
    assert c.get('/').status_code==200
    assert c.get('/api/summary').json()['total_leads']==220
    assert 'lead_id' in c.get('/export/queue.csv').text
    assert c.post('/run-routing').status_code==200
    assert c.post('/briefing').status_code==200
    assert c.get('/export/audit.csv').status_code==200
    assert c.post('/reset').status_code==200
    assert c.get('/api/summary').json()['unassigned_leads']>0
