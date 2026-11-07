"""Offline lexical retrieval with citation metadata. No model download required."""
import json, math, re
from pathlib import Path
from collections import Counter
BASE=Path(__file__).resolve().parents[1]
STOP={'what','which','when','where','does','the','and','are','for','with','from','how','many','days','please','about','this','that','can','you','tell','me','of','to','in','is','a','an'}
def tokenize(s):
    return [w for w in re.findall(r"[^\W_]+",s.lower(),flags=re.UNICODE) if len(w)>1 and w not in STOP]
def load_documents(path=None):
    path=Path(path or BASE/'knowledge_base'/'official_source_notes.json')
    docs=json.loads(path.read_text(encoding='utf-8'))
    for p in sorted((BASE/'knowledge_base'/'local_docs').glob('*.txt')) if (BASE/'knowledge_base'/'local_docs').exists() else []:
        docs.append({'id':p.stem,'title':p.name,'source_url':'local-file:'+p.name,'section':'User-supplied text','review_status':'unreviewed user upload','text':p.read_text(encoding='utf-8')[:50000]})
    return docs
def retrieve(query,docs=None,k=3):
    docs=docs if docs is not None else load_documents()
    q=Counter(tokenize(query))
    if not q: return []
    corpus=[Counter(tokenize(d['title']+' '+d['section']+' '+d['text'])) for d in docs]
    n=len(corpus)
    ranked=[]
    for d,terms in zip(docs,corpus):
        score=sum((1+math.log(1+terms[w]))*math.log(1+(n+1)/(1+sum(w in c for c in corpus))) for w in q if terms[w])
        if score>0: ranked.append((score,d))
    return [dict(d,score=round(score,3)) for score,d in sorted(ranked,key=lambda x:-x[0])[:k]]
