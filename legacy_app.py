import json
from datetime import date
import streamlit as st
import pandas as pd
import db,extra
from dotenv import load_dotenv
load_dotenv()
from ai.service import ask, summarize, has_api_key
from i18n import LANGUAGES,tr

st.set_page_config(page_title='ASHA Sankalan | Digital Referral Portal',page_icon='🏥',layout='wide',initial_sidebar_state='expanded')
db.initialize(); extra.init_extra()
if 'language' not in st.session_state: st.session_state.language='mr'
if 'draft' not in st.session_state: st.session_state.draft={}

with st.sidebar:
    st.markdown('### 🏥 ASHA SANKALAN')
    st.caption('Digital Referral & Continuity of Care')
    language_label=st.selectbox('🌐 Language / भाषा',list(LANGUAGES),index=list(LANGUAGES.values()).index(st.session_state.language))
    st.session_state.language=LANGUAGES[language_label]
    L=st.session_state.language
    t=lambda k:tr(L,k)
    accounts=db.users()
    user=st.selectbox(t('logout'),accounts,format_func=lambda u:f"{u['display_name']} · {t(u['role'])}")
    st.caption(f"🏥 {user['facility']}")
    large=st.toggle(t('large'),value=False)
    contrast=st.toggle(t('contrast'),value=False)
    pages=[t('home')] + ([t('new')] if user['role']=='asha' else []) + [t('referrals'),'🤖 AI Knowledge Assistant',t('alerts'),t('notices'),t('help')]
    page=st.radio('Navigation',pages,label_visibility='collapsed')
    st.divider()
    st.caption('RESEARCH DEMONSTRATION · SYNTHETIC DATA ONLY')
    st.caption('Demo account switcher is not authentication.')

bg='#0d2329' if contrast else '#f5f8fb'
fg='#ffffff' if contrast else '#17324a'
card='#172f39' if contrast else '#ffffff'
st.markdown(f'''<style>
.stApp {{background:{bg};color:{fg};}}
.block-container {{padding-top:1.2rem;max-width:1380px;}}
[data-testid="stSidebar"] {{background:{'#09252c' if contrast else '#edf4f6'};}}
[data-testid="stMetric"] {{background:{card};border:1px solid {'#62858d' if contrast else '#dbe7eb'};border-radius:14px;padding:16px;}}
.stButton button[kind="primary"],button[data-testid="stBaseButton-primary"] {{background:#126b69;border-radius:9px;}}
h1,h2,h3 {{letter-spacing:-.025em;}}
.stApp p,.stApp label {{font-size:{'1.13rem' if large else '1rem'};}}
.portal-header {{padding:20px 24px;background:linear-gradient(100deg,#126b69,#235a7a);color:white;border-radius:15px;margin-bottom:15px;}}
.portal-header h2 {{color:white;margin:0;}}
.portal-header p {{color:#e3f4f0;margin:6px 0 0;}}
.portal-note {{padding:12px 16px;border-left:4px solid #c78b36;background:{card};border-radius:8px;margin:12px 0;}}
</style>''',unsafe_allow_html=True)
st.markdown('<div class="portal-header"><h2>🏥 ASHA SANKALAN</h2><p>Digital Referral & Continuity of Care · Research Prototype</p></div>',unsafe_allow_html=True)
st.warning('TRAINING DEMO ONLY · Use synthetic patients. No clinical diagnosis, automatic triage, official affiliation, or production login.')

all_rows=db.referrals(user)
unread=[n for n in extra.notifications(user['id']) if not n['read_at']]

def list_referrals(rows):
    query=st.text_input(t('search'),key='referral_search')
    states=['All','Created','Accepted','Feedback Provided','Closed']
    state=st.selectbox(t('filter'),states,format_func=lambda x:t('all') if x=='All' else x)
    filtered=extra.search(rows,query,None if state=='All' else state)
    if not filtered: st.info(t('noresults'))
    for r in filtered:
        rid=r['id']
        with st.expander(f"ASHA-{rid:05d}  |  {r['patient_name']}  |  {r['status']}",expanded=r['status'] in ('Created','Accepted','Feedback Provided')):
            st.write(f"**{t('village')}:** {r['village']} · **{t('destination')}:** {r['target_facility']} · **{t('priority')}:** {r['urgency']}")
            st.write(f"**{t('reason')}:** {r['reason']}")
            feedback,followup,events=db.detail(user,rid)
            if user['role']=='doctor' and r['status']=='Created':
                if st.button(t('accept'),key=f'accept_{rid}',type='primary'):
                    try:
                        db.accept_referral(user,rid)
                        extra.notify(r['created_by'],rid,f'Referral ASHA-{rid:05d} accepted at PHC')
                        st.rerun()
                    except (ValueError,PermissionError) as e: st.error(str(e))
            if user['role']=='doctor' and r['status']=='Accepted':
                with st.form(f'feedback_{rid}'):
                    outcome=st.text_area(t('outcome'))
                    instructions=st.text_area(t('instructions'))
                    followup_date=st.date_input(t('date'),date.today())
                    if st.form_submit_button(t('send'),type='primary'):
                        try:
                            db.provide_feedback(user,rid,outcome,instructions,followup_date.isoformat())
                            extra.notify(r['created_by'],rid,f'Doctor feedback available for ASHA-{rid:05d}')
                            st.rerun()
                        except (ValueError,PermissionError) as e: st.error(str(e))
            if feedback:
                st.success(t('feedback'))
                st.write(f"**{t('outcome')}:** {feedback['outcome']}")
                st.write(f"**{t('instructions')}:** {feedback['instructions']}")
                st.write(f"**{t('date')}:** {feedback['followup_date'] or '—'}")
            if user['role']=='asha' and r['status']=='Feedback Provided':
                with st.form(f'close_{rid}'):
                    notes=st.text_area(t('followup'))
                    if st.form_submit_button(t('close'),type='primary'):
                        try:
                            db.close_referral(user,rid,notes)
                            for u in db.users():
                                if u['role']=='supervisor': extra.notify(u['id'],rid,f'ASHA-{rid:05d} closed after community follow-up')
                            st.rerun()
                        except (ValueError,PermissionError) as e: st.error(str(e))
            if followup: st.info(f"{t('followup')}: {followup['notes']}")
            st.markdown(f"**{t('timeline')}**")
            for e in events:
                st.markdown(f"- **{e['event_type']}** · {e['created_at'][:16].replace('T',' ')} UTC · {e['display_name']} — {e['detail']}")

def alerts_panel():
    st.subheader(f"🔔 {t('alerts')} ({len(unread)})")
    notices=extra.notifications(user['id'])
    if not notices: st.info('No notifications yet. Notifications appear when referrals change state.')
    for n in notices[:30]:
        c1,c2=st.columns([5,1])
        c1.write(('🔵 ' if not n['read_at'] else '✓ ')+n['message'])
        c1.caption(n['created_at'][:16].replace('T',' ')+' UTC')
        if not n['read_at'] and c2.button(t('read'),key=f"read_{n['id']}"):
            extra.mark_read(user['id'],n['id']);st.rerun()

if page==t('home'):
    st.title(f"{t('welcome')}, {user['display_name']}!")
    total=len(all_rows);closed=sum(r['status']=='Closed' for r in all_rows)
    a,b,c,d=st.columns(4)
    a.metric(t('total'),total);b.metric(t('closed'),closed)
    c.metric(t('pending'),sum(r['status'] in ('Created','Accepted') for r in all_rows))
    d.metric(t('rate'),f'{closed/total:.0%}' if total else '—')
    c1,c2=st.columns([2,1])
    with c1:
        st.subheader(t('referrals'))
        if all_rows:
            st.dataframe(pd.DataFrame(all_rows)[['id','patient_name','village','target_facility','status','created_at']],hide_index=True,use_container_width=True)
        else: st.info('No referrals yet. Create a synthetic referral to begin.')
    with c2:
        st.subheader(f"🔔 {t('alerts')}")
        for n in unread[:4]: st.info(n['message'])
        if not unread: st.success('No unread notifications')
        st.subheader(t('news'))
        for n in extra.notices()[:2]:
            st.write('📢 '+(n.get('title_'+L) or n['title_en']))
            st.caption(n['source']+' · '+('Verified' if n['verified'] else 'Demo / unverified'))

elif page==t('new') and user['role']=='asha':
    st.title('➕ '+t('create'))
    st.caption('Only synthetic data. Save your form draft to a file if you need to continue later.')
    uploaded=st.file_uploader(t('import')+' (JSON)',type=['json'])
    if uploaded and st.button('Load draft into form'):
        try:
            st.session_state.draft=extra.safe_draft(json.load(uploaded))
            for key,value in st.session_state.draft.items(): st.session_state['field_'+key]=value
            st.rerun()
        except (ValueError,UnicodeDecodeError,json.JSONDecodeError) as e: st.error(str(e))
    draft=st.session_state.draft
    c1,c2=st.columns(2)
    with c1:
        name=st.text_input(t('patient')+' *',value=draft.get('name',''),key='field_name')
        age=st.number_input(t('age'),min_value=0,max_value=120,value=int(draft.get('age',35)),key='field_age')
        sex=st.selectbox(t('sex'),['Female','Male','Other'],index=['Female','Male','Other'].index(draft.get('sex','Female')),key='field_sex')
    with c2:
        village=st.text_input(t('village')+' *',value=draft.get('village',''),key='field_village')
        target=st.selectbox(t('destination'),['Demo PHC'],key='field_target')
        urgency=st.selectbox(t('priority'),['Routine','Priority'],key='field_urgency')
    reason=st.text_area(t('reason')+' *',value=draft.get('reason',''),key='field_reason')
    values={'name':name,'age':int(age),'sex':sex,'village':village,'target':target,'urgency':urgency,'reason':reason}
    col1,col2=st.columns([1,1])
    col1.download_button('⬇ '+t('export'),data=json.dumps(values,ensure_ascii=False,indent=2),file_name='asha_demo_draft.json',mime='application/json')
    if col2.button(t('submit'),type='primary',use_container_width=True):
        try:
            rid=db.create_referral(user,name,int(age),sex,village,reason,urgency,target)
            for u in db.users():
                if u['role']=='doctor' and u['facility']==target: extra.notify(u['id'],rid,f'New referral ASHA-{rid:05d} requires review')
            st.session_state.draft={}
            st.success(f'Referral ASHA-{rid:05d} created successfully')
        except (ValueError,PermissionError) as e: st.error(str(e))
    st.divider()
    st.subheader('🎙 '+t('voice'))
    st.caption('Audio capture only: no transcription, translation, or medical interpretation. Audio is not automatically attached to patient records.')
    audio=st.audio_input('Record a synthetic voice note')
    if audio: st.download_button(t('saveaudio'),audio.getvalue(),file_name='demo_voice_note.wav',mime='audio/wav')
    st.info('Offline limitation: export/import allows manual draft transfer. It does not enable form editing while this web app is disconnected, nor does it auto-sync.')

elif page==t('referrals'):
    st.title('📋 '+t('referrals'))
    list_referrals(all_rows)
elif page=='🤖 AI Knowledge Assistant':
    st.title('🤖 AI Knowledge Assistant / माहिती सहाय्यक')
    st.info('Research prototype. Source notes are short summaries of official public materials, not a substitute for clinical protocols. Never enter real patient data.')
    ai_mode=st.radio('Answer mode',['Auto (OpenAI when configured)','Offline only'],horizontal=True)
    st.caption('OpenAI API configured: '+('Yes' if has_api_key() else 'No — offline source retrieval works'))
    q=st.text_input('Ask about ASHA programmes or home-visit schedules',placeholder='Which days are HBNC home visits scheduled after institutional delivery?')
    if st.button('Find answer',type='primary') and q.strip():
        with st.spinner('Searching source notes...'):
            result=ask(q,mode='offline' if ai_mode.startswith('Offline') else 'auto')
        st.caption('Answer mode: '+result['mode'])
        st.write(result['answer'])
        st.subheader('Source references')
        for source in result['sources']:
            with st.expander(source['id']+' · '+source['title']):
                st.write(source['text'])
                st.caption(source['review_status']+' · '+source['section'])
                if source['source_url'].startswith('https:'): st.link_button('Open official source',source['source_url'])
    st.divider()
    st.subheader('📝 AI feedback summarization — draft preview')
    st.caption('Use synthetic doctor-authored feedback only. The original is preserved. Do not use the draft until a clinician reviews it.')
    with st.form('summary_preview'):
        outcome=st.text_area('Doctor outcome (synthetic)')
        instructions=st.text_area('Doctor follow-up instructions (synthetic)')
        follow_date=st.text_input('Follow-up date (as recorded by doctor)')
        submit_summary=st.form_submit_button('Generate summary draft')
    if submit_summary:
        try:
            result=summarize(outcome,instructions,follow_date,mode='offline' if ai_mode.startswith('Offline') else 'auto')
            st.caption('Summary mode: '+result['mode'])
            st.warning('UNAPPROVED DRAFT — check against original doctor feedback')
            st.write(result['summary'])
            with st.expander('Original doctor feedback (unaltered)'): st.json(result['original'])
        except ValueError as exc: st.error(str(exc))

elif page==t('alerts'):
    alerts_panel()
elif page==t('notices'):
    st.title('📢 '+t('notices'))
    st.caption('Notices are stored in the portal database. No external government news feed is connected.')
    for n in extra.notices():
        with st.container(border=True):
            st.subheader(n.get('title_'+L) or n['title_en'])
            st.write(n['body_en'])
            st.caption(f"Source: {n['source']} · {n['posted_at'][:10]} · {'Verified' if n['verified'] else 'Demo / not independently verified'}")
            if n['source_url']: st.link_button('Source',n['source_url'])
elif page==t('help'):
    st.title('♿ '+t('help'))
    st.write('Use the language selector and accessibility toggles in the sidebar. Required fields are marked with *.')
    st.write('Workflow: ASHA creates referral → PHC doctor accepts → doctor records feedback → ASHA closes follow-up.')
    st.write('Voice notes are recordings only. Exported draft JSON files are unencrypted and should contain synthetic data only.')
    st.write('Security: role switching is for demonstrations only; there is no secure login or patient consent management.')
    st.write('Accessibility is partially supported; a full WCAG/GIGW accessibility audit has not been performed.')

st.divider()
st.caption('ASHA Sankalan v2 · Independent research prototype · Not affiliated with or endorsed by Government of India · No real patient data')
