from ai.retrieval import load_documents,retrieve
from ai.service import ask,summarize

def test_offline_answer():
    result=ask('HBNC newborn home visits days after institutional delivery',mode='offline')
    assert result['sources']
    assert 'NHM-HBNC-01' in result['answer']

def test_unrelated_query_abstains():
    result=ask('quantum rocket interstellar mechanics',mode='offline')
    assert not result['sources']

def test_offline_summary_preserves_original():
    result=summarize('Attended PHC','Contact on follow-up','2026-11-09',mode='offline')
    assert result['original']['instructions']=='Contact on follow-up'
    assert '2026-11-09' in result['summary']
