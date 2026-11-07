import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import os

DB_PATH = os.environ.get('ASHA_DB_PATH', str(Path(__file__).parent / 'asha_demo.db'))

def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    conn.execute('PRAGMA busy_timeout=15000')
    return conn

def initialize():
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('asha','doctor','supervisor')),
            facility TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, age INTEGER NOT NULL CHECK(age BETWEEN 0 AND 120),
            sex TEXT NOT NULL CHECK(sex IN ('Female','Male','Other')),
            village TEXT NOT NULL, created_by INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL REFERENCES patients(id),
            created_by INTEGER NOT NULL REFERENCES users(id),
            source_facility TEXT NOT NULL, target_facility TEXT NOT NULL,
            reason TEXT NOT NULL, urgency TEXT NOT NULL CHECK(urgency IN ('Routine','Priority')),
            status TEXT NOT NULL CHECK(status IN ('Created','Accepted','Feedback Provided','Closed')),
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id INTEGER NOT NULL UNIQUE REFERENCES referrals(id),
            doctor_id INTEGER NOT NULL REFERENCES users(id),
            outcome TEXT NOT NULL, instructions TEXT NOT NULL,
            followup_date TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS followups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id INTEGER NOT NULL UNIQUE REFERENCES referrals(id),
            asha_id INTEGER NOT NULL REFERENCES users(id),
            notes TEXT NOT NULL, completed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referral_id INTEGER NOT NULL REFERENCES referrals(id),
            actor_id INTEGER NOT NULL REFERENCES users(id),
            event_type TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
        );
        ''')
        db.executemany('INSERT OR IGNORE INTO users(id,username,display_name,role,facility) VALUES(?,?,?,?,?)', [
            (1,'asha_demo','Asha Patil','asha','Village Health Post'),
            (2,'doctor_demo','Dr. Meera Shah','doctor','Demo PHC'),
            (3,'supervisor_demo','District Supervisor','supervisor','District Office')
        ])

def users():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM users ORDER BY id')]

def referrals(user):
    query = '''SELECT r.*, p.name AS patient_name, p.age, p.sex, p.village,
        u.display_name AS creator_name FROM referrals r
        JOIN patients p ON p.id=r.patient_id JOIN users u ON u.id=r.created_by'''
    params=[]
    if user['role']=='asha':
        query+=' WHERE r.created_by=?'; params=[user['id']]
    elif user['role']=='doctor':
        query+=' WHERE r.target_facility=?'; params=[user['facility']]
    query+=' ORDER BY r.id DESC'
    with connect() as db:
        return [dict(r) for r in db.execute(query,params)]

def get_referral(db, rid):
    row=db.execute('SELECT * FROM referrals WHERE id=?',(rid,)).fetchone()
    if not row: raise ValueError('Referral not found')
    return row

def create_referral(user, name, age, sex, village, reason, urgency, target):
    if user['role']!='asha': raise PermissionError('Only ASHA workers can create referrals')
    if not all([name.strip(),village.strip(),reason.strip(),target.strip()]): raise ValueError('Complete all required fields')
    if not 0<=age<=120: raise ValueError('Invalid age')
    with connect() as db:
        cur=db.execute('INSERT INTO patients(name,age,sex,village,created_by,created_at) VALUES(?,?,?,?,?,?)',
                       (name.strip(),age,sex,village.strip(),user['id'],now()))
        patient_id=cur.lastrowid
        cur=db.execute('''INSERT INTO referrals(patient_id,created_by,source_facility,target_facility,reason,urgency,status,created_at,updated_at)
                          VALUES(?,?,?,?,?,?,?,?,?)''',(patient_id,user['id'],user['facility'],target,reason.strip(),urgency,'Created',now(),now()))
        rid=cur.lastrowid
        db.execute('INSERT INTO events(referral_id,actor_id,event_type,detail,created_at) VALUES(?,?,?,?,?)',(rid,user['id'],'Created','Referral created',now()))
        return rid

def accept_referral(user,rid):
    if user['role']!='doctor': raise PermissionError('Doctor role required')
    with connect() as db:
        r=get_referral(db,rid)
        if r['target_facility']!=user['facility']: raise PermissionError('Not assigned to your facility')
        if r['status']!='Created': raise ValueError('Referral must be Created')
        db.execute("UPDATE referrals SET status='Accepted',updated_at=? WHERE id=?",(now(),rid))
        db.execute('INSERT INTO events(referral_id,actor_id,event_type,detail,created_at) VALUES(?,?,?,?,?)',(rid,user['id'],'Accepted','Referral accepted at facility',now()))

def provide_feedback(user,rid,outcome,instructions,followup_date):
    if user['role']!='doctor': raise PermissionError('Doctor role required')
    if not outcome.strip() or not instructions.strip(): raise ValueError('Outcome and instructions required')
    with connect() as db:
        r=get_referral(db,rid)
        if r['target_facility']!=user['facility']: raise PermissionError('Not assigned to your facility')
        if r['status']!='Accepted': raise ValueError('Referral must be Accepted')
        db.execute('INSERT INTO feedback(referral_id,doctor_id,outcome,instructions,followup_date,created_at) VALUES(?,?,?,?,?,?)',
                   (rid,user['id'],outcome.strip(),instructions.strip(),followup_date,now()))
        db.execute("UPDATE referrals SET status='Feedback Provided',updated_at=? WHERE id=?",(now(),rid))
        db.execute('INSERT INTO events(referral_id,actor_id,event_type,detail,created_at) VALUES(?,?,?,?,?)',(rid,user['id'],'Feedback Provided','Doctor feedback recorded',now()))

def close_referral(user,rid,notes):
    if user['role']!='asha': raise PermissionError('ASHA role required')
    if not notes.strip(): raise ValueError('Follow-up notes required')
    with connect() as db:
        r=get_referral(db,rid)
        if r['created_by']!=user['id']: raise PermissionError('Not your referral')
        if r['status']!='Feedback Provided': raise ValueError('Doctor feedback required before closure')
        db.execute('INSERT INTO followups(referral_id,asha_id,notes,completed_at) VALUES(?,?,?,?)',(rid,user['id'],notes.strip(),now()))
        db.execute("UPDATE referrals SET status='Closed',updated_at=? WHERE id=?",(now(),rid))
        db.execute('INSERT INTO events(referral_id,actor_id,event_type,detail,created_at) VALUES(?,?,?,?,?)',(rid,user['id'],'Closed','Community follow-up completed',now()))

def detail(user,rid):
    with connect() as db:
        r=get_referral(db,rid)
        if user['role']=='asha' and r['created_by']!=user['id']: raise PermissionError('Not your referral')
        if user['role']=='doctor' and r['target_facility']!=user['facility']: raise PermissionError('Not your facility')
        feedback=db.execute('SELECT * FROM feedback WHERE referral_id=?',(rid,)).fetchone()
        followup=db.execute('SELECT * FROM followups WHERE referral_id=?',(rid,)).fetchone()
        events=db.execute('''SELECT e.event_type,e.detail,e.created_at,u.display_name FROM events e
            JOIN users u ON u.id=e.actor_id WHERE e.referral_id=? ORDER BY e.id''',(rid,)).fetchall()
        return (dict(feedback) if feedback else None,dict(followup) if followup else None,[dict(e) for e in events])
