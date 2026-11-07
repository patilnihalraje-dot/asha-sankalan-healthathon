# ASHA Sankalan — Version 1

## Real Time Patient Referral Loop System

**The right patient, in the right facility, at the right time.**

Health-a-thon 2026 research demonstration. **All records and inventory values are synthetic.** No real clinical referral, emergency dispatch, medicine stock, GPS, government endorsement or secure production login is provided.

## Quick start (macOS/Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Optional: add sponsored Sarvam API key to .env
python -m streamlit run app.py
```

Windows: `.venv\\Scripts\\activate` instead of `source`.

For the original referral application (preserved unchanged): `python -m streamlit run legacy_app.py`. It uses a separate SQLite file `asha_demo.db` from the new `pilot_demo.db`. Both applications are independent demos; they do **not** synchronize data.

## Features

- Seven-level care hierarchy, nonsequential clinical referrals, grassroots and facility entry points
- Mulshi taluka demonstration village directory, facility directory, approximate coordinates, local distance calculations, map and chart
- Simulated antivenom availability and facility capability; comparison across PHC catchment areas
- Unique referral journey, onward transfer legs, event audit trail, manual arrival/feedback updates, receiving facility in-app alerts
- ASHA-only community-loop closure after feedback; simulated role permissions on event actions
- Governance dashboard: ANM, CHO, Medical Officer, Block/Taluka Health Officer, **MS — RH / CHC / SDH (Medical Superintendent)**, District Health Officer, Civil Surgeon. The MS role is also available in the sidebar Demo role selector, with simulated facility-level referral updates and onward-referral permissions.
- Sarvam or OpenAI knowledge assistant, Marathi/Hindi/English greeting and translation, local RAG including verified-source summaries of Maharashtra Public Health Department **Arogyam Paramam Dhanam** and **ASHA programme**, unverified general LLM fallback, feedback summary draft
- Original application remains available as `legacy_app.py` (including its older workflows)

## Data and limitations

The names of facilities are pilot examples, and their **coordinates are approximate, not independently geocoded**. The district hospital is a fictional demonstration placeholder. **All medicine availability flags and emergency capability flags are invented** and must never guide real treatment. No actual road ETA or real-time ambulance tracking is computed. Map background may require internet access and is subject to its provider's usage policies. Use only synthetic patient aliases.

The MS role is limited to RH/CHC/SDH facilities in the governance display; the pilot has one demonstration Rural Hospital and no confirmed CHC/SDH inventory. This is UI/demo scope only, not real facility authorization.

The UI has a role switcher for demonstration, not secure authentication or enforcement of geographic permissions. Event operations have basic role checks in `pilot.py`, but do not establish real-world actor identity. Do not deploy with personal health data. Production requires authentication, consent, audit integrity, facility validation, clinical protocols, secure hosting, notification delivery, data governance, and clinician-led safety review.

The original app's database is **not migrated** into the new demo; this prevents inadvertent exposure and avoids changing existing patient records. Use `legacy_app.py` to access the original demo.

## Optional Sarvam AI

`.env` uses `AI_PROVIDER=sarvam`, `SARVAM_API_KEY=...`, `SARVAM_MODEL=sarvam-105b`, `SARVAM_MAX_TOKENS=4096`. Unlike your company-wide `OPENAI_API_KEY`, the project reads its own `.env` key explicitly. For no external API usage, set `AI_PROVIDER=offline`. RAG uses the included short source notes; no web search is enabled.

## Tests

`python -m pytest -q tests/test_pilot.py`

## Directory

- `app.py`: interactive command centre
- `pilot.py`: synthetic geography, SQLite events, permissions and simulated resources
- `ai/service.py`: Sarvam/OpenAI/offline knowledge and summarization
- `ai/retrieval.py`, `knowledge_base/`: local source notes
- `legacy_app.py`, `db.py`, `extra.py`, `i18n.py`: previous demo preserved

## Version 1 release notes (2026-11-07)

- Renamed prominent title and subtitle according to the project wording.
- Added MS — RH / CHC / SDH to the sidebar demo role, oversight dashboard, and existing simulated hospital-stage actions.
- Added five compact, source-linked knowledge entries from the Maharashtra government’s CPHC and ASHA pages. Retrieval works locally without an AI API; Sarvam remains optional.
- Retained the original seven-level journey hierarchy, Mulshi facility finder, simulated inventory, event timeline, and original legacy app.
- No eight proposed future enhancements were implemented in this release.
