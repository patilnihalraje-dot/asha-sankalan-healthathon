"""Sarvam/OpenAI optional multilingual assistant; never sends real patient records."""
import os, re
from pathlib import Path
from dotenv import dotenv_values
from .retrieval import retrieve

ROOT = Path(__file__).resolve().parents[1]
def config():
    c=dict(os.environ)
    c.update({k:v for k,v in dotenv_values(ROOT/'.env').items() if v is not None})
    return c

def provider(): return config().get('AI_PROVIDER','sarvam').lower()
def has_api_key():
    c=config(); return bool(c.get('SARVAM_API_KEY') if provider()=='sarvam' else c.get('ASHA_SANKALAN_OPENAI_API_KEY') if provider()=='openai' else False)

def generate(system, prompt, max_tokens=4096):
    from openai import OpenAI
    c=config(); p=provider()
    if p=='sarvam':
        client=OpenAI(api_key=c['SARVAM_API_KEY'],base_url='https://api.sarvam.ai/v1',timeout=90,max_retries=1)
        r=client.chat.completions.create(model=c.get('SARVAM_MODEL','sarvam-105b'),messages=[{'role':'system','content':system},{'role':'user','content':prompt}],max_tokens=max(max_tokens,int(c.get('SARVAM_MAX_TOKENS','4096'))))
        answer=(r.choices[0].message.content or '').strip()
        if r.choices[0].finish_reason=='length' or not answer: raise RuntimeError('Model response empty or truncated; increase token budget')
        return answer
    if p=='openai':
        client=OpenAI(api_key=c['ASHA_SANKALAN_OPENAI_API_KEY'],timeout=60,max_retries=1)
        r=client.responses.create(model=c.get('OPENAI_CHAT_MODEL','gpt-4.1-mini'),instructions=system,input=prompt,max_output_tokens=1100)
        if not r.output_text: raise RuntimeError('Empty model response')
        return r.output_text
    raise RuntimeError('AI_PROVIDER=offline')

def language(q):
    if re.search('[\u0900-\u097f]',q):
        return 'Hindi' if any(w in q for w in ['क्या','कैसे','बताइए','मुझे','नमस्ते']) else 'Marathi'
    return 'Marathi' if any(w in q.lower() for w in ['namaskar','sevike','kay aahe','sanga','balala']) else 'English'

def greeting(q):
    s=re.sub(r'[!?.।,]+','',q.lower()).strip()
    if s in {'hi','hello','hey','good morning','good evening','namaskar','नमस्कार','नमस्ते','शुभ सकाळ','शुभ प्रभात'}:
        return {'Marathi':'नमस्कार! मी आशा संकलन सहाय्यक आहे. आरोग्य कार्यक्रम, संदर्भ सेवा आणि फॉलो-अप याबद्दल विचारा.','Hindi':'नमस्ते! मैं आशा संकलन सहायक हूँ। आप स्वास्थ्य कार्यक्रम और रेफरल के बारे में पूछ सकते हैं।','English':'Hello! I’m the ASHA Sankalan assistant. Ask me about referrals, ASHA programmes, or follow-up.'}[language(q)]
    if s in {'thanks','thank you','धन्यवाद','आभार'}: return {'Marathi':'आपले स्वागत आहे!','Hindi':'आपका स्वागत है!','English':'You’re welcome!'}[language(q)]
    return None

def ask(query,mode='auto'):
    query=(query or '').strip()
    if not query: return {'mode':'offline','answer':'Please enter a question.','sources':[]}
    g=greeting(query)
    if g: return {'mode':'greeting','answer':g,'sources':[]}
    online=mode!='offline' and has_api_key()
    search=query
    if online and language(query)!='English':
        try: search=generate('Translate the question into a short English search query; return only the query, no answer.',query)
        except Exception: pass
    hits=retrieve(search)
    if hits:
        if online:
            context='\n'.join(f"[{d['id']}] {d['title']}: {d['text']}" for d in hits)
            try:
                answer=generate('Answer in the same language as the user. Use ONLY provided source notes for medical facts. Cite their IDs. Never invent clinical protocols, drug doses or sources. Refer clinical decisions to qualified professionals.',f'Question: {query}\nSource notes:\n{context}')
                return {'mode':provider(),'answer':answer,'sources':hits}
            except Exception as e: error=type(e).__name__
        else: error=None
        return {'mode':'offline-fallback' if error else 'offline','answer':('AI unavailable ('+error+').\n' if error else '')+'Source excerpts:\n'+'\n'.join(f"[{d['id']}] {d['text']}" for d in hits),'sources':hits}
    if online:
        try:
            answer=generate('You are a multilingual ASHA programme assistant. Answer in the user language. There are no retrieved documents or live web results. For medical questions clearly say this is unverified general AI knowledge, not an official protocol. Do not invent citations, prescriptions, dosing or patient-specific treatment decisions. Recommend qualified clinical guidance for emergencies.',query)
            return {'mode':provider()+'-general','answer':answer+'\n\n⚠️ No verified local source or live web search supports this response.','sources':[]}
        except Exception as e: return {'mode':'offline','answer':f'No matching source; AI unavailable ({type(e).__name__}).','sources':[]}
    return {'mode':'offline','answer':'No matching local source. Consult verified clinical guidance.','sources':[]}

def summarize(outcome,instructions,followup_date,mode='auto'):
    if not outcome.strip() or not instructions.strip(): raise ValueError('Both doctor fields required')
    original={'outcome':outcome,'instructions':instructions,'followup_date':followup_date}
    fallback=f'Doctor outcome: {outcome}\nInstructions: {instructions}\nFollow-up: {followup_date or "Not specified"}'
    if mode=='offline' or not has_api_key(): return {'mode':'offline','summary':fallback,'original':original}
    try:
        text=generate('Summarize clinician-written synthetic feedback for ASHA workers. Preserve all details, dates, uncertainty and instructions exactly. Do not invent treatment or clinical advice. Mark as draft requiring clinician approval.',fallback)
        return {'mode':provider(),'summary':text,'original':original}
    except Exception as e: return {'mode':'offline-fallback','summary':fallback,'original':original,'error':type(e).__name__}
