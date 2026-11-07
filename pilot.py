"""Self-contained, synthetic Mulshi pilot data and event-driven referral engine."""
import sqlite3, math
from datetime import datetime, timezone
from pathlib import Path
DB=Path(__file__).parent/'pilot_demo.db'
# Approximate demonstration coordinates, not a verified facility geocoding directory.
VILLAGES=[('Paud',18.524,73.615,'PHC Maan'),('Pirangut',18.510,73.682,'PHC Maan'),('Maan',18.564,73.725,'PHC Maan'),('Lavale',18.539,73.729,'PHC Maan'),('Bhugaon',18.500,73.752,'PHC Maan'),('Mutha',18.450,73.620,'PHC Mutha'),('Male',18.585,73.590,'PHC Male'),('Ambavane',18.640,73.470,'PHC Ambavane')]
FACILITIES=[('PHC Maan','PHC',18.564,73.725,1,0,'Maan'),('PHC Mutha','PHC',18.450,73.620,1,1,'Mutha'),('PHC Male','PHC',18.585,73.590,1,1,'Male'),('PHC Ambavane','PHC',18.640,73.470,0,0,'Ambavane'),('Rural Hospital Paud','Rural Hospital',18.524,73.615,1,1,'Paud'),('District Hospital Demo','District Hospital',18.510,73.850,1,1,'Outside pilot')]
ROLES=['ASHA','Anganwadi Worker','MPW','ANM','CHO','Medical Officer','Block Health Officer','MS — RH / CHC / SDH','District Health Officer','Civil Surgeon']
EVENTS=['Created','Notified','Acknowledged','Transport started','Arrived','Care started','Feedback recorded','Community follow-up closed']
def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def connect():
    c=sqlite3.connect(DB,timeout=20); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON');return c
def init():
    with connect() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS villages(id INTEGER PRIMARY KEY,name TEXT UNIQUE,lat REAL,lon REAL,assigned_phc TEXT);
        CREATE TABLE IF NOT EXISTS facilities(id INTEGER PRIMARY KEY,name TEXT UNIQUE,type TEXT,lat REAL,lon REAL,emergency_capable INTEGER,antivenom_demo INTEGER,area TEXT);
        CREATE TABLE IF NOT EXISTS journeys(id INTEGER PRIMARY KEY AUTOINCREMENT,patient_alias TEXT NOT NULL,village TEXT NOT NULL,reason TEXT NOT NULL,priority TEXT NOT NULL,origin_role TEXT NOT NULL,assigned_asha TEXT NOT NULL,destination TEXT NOT NULL,eta TEXT,created_at TEXT NOT NULL,status TEXT NOT NULL,feedback TEXT DEFAULT '',outcome TEXT DEFAULT '');
        CREATE TABLE IF NOT EXISTS legs(id INTEGER PRIMARY KEY AUTOINCREMENT,journey_id INTEGER NOT NULL REFERENCES journeys(id),source TEXT NOT NULL,destination TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,journey_id INTEGER NOT NULL REFERENCES journeys(id),leg_id INTEGER REFERENCES legs(id),event_type TEXT NOT NULL,actor_role TEXT NOT NULL,actor_label TEXT NOT NULL,facility TEXT,details TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT,journey_id INTEGER,recipient TEXT,message TEXT,created_at TEXT,read_at TEXT);''')
        c.executemany('INSERT OR IGNORE INTO villages(name,lat,lon,assigned_phc) VALUES(?,?,?,?)',VILLAGES)
        c.executemany('INSERT OR IGNORE INTO facilities(name,type,lat,lon,emergency_capable,antivenom_demo,area) VALUES(?,?,?,?,?,?,?)',FACILITIES)
def rows(sql,args=()):
    with connect() as c: return [dict(r) for r in c.execute(sql,args)]
def villages(): return rows('SELECT * FROM villages ORDER BY name')
def facilities(): return rows('SELECT * FROM facilities ORDER BY name')
def journeys(): return rows('SELECT * FROM journeys ORDER BY id DESC')
def get(jid):
    r=rows('SELECT * FROM journeys WHERE id=?',(jid,));return r[0] if r else None
def events(jid): return rows('SELECT * FROM events WHERE journey_id=? ORDER BY id',(jid,))
def legs(jid): return rows('SELECT * FROM legs WHERE journey_id=? ORDER BY id',(jid,))
def distance(a,b,c,d):
    r=6371.0088;p1,p2=math.radians(a),math.radians(c);dp=p2-p1;dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.atan2(math.sqrt(x),math.sqrt(max(0,1-x)))
def ranked(village,emergency=False):
    v=next(x for x in villages() if x['name']==village)
    out=[]
    for f in facilities():
        f['km']=round(distance(v['lat'],v['lon'],f['lat'],f['lon']),1)
        f['eligible_demo']=bool(f['emergency_capable'] and f['antivenom_demo']) if emergency else True
        f['assigned']=f['name']==v['assigned_phc'];out.append(f)
    return sorted(out,key=lambda x:(not x['eligible_demo'],x['km']))
def create(patient_alias,village,reason,priority,origin_role,assigned_asha,destination,eta):
    if not all([patient_alias.strip(),village,reason.strip(),destination,assigned_asha.strip()]):raise ValueError('Required fields missing')
    if origin_role not in ROLES:raise ValueError('Unknown role')
    if destination not in {f['name'] for f in facilities()}:raise ValueError('Unknown facility')
    if village not in {v['name'] for v in villages()}:raise ValueError('Unknown village')
    with connect() as c:
        t=now();cur=c.execute('INSERT INTO journeys(patient_alias,village,reason,priority,origin_role,assigned_asha,destination,eta,created_at,status) VALUES(?,?,?,?,?,?,?,?,?,?)',(patient_alias.strip(),village,reason.strip(),priority,origin_role,assigned_asha.strip(),destination,eta,t,'Created'));jid=cur.lastrowid
        leg=c.execute('INSERT INTO legs(journey_id,source,destination,created_at) VALUES(?,?,?,?)',(jid,village,destination,t)).lastrowid
        c.execute('INSERT INTO events(journey_id,leg_id,event_type,actor_role,actor_label,facility,details,created_at) VALUES(?,?,?,?,?,?,?,?)',(jid,leg,'Created',origin_role,origin_role,village,'Referral created; destination: '+destination,t))
        c.execute('INSERT INTO alerts(journey_id,recipient,message,created_at) VALUES(?,?,?,?)',(jid,destination,f'Incoming {priority} referral REF-{jid:05d} from {village}',t))
        return jid
# Explicit role capabilities; UI switching is only a demo, not authentication.
PERMISSIONS={'Notified':ROLES,'Acknowledged':['CHO','Medical Officer','MS — RH / CHC / SDH'],'Transport started':['ASHA','Anganwadi Worker','MPW','ANM','CHO','Medical Officer','MS — RH / CHC / SDH'],'Arrived':['ANM','CHO','Medical Officer','MS — RH / CHC / SDH'],'Care started':['CHO','Medical Officer','MS — RH / CHC / SDH'],'Feedback recorded':['CHO','Medical Officer','MS — RH / CHC / SDH'],'Community follow-up closed':['ASHA']}
def advance(jid,event,role,details='',outcome=''):
    j=get(jid)
    if not j:raise ValueError('Unknown referral')
    if event not in EVENTS[1:]:raise ValueError('Unknown event')
    if role not in PERMISSIONS.get(event,[]):raise PermissionError('Role cannot record this event')
    if j['status']=='Community follow-up closed':raise ValueError('Journey already closed')
    history=[e['event_type'] for e in events(jid)]
    if event in history and event not in ('Transport started','Arrived','Care started'):raise ValueError('Event already recorded')
    if event=='Community follow-up closed' and 'Feedback recorded' not in history:raise ValueError('Feedback required before ASHA closure')
    if event=='Feedback recorded' and not details.strip():raise ValueError('Clinical feedback details required')
    with connect() as c:
        t=now();leg=c.execute('SELECT id FROM legs WHERE journey_id=? ORDER BY id DESC LIMIT 1',(jid,)).fetchone()['id']
        c.execute('INSERT INTO events(journey_id,leg_id,event_type,actor_role,actor_label,facility,details,created_at) VALUES(?,?,?,?,?,?,?,?)',(jid,leg,event,role,role,j['destination'],details,t))
        c.execute('UPDATE journeys SET status=? WHERE id=?',(event,jid))
        if event=='Feedback recorded':c.execute('UPDATE journeys SET feedback=?,outcome=? WHERE id=?',(details,outcome,jid))
        if event in ('Feedback recorded','Arrived','Community follow-up closed'):
            c.execute('INSERT INTO alerts(journey_id,recipient,message,created_at) VALUES(?,?,?,?)',(jid,j['assigned_asha'],f'REF-{jid:05d}: {event}',t))
def transfer(jid,role,destination,reason):
    j=get(jid)
    if not j or j['status']=='Community follow-up closed':raise ValueError('Journey unavailable')
    if role not in ('CHO','Medical Officer','MS — RH / CHC / SDH'):raise PermissionError('Clinical role required for onward referral')
    if destination not in {f['name'] for f in facilities()}:raise ValueError('Unknown facility')
    if destination==j['destination']:raise ValueError('Select a different destination')
    if not reason.strip():raise ValueError('Reason required')
    with connect() as c:
        t=now();leg=c.execute('INSERT INTO legs(journey_id,source,destination,created_at) VALUES(?,?,?,?)',(jid,j['destination'],destination,t)).lastrowid
        c.execute('INSERT INTO events(journey_id,leg_id,event_type,actor_role,actor_label,facility,details,created_at) VALUES(?,?,?,?,?,?,?,?)',(jid,leg,'Onward referred',role,role,j['destination'],reason,t))
        c.execute('UPDATE journeys SET destination=?,status=? WHERE id=?',(destination,'Onward referred',jid))
        c.execute('INSERT INTO alerts(journey_id,recipient,message,created_at) VALUES(?,?,?,?)',(jid,destination,f'Incoming onward referral REF-{jid:05d}',t))
def update_stock(facility,stock):
    with connect() as c:c.execute('UPDATE facilities SET antivenom_demo=? WHERE name=?',(int(stock),facility))
def seed():
    if journeys():return
    jid=create('DEMO Patient A','Paud','Suspected snakebite','Emergency','ASHA','ASHA Demo Worker','PHC Male','11:30')
    advance(jid,'Notified','ASHA','Facility notified (simulated)')
    advance(jid,'Acknowledged','Medical Officer','Receiving team acknowledged')
    advance(jid,'Transport started','ASHA','Transport departure confirmed (demo)')
    jid2=create('DEMO Patient B','Maan','Suspected leprosy — specialist review','Priority','Medical Officer','ASHA Demo Worker','Rural Hospital Paud','')
    advance(jid2,'Notified','Medical Officer','Referral sent (demo)')
    jid3=create('DEMO Patient C','Pirangut','Maternal follow-up','Routine','ANM','ASHA Demo Worker','PHC Maan','')
    advance(jid3,'Notified','ANM','Referral sent (demo)')
    advance(jid3,'Acknowledged','Medical Officer','Accepted (demo)')
    advance(jid3,'Arrived','ANM','Arrived (demo)')
    advance(jid3,'Feedback recorded','Medical Officer','Synthetic follow-up instructions','Discharged')
