# Architecture, operating modes, test plan

## Operating modes

**No API key:** Python token-based lexical retrieval against five source-attributed public-health notes; deterministic extractive answers. Doctor feedback is formatted verbatim. All existing referral, notification, search, multilingual, voice recording and draft export/import functions remain.

**With API key:** Same retrieval runs locally; retrieved notes are sent to an OpenAI model to produce a citation-oriented answer. Doctor feedback can be reformatted into an unapproved summary draft. API errors fall back to offline mode. Only synthetic inputs are permitted.

## Reproducibility

Python 3.10+, pip, network for package installation. Install with `python -m pip install -r requirements.txt`; copy `.env.example` to `.env` and set `OPENAI_API_KEY` optionally; run `python -m streamlit run app.py`. Database is created automatically. No embedding model download or precomputed vector index required. This is **lexical retrieval + optional LLM**, not embedding-based semantic RAG.

## Upgrade to full semantic RAG

1. Get clinician-approved, appropriately licensed source documents and exact versions.
2. Parse pages and preserve headings/page references; chunk by clinical section.
3. Embed chunks with configurable embeddings model; build reproducible local index.
4. Hybrid retrieval (BM25 + vectors), metadata filters, source-version checks and minimum confidence thresholds.
5. Evaluate 30+ clinician-reviewed questions including no-answer, misleading wording, multilingual and prompt-injection cases.
6. Review groundedness, citation correctness, patient safety, privacy and abstention behavior.

## Acceptance tests

- Run `python -m pytest -q` and `python scripts/check_setup.py`.
- With no key: query HBNC schedule; receive sourced excerpt; no network call.
- With a valid key: same query; answer includes source ID, with source links displayed.
- With an invalid key: graceful fallback to excerpts.
- Summary: doctor original remains intact; generated text explicitly unapproved.
- Existing workflow: ASHA create -> doctor accept -> doctor feedback -> ASHA follow-up -> close.
- UI: change language; check notifications, search, timeline, accessibility controls.
- Never test with real patient information.

## Known limitations

Demo role switcher is not authentication. SQLite is single-instance local persistence, not a production multiuser database. Source notes are manually curated, not entire official PDFs. Search is lexical, so paraphrases in Marathi/Hindi may not retrieve as well as English. No actual offline sync; manual draft export/import only. Voice captures audio but does not transcribe. Summaries are preview-only and not automatically stored/approved. External API access requires internet and incurs provider charges.
