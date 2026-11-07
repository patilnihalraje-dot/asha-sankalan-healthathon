import os,sys,tempfile,json
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
import db,extra
from i18n import tr

def test_v2_extensions():
    old=db.DB_PATH
    with tempfile.TemporaryDirectory() as tmp:
        db.DB_PATH=os.path.join(tmp,'test.db')
        try:
            db.initialize();extra.init_extra()
            asha,doctor,supervisor=db.users()
            rid=db.create_referral(asha,'Test Patient',29,'Female','Demo Village','Routine review','Routine','Demo PHC')
            extra.notify(doctor['id'],rid,'New referral')
            assert len(extra.notifications(doctor['id']))==1
            nid=extra.notifications(doctor['id'])[0]['id']
            extra.mark_read(doctor['id'],nid)
            assert extra.notifications(doctor['id'])[0]['read_at']
            assert len(extra.search(db.referrals(asha),'ASHA-00001',None))==1
            assert len(extra.search(db.referrals(asha),'demo village','Created'))==1
            assert len(extra.notices())==1
            assert tr('mr','new')=='नवीन रेफरल'
            assert extra.safe_draft({'name':'Demo','unused':False})=={'name':'Demo'}
            db.accept_referral(doctor,rid)
            db.provide_feedback(doctor,rid,'Reviewed','Contact patient','2026-11-09')
            db.close_referral(asha,rid,'Contacted')
            assert db.referrals(asha)[0]['status']=='Closed'
        finally: db.DB_PATH=old
