import os
import tempfile
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import db

class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        db.DB_PATH=os.path.join(self.temp.name,'test.db')
        db.initialize()
        self.asha,self.doctor,self.supervisor=db.users()
    def tearDown(self): self.temp.cleanup()
    def test_closed_loop_and_permissions(self):
        rid=db.create_referral(self.asha,'Test Patient',32,'Female','Demo Village','Review requested','Routine','Demo PHC')
        self.assertEqual(db.referrals(self.asha)[0]['status'],'Created')
        with self.assertRaises(ValueError): db.close_referral(self.asha,rid,'Premature')
        with self.assertRaises(PermissionError): db.accept_referral(self.asha,rid)
        db.accept_referral(self.doctor,rid)
        db.provide_feedback(self.doctor,rid,'Assessed','Follow up in one week','2026-11-14')
        feedback,_,events=db.detail(self.asha,rid)
        self.assertEqual(feedback['outcome'],'Assessed')
        db.close_referral(self.asha,rid,'Follow-up done')
        self.assertEqual(db.referrals(self.supervisor)[0]['status'],'Closed')
        self.assertEqual(len(db.detail(self.supervisor,rid)[2]),4)
        with self.assertRaises(ValueError): db.close_referral(self.asha,rid,'Duplicate')

if __name__=='__main__': unittest.main()
