import os, tempfile
from pathlib import Path
import pilot

def setup_function():
    pilot.DB=Path(tempfile.mkdtemp())/'test.db'
    pilot.init()

def test_directory_and_distance():
    assert len(pilot.villages())>=5
    assert len(pilot.facilities())>=5
    assert pilot.distance(18.5,73.6,18.5,73.6)==0
    assert pilot.ranked('Paud',True)[0]['eligible_demo']

def test_journey_and_closure():
    jid=pilot.create('DEMO A','Paud','Snakebite','Emergency','ASHA','Asha Demo','PHC Male','12:00')
    assert pilot.get(jid)['status']=='Created'
    pilot.advance(jid,'Acknowledged','Medical Officer')
    pilot.advance(jid,'Feedback recorded','Medical Officer','Synthetic discharge instructions','Discharged')
    pilot.advance(jid,'Community follow-up closed','ASHA','Community follow-up complete')
    assert pilot.get(jid)['status']=='Community follow-up closed'

def test_unauthorized_and_missing_feedback():
    jid=pilot.create('DEMO B','Maan','Other','Routine','ANM','Asha Demo','PHC Maan','')
    try:pilot.advance(jid,'Community follow-up closed','ASHA','No feedback')
    except ValueError:pass
    else:raise AssertionError('Closure must require feedback')
    try:pilot.advance(jid,'Acknowledged','ASHA')
    except PermissionError:pass
    else:raise AssertionError('ASHA must not acknowledge as clinician')

def test_onward_leg():
    jid=pilot.create('DEMO C','Mutha','Other','Priority','Medical Officer','Asha Demo','PHC Mutha','')
    pilot.transfer(jid,'Medical Officer','Rural Hospital Paud','Needs specialist care')
    assert len(pilot.legs(jid))==2
    assert pilot.get(jid)['destination']=='Rural Hospital Paud'

def test_stock_toggle():
    pilot.update_stock('PHC Maan',True)
    assert next(f for f in pilot.facilities() if f['name']=='PHC Maan')['antivenom_demo']==1
