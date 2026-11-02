from pathlib import Path
import csv,io
from fastapi import FastAPI,Form
from fastapi.responses import HTMLResponse,RedirectResponse,Response,JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from . import engine as e

ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='FlowAssist',version='1.0',description='Synthetic CRM routing, SLA monitoring and audit trail.')
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
tpl=Jinja2Templates(directory=ROOT/'templates')

def context(request,brief=None,mode=None,msg=None):
    leads=e.load();s=e.analyze(leads)
    queue=sorted(s['leads'],key=lambda l:(-len(l['issues']),l['created_at']))
    return dict(request=request,title='Routing & SLA operations',s=s,leads=queue[:65],team=e.TEAM,audit=e.audit()[:15],brief=brief,mode=mode,msg=msg,asof=e.AS_OF.strftime('%b %d, %Y'))

@app.get('/',response_class=HTMLResponse)
def dashboard(request:Request):return tpl.TemplateResponse(request,'dashboard.html',context(request))

@app.post('/run-routing',response_class=HTMLResponse)
def run_routing(request:Request):
    changed=e.route_unassigned()
    return tpl.TemplateResponse(request,'dashboard.html',context(request,msg=f'Routed {changed} eligible, previously unassigned new leads. Changes saved to SQLite and audit log.'))

@app.post('/escalate/{lead_id}',response_class=HTMLResponse)
def escalate(lead_id:str,request:Request):
    try:e.escalate(lead_id);msg=f'{lead_id} flagged for human follow-up.'
    except KeyError:msg='Lead does not exist.'
    return tpl.TemplateResponse(request,'dashboard.html',context(request,msg=msg))

@app.post('/reassign/{lead_id}',response_class=HTMLResponse)
def reassign(lead_id:str,request:Request,owner:str=Form(...)):
    try:e.update_owner(lead_id,owner);msg=f'{lead_id} assigned to {owner} with skill/territory validation.'
    except (KeyError,ValueError) as ex:msg=f'Assignment rejected: {ex}'
    return tpl.TemplateResponse(request,'dashboard.html',context(request,msg=msg))

@app.post('/briefing',response_class=HTMLResponse)
def briefing(request:Request):
    s=e.analyze(e.load());brief,mode=e.optional_llm_briefing(s)
    return tpl.TemplateResponse(request,'dashboard.html',context(request,brief=brief,mode=mode))

@app.post('/reset',response_class=HTMLResponse)
def reset(request:Request):
    e.init_db(reset=True)
    return tpl.TemplateResponse(request,'dashboard.html',context(request,msg='Demo reset to the original synthetic lead queue.'))

@app.get('/api/summary')
def summary():
    s=e.analyze(e.load());return {**e.briefing_facts(s),'issue_counts':s['issue_counts']}

@app.get('/export/{kind}.csv')
def export(kind:str):
    if kind not in ('queue','audit'):return JSONResponse({'error':'Unknown export'},status_code=404)
    rows=e.load() if kind=='queue' else e.audit()
    buf=io.StringIO();fields=list(rows[0]) if rows else (['lead_id'] if kind=='queue' else ['id'])
    writer=csv.DictWriter(buf,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return Response(buf.getvalue(),media_type='text/csv',headers={'Content-Disposition':f'attachment; filename="flowassist_{kind}.csv"'})

@app.get('/health')
def health():return {'status':'ok','synthetic':True,'rows':len(e.load()),'as_of':e.AS_OF.isoformat()}
