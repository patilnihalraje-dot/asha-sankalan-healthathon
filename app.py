"""ASHA Sankalan 2026 — interactive referral coordination demonstration."""
import html
from datetime import datetime, timezone
import pandas as pd
import streamlit as st
import pilot
from ai.service import ask, summarize, provider, has_api_key

st.set_page_config(page_title='ASHA Sankalan | Version 1 | Real Time Patient Referral Loop System',page_icon='🏥',layout='wide',initial_sidebar_state='expanded')
pilot.init();pilot.seed()

st.markdown('''<style>
.stApp{background:#f3f7fa;color:#143046}.block-container{max-width:1450px;padding-top:1rem}
[data-testid="stSidebar"]{background:#e9f2f5}
.hero{background:linear-gradient(112deg,#073c48,#087c81 70%,#12a5a0);padding:25px 29px;border-radius:19px;color:white;margin-bottom:15px;box-shadow:0 8px 25px #0c555622}
.hero h1{font-size:2rem;margin:0;color:white}.hero p{color:#d6f6f0;margin:7px 0 0}
[data-testid="stMetric"]{border:1px solid #dbe8ee;background:white;padding:13px;border-radius:13px}
.pill{display:inline-block;border-radius:22px;background:#e0f4ed;padding:5px 12px;color:#09644d;font-weight:700;font-size:12px}
.live{display:inline-flex;align-items:center;gap:7px;font-weight:700;color:#097a66}
.dot{width:9px;height:9px;background:#12ad8a;border-radius:50%;animation:pulse 1.6s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 #0ea88377}70%{box-shadow:0 0 0 10px #0ea88300}100%{box-shadow:0 0 0 0 #0ea88300}}
.timeline{border-left:3px solid #b7d8d5;padding:4px 0 4px 18px;margin-left:9px}.event{background:white;border:1px solid #dce9e9;border-radius:11px;padding:10px 14px;margin:8px 0;position:relative}.event:before{content:'';width:12px;height:12px;border-radius:50%;background:#0b8983;position:absolute;left:-27px;top:15px;border:2px solid white}
[data-testid="stButton"] button[kind="primary"]{background:#087c78;border-radius:10px}
</style>''',unsafe_allow_html=True)

with st.sidebar:
    st.markdown('## 🏥 ASHA SANKALAN')
    st.caption('Version 1 · Health-a-thon 2026 · Mulshi Pilot')
    role=st.selectbox('👤 Demo role',pilot.ROLES,index=0)
    st.caption('Role switcher is a demo only, NOT secure authentication.')
    page=st.radio('Explore',['📊 Command Centre','📍 Facility Finder','➕ Create Referral','🚑 Live Journey Tracker','🏛️ Governance','🤖 AI Assistant','🔔 Notifications','📖 Project Guide'])
    st.divider()
    st.caption('🟢 Local SQLite · No paid map API')
    st.caption('🟠 Coordinates approximate · medicine stock SIMULATED')
    st.caption(f'AI: {provider()} · {"configured" if has_api_key() else "offline"}')
    st.warning('SYNTHETIC DATA ONLY. Not for actual clinical referral or emergency dispatch.')

st.markdown('<div class="hero"><h1>ASHA SANKALAN <span style="font-size:16px;font-weight:400">| Real Time Patient Referral Loop System</span></h1><p>The right patient, in the right facility, at the right time.</p></div>',unsafe_allow_html=True)

all_j=pilot.journeys()

def view_map(village,facilities):
    v=next(x for x in pilot.villages() if x['name']==village)
    points=[{'name':'📍 '+village+' (patient origin)','lat':v['lat'],'lon':v['lon'],'kind':'Village'}]
    points += [{'name':f['name'],'lat':f['lat'],'lon':f['lon'],'kind':f['type']} for f in facilities]
    st.map(pd.DataFrame(points),latitude='lat',longitude='lon',size=110,zoom=10)
    st.caption('Approximate demonstration coordinates; map is not a verified routing or ambulance navigation service.')

def status_html(j):
    color='#b45309' if j['priority']=='Emergency' else '#137f76'
    return f'<span style="font-weight:700;color:{color}">{html.escape(j["priority"])}</span> · {html.escape(j["status"])}'

def show_timeline(jid):
    j=pilot.get(jid)
    ev=pilot.events(jid)
    st.markdown(f'### REF-{jid:05d} · {html.escape(j["patient_alias"])}')
    st.markdown(status_html(j),unsafe_allow_html=True)
    st.caption(f"Origin: {j['village']} · Current destination: {j['destination']} · ETA: {j['eta'] or 'Not supplied'} (worker-entered, not GPS)")
    a,b,c=st.columns(3)
    a.metric('Confirmed events',len(ev));b.metric('Referral legs',len(pilot.legs(jid)));c.metric('Current status',j['status'])
    if j['status'] in ('Transport started','Notified','Acknowledged','Onward referred'):
        st.markdown('<div class="live"><span class="dot"></span> ACTIVE REFERRAL · awaiting next confirmed update</div>',unsafe_allow_html=True)
    st.progress(min(len({x['event_type'] for x in ev}.intersection(pilot.EVENTS))/len(pilot.EVENTS),1.0),text='Recorded milestones (not clinical recovery progress)')
    for leg in pilot.legs(jid):st.caption(f"🧭 Leg {leg['id']}: {leg['source']} → {leg['destination']}")
    st.markdown('<div class="timeline">',unsafe_allow_html=True)
    for e in ev:
        label=html.escape(e['event_type']);details=html.escape(e['details'] or '');actor=html.escape(e['actor_role'])
        st.markdown(f'<div class="event"><b>{label}</b> · <small>{html.escape(e["created_at"][:16].replace("T"," "))} UTC</small><br><span style="color:#526675">{actor} · {details}</span></div>',unsafe_allow_html=True)
    st.markdown('</div>',unsafe_allow_html=True)
    st.caption('Timeline timestamps are server-generated; location is not GPS tracked. Refresh for updates from other sessions.')

if page=='📊 Command Centre':
    st.markdown('## Operational overview')
    st.markdown('<div class="live"><span class="dot"></span> DEMO OPERATIONS FEED · refresh to see new events</div>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    a.metric('Total journeys',len(all_j));b.metric('Active',sum(j['status']!='Community follow-up closed' for j in all_j));c.metric('Emergency',sum(j['priority']=='Emergency' for j in all_j));d.metric('Community loops closed',sum(j['status']=='Community follow-up closed' for j in all_j))
    left,right=st.columns([2,1])
    with left:
        st.subheader('Incoming & ongoing referrals')
        st.dataframe(pd.DataFrame([{'Referral':f"REF-{j['id']:05d}",'Patient (demo)':j['patient_alias'],'Village':j['village'],'Priority':j['priority'],'Destination':j['destination'],'Status':j['status']} for j in all_j]),hide_index=True,use_container_width=True)
        if all_j:
            jid=st.selectbox('Quick track referral',[j['id'] for j in all_j],format_func=lambda x:f'REF-{x:05d}',key='overview_select')
            show_timeline(jid)
    with right:
        st.subheader('Status distribution')
        st.bar_chart(pd.Series([j['status'] for j in all_j]).value_counts(),horizontal=True)
        st.subheader('Emergency desk')
        for j in all_j:
            if j['priority']=='Emergency' and j['status']!='Community follow-up closed':
                st.error(f"REF-{j['id']:05d} · {j['village']} → {j['destination']}\n\n{j['status']}")
        st.caption('Alerts are simulated in-app, not SMS, WhatsApp, or ambulance dispatch.')

elif page=='📍 Facility Finder':
    st.header('📍 Mulshi geographical referral pilot')
    st.info('Village and facility names are pilot examples; coordinates are approximate and unverified. All antivenom availability and emergency capability flags are SIMULATED.')
    c1,c2=st.columns([1,2])
    with c1:
        village=st.selectbox('Patient village',[v['name'] for v in pilot.villages()],index=next((i for i,v in enumerate(pilot.villages()) if v['name']=='Paud'),0))
        condition=st.selectbox('Referral scenario',['Suspected snakebite (emergency)','General referral'])
        emergency=condition.startswith('Suspected')
        v=next(x for x in pilot.villages() if x['name']==village)
        st.caption(f"Administratively assigned (demo): {v['assigned_phc']}")
        ranked=pilot.ranked(village,emergency)
        st.markdown('#### Nearby facilities')
        for f in ranked:
            label='🟢 Eligible in simulation' if f['eligible_demo'] else '🔴 Not eligible in simulation'
            st.markdown(f"**{f['name']}** · {f['km']} km straight-line  ")
            st.caption(f"{f['type']} · {label} · Antivenom demo: {'Yes' if f['antivenom_demo'] else 'No'}")
        if emergency:
            eligible=[f for f in ranked if f['eligible_demo']]
            if eligible:st.success(f"First matching simulated facility: {eligible[0]['name']} ({eligible[0]['km']} km straight-line)")
            else:st.error('No matching simulated facility. Emergency clinical coordination required.')
        st.warning('For real snakebite, urgent emergency medical assessment/transport is essential. Antivenom stock alone does not establish facility suitability.')
    with c2:
        view_map(village,ranked)
        chart=pd.DataFrame([{'Facility':f['name'],'Straight-line km':f['km']} for f in sorted(ranked,key=lambda x:x['km'])])
        st.bar_chart(chart.set_index('Facility'))
        st.caption('Distances are straight-line estimates, not driving distances or arrival times.')
    with st.expander('🧪 Simulate changing antivenom availability (demo admin control)'):
        facility=st.selectbox('Facility to update',[f['name'] for f in pilot.facilities()])
        current=next(f for f in pilot.facilities() if f['name']==facility)
        stock=st.toggle('Simulated antivenom available',value=bool(current['antivenom_demo']))
        if st.button('Save simulated stock status'):
            pilot.update_stock(facility,stock);st.success('Updated simulated inventory.');st.rerun()

elif page=='➕ Create Referral':
    st.header('➕ Create multi-level referral')
    st.caption('Authorized clinical decisions remain with qualified staff. Any origin role can be simulated; production permissions require verified login.')
    with st.form('create_referral'):
        a,b=st.columns(2)
        with a:
            name=st.text_input('Synthetic patient alias *',value='DEMO Patient D')
            village=st.selectbox('Village *',[v['name'] for v in pilot.villages()])
            reason=st.selectbox('Reason',['Suspected snakebite','Suspected leprosy','Maternal follow-up','Child health follow-up','Other'])
            if reason=='Other':reason=st.text_input('Reason details')
            priority=st.selectbox('Priority',['Emergency','Priority','Routine'],index=0)
        with b:
            origin=st.selectbox('Referral created by',pilot.ROLES,index=pilot.ROLES.index(role))
            asha=st.text_input('Assigned community follow-up ASHA',value='ASHA Demo Worker')
            ranked=pilot.ranked(village,reason=='Suspected snakebite')
            destination=st.selectbox('Receiving facility *',[f['name'] for f in ranked],format_func=lambda x:x+' · '+str(next(f['km'] for f in ranked if f['name']==x))+' km straight-line')
            eta=st.text_input('Expected arrival (worker-entered; optional)',placeholder='e.g. 14:30, unverified')
        st.caption('Destination list is distance-ranked with simulated capability filtering. Selection does not constitute medical advice.')
        if st.form_submit_button('🚑 Create referral and notify receiving facility',type='primary'):
            try:
                jid=pilot.create(name,village,reason,priority,origin,asha,destination,eta)
                st.success(f'Created REF-{jid:05d}. In-app notification generated for {destination}.')
                st.session_state['last_referral']=jid
            except (ValueError,PermissionError) as e:st.error(str(e))
    if st.session_state.get('last_referral'):show_timeline(st.session_state['last_referral'])

elif page=='🚑 Live Journey Tracker':
    st.header('🚑 Patient journey tracking')
    st.caption('E-commerce-style milestones are driven by recorded events, not fabricated live GPS movement.')
    if all_j:
        jid=st.selectbox('Select referral',[j['id'] for j in all_j],format_func=lambda x:f'REF-{x:05d} · '+pilot.get(x)['patient_alias'])
        show_timeline(jid)
        st.divider()
        with st.container(border=True):
            st.subheader('Record next confirmed event')
            event=st.selectbox('Milestone',pilot.EVENTS[1:])
            allowed=pilot.PERMISSIONS[event]
            st.caption('Permitted demo roles: '+', '.join(allowed))
            details=st.text_area('Event details / feedback',placeholder='Use synthetic information only')
            outcome=st.selectbox('Outcome (for clinical feedback)',['Not recorded','Discharged','Admitted','Transferred','Deceased','Other']) if event=='Feedback recorded' else ''
            if st.button('Record milestone',type='primary'):
                try:pilot.advance(jid,event,role,details,outcome);st.success('Event recorded and timeline updated.');st.rerun()
                except (ValueError,PermissionError) as e:st.error(str(e))
        with st.expander('🔀 Onward referral to another facility'):
            destination=st.selectbox('Next facility',[f['name'] for f in pilot.facilities()])
            reason=st.text_area('Reason for onward referral')
            if st.button('Create linked referral leg'):
                try:pilot.transfer(jid,role,destination,reason);st.rerun()
                except (ValueError,PermissionError) as e:st.error(str(e))
        if st.button('🔄 Refresh tracking data'):st.rerun()

elif page=='🏛️ Governance':
    st.header('🏛️ Supervision and governance')
    st.caption('Seven oversight roles · ANM → CHO → Medical Officer → Block/Taluka Health Officer → MS — RH / CHC / SDH → District Health Officer → Civil Surgeon. These are dashboard perspectives, not necessarily a strict administrative reporting chain.')
    oversight=['ANM','CHO','Medical Officer','Block Health Officer','MS — RH / CHC / SDH','District Health Officer','Civil Surgeon']
    scope=st.selectbox('View supervisory perspective',oversight,index=oversight.index(role) if role in oversight else 0)
    st.info('Pilot dataset covers one demonstration taluka only. District/Civil Surgeon totals are not real district-wide statistics.')
    filtered=all_j
    if scope in ('CHO','Medical Officer','MS — RH / CHC / SDH'):
        facilities_in_scope=[f['name'] for f in pilot.facilities() if (scope!='MS — RH / CHC / SDH' or f['type'] in ('Rural Hospital','CHC','Sub-District Hospital'))]
        fac=st.selectbox('Facility scope',facilities_in_scope)
        filtered=[j for j in all_j if j['destination']==fac or any(l['destination']==fac for l in pilot.legs(j['id']))]
    elif scope=='ANM':
        v=st.selectbox('Village/sub-centre scope',[v['name'] for v in pilot.villages()])
        filtered=[j for j in all_j if j['village']==v]
    a,b,c,d=st.columns(4)
    a.metric('Referrals in scope',len(filtered));b.metric('Pending community closure',sum(j['status']!='Community follow-up closed' for j in filtered));c.metric('Emergency',sum(j['priority']=='Emergency' for j in filtered));d.metric('Feedback recorded',sum(any(e['event_type']=='Feedback recorded' for e in pilot.events(j['id'])) for j in filtered))
    if filtered:
        data=pd.DataFrame([{'Referral':f"REF-{j['id']:05d}",'Village':j['village'],'Destination':j['destination'],'Priority':j['priority'],'Status':j['status'],'Events':len(pilot.events(j['id'])),'Onward legs':len(pilot.legs(j['id']))} for j in filtered])
        st.dataframe(data,hide_index=True,use_container_width=True)
        a,b=st.columns(2)
        with a:st.subheader('By priority');st.bar_chart(data['Priority'].value_counts())
        with b:st.subheader('By status');st.bar_chart(data['Status'].value_counts())
        st.subheader('Overdue / attention queue (demonstration)')
        st.dataframe(data[data['Status']!='Community follow-up closed'],hide_index=True,use_container_width=True)
        st.caption('True overdue detection requires configurable SLA thresholds and validated timestamps. No performance ranking of individual health workers is implied.')

elif page=='🤖 AI Assistant':
    st.header('🤖 Multilingual ASHA knowledge assistant')
    st.caption(f'Provider: {provider()} · API key configured: {has_api_key()} · Offline fallback always available')
    st.warning('Maharashtra Public Health Department source notes are included locally. No live web search is configured. General LLM fallback is unverified; never use it as a clinical protocol.')
    offline=st.toggle('Offline only',value=False)
    q=st.text_input('Ask in English, मराठी, हिंदी',placeholder='आशा सेविकेची प्रमुख कामे कोणती?')
    if st.button('Ask assistant',type='primary') and q:
        with st.spinner('Checking knowledge notes / AI...'):result=ask(q,'offline' if offline else 'auto')
        st.caption('Answer mode: '+result['mode']);st.write(result['answer'])
        for source in result['sources']:
            with st.expander(source['title']+' · '+source['id']):
                st.write(source['text'])
                if source.get('source_url'):st.link_button('Source document',source['source_url'])
    st.divider();st.subheader('📝 Doctor feedback summary (draft only)')
    with st.form('summary'):
        outcome=st.text_area('Synthetic doctor outcome');instructions=st.text_area('Synthetic doctor instructions');follow=st.text_input('Follow-up date')
        if st.form_submit_button('Draft summary'):
            try:
                r=summarize(outcome,instructions,follow,'offline' if offline else 'auto')
                st.caption('Mode: '+r['mode']);st.warning('Unapproved draft; clinician must verify.');st.write(r['summary'])
            except ValueError as e:st.error(str(e))

elif page=='🔔 Notifications':
    st.header('🔔 In-app notifications')
    notifications=pilot.rows('SELECT * FROM alerts ORDER BY id DESC LIMIT 80')
    st.caption('Local simulated notifications. No external SMS, WhatsApp or push notification service connected.')
    for n in notifications:
        st.info(f"{n['created_at'][:16]} UTC · To: {n['recipient']} · {n['message']}")

elif page=='📖 Project Guide':
    st.header('📖 Architecture & workflow')
    st.markdown('''**Seven care levels:** Community/household → grassroots workers (ASHA/AWW/MPW) → Sub-Centre/ANM → PHC/CHO/Medical Officer → CHC → SDH → District Hospital/Medical College. Patients may bypass levels according to clinical protocols; these are not mandatory sequential stops.

**Seven governance perspectives:** ANM, CHO, Medical Officer, Block/Taluka Health Officer, MS — RH / CHC / SDH (Medical Superintendent), District Health Officer, Civil Surgeon. Administrative oversight and clinical authority are distinct.

**Journey model:** One journey ID, multiple onward referral legs, timestamped events, receiving facility notification, clinician feedback, ASHA community closure. Status updates are manual and become visible after refreshing the UI.

**Pilot:** Mulshi, Pune district. Facility/village coordinates are approximate and unverified; antivenom stock is entirely simulated. Distance is Haversine straight-line, not road ETA. No GPS or hospital inventory API is connected.

**Safety:** No real patient data, no production authentication, no confirmed clinical triage, no real-time stock, no ambulance dispatch, and no official endorsement. Real snakebite requires urgent medical assessment and appropriate emergency transport.''')
    st.code('python -m streamlit run app.py\n# To run the original application separately:\npython -m streamlit run legacy_app.py',language='bash')

st.divider();st.caption('ASHA Sankalan · Version 1 · Health-a-thon demonstration · Synthetic records · No clinical deployment or official affiliation')
