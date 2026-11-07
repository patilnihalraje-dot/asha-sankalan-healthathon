import json
from datetime import datetime,timezone
import db

def init_extra():
    with db.connect() as conn:
        conn.executescript('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT, recipient_id INTEGER NOT NULL REFERENCES users(id),
            referral_id INTEGER REFERENCES referrals(id), message TEXT NOT NULL,
            created_at TEXT NOT NULL, read_at TEXT);
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,title_en TEXT NOT NULL,title_mr TEXT,title_hi TEXT,
            body_en TEXT NOT NULL,source TEXT NOT NULL,source_url TEXT,posted_at TEXT NOT NULL,
            verified INTEGER NOT NULL DEFAULT 0);
        ''')
        conn.execute('''INSERT INTO notices(title_en,title_mr,title_hi,body_en,source,source_url,posted_at,verified)
          SELECT ?,?,?,?,?,?,?,? WHERE NOT EXISTS (SELECT 1 FROM notices)''',(
          'Demo notice: referral follow-up checklist','नमुना सूचना: रेफरल पाठपुरावा यादी','डेमो सूचना: रेफरल फॉलो-अप सूची',
          'Training-only notice. Verify the referral ID, confirm facility feedback, and document follow-up. Not official medical guidance.',
          'ASHA Sankalan demo team',None,datetime.now(timezone.utc).isoformat(),0))

def notify(user_id,referral_id,message):
    with db.connect() as conn:
        conn.execute('INSERT INTO notifications(recipient_id,referral_id,message,created_at) VALUES(?,?,?,?)',
                     (user_id,referral_id,message,db.now()))

def notifications(user_id):
    with db.connect() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM notifications WHERE recipient_id=? ORDER BY id DESC',(user_id,))]

def mark_read(user_id,notification_id):
    with db.connect() as conn:
        conn.execute('UPDATE notifications SET read_at=? WHERE id=? AND recipient_id=?',(db.now(),notification_id,user_id))

def notices():
    with db.connect() as conn:
        return [dict(r) for r in conn.execute('SELECT * FROM notices ORDER BY id DESC')]

def search(rows,term,status):
    term=term.strip().lower()
    return [r for r in rows if (not status or r['status']==status) and
        (not term or any(term in str(r.get(k,'')).lower() for k in ('id','patient_name','village','reason','target_facility')) or term.replace('asha-','').lstrip('0')==str(r['id']))]

def safe_draft(obj):
    allowed=('name','age','sex','village','reason','urgency','target')
    if not isinstance(obj,dict): raise ValueError('Invalid draft')
    result={k:obj[k] for k in allowed if k in obj and isinstance(obj[k],(str,int))}
    if len(json.dumps(result))>12000: raise ValueError('Draft too large')
    return result
