"""Version 1 requested change regression tests."""
from pathlib import Path
import pilot
from ai.retrieval import retrieve,load_documents


def test_ms_role_and_hospital_actions():
    ms='MS — RH / CHC / SDH'
    assert pilot.ROLES.index('Block Health Officer') < pilot.ROLES.index(ms) < pilot.ROLES.index('District Health Officer')
    for action in ('Acknowledged','Arrived','Care started','Feedback recorded'):
        assert ms in pilot.PERMISSIONS[action]


def test_official_source_search():
    documents=load_documents()
    ids={x['id'] for x in documents}
    assert {'MAH-CPHC-2025-01','MAH-CPHC-2025-02','MAH-CPHC-2025-03','MAH-ASHA-2025-01','MAH-ASHA-2025-02'} <= ids
    results=retrieve('Community Health Officer ANM MPW ASHA sub-centre primary care team')
    assert any(x['id']=='MAH-CPHC-2025-02' for x in results)
    assert all('source_url' in x for x in results)


def test_version_and_branding():
    root=Path(__file__).resolve().parents[1]
    assert (root/'VERSION').read_text().strip()=='1.0.0'
    text=(root/'app.py').read_text()
    assert 'Real Time Patient Referral Loop System' in text
    assert 'The right patient, in the right facility, at the right time.' in text
    assert 'MS — RH / CHC / SDH' in text
