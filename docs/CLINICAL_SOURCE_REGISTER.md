# Official source register and safety boundaries

These are **public government-hosted references**, not an assertion that their full PDFs are bundled, licensed for redistribution, or clinician-approved for clinical decision support. The repository contains **short attributed summaries only**. Before clinical use, Dr. Prashant should validate versions, scope, applicability, translations and exact passages.

| ID | Official reference | Coverage |
|---|---|---|
| NHM-HBNC-01 / 03 | https://www.nhm.gov.in/index1.php?lang=1&level=0&lid=760&linkid=491 | HBNC home visits, referral/follow-up |
| NHM-HBYC-02 | Same NHM page | HBYC visits at 3/6/9/12/15 months |
| NHM-ASHA-M6-04 | https://hbnc-hbyc.mohfw.gov.in/assets/document/ASHA_Training_Module_6.pdf | Maternal health training topics |
| NHM-ASHA-M7-05 | https://hbnc-hbyc.mohfw.gov.in/assets/document/ASHA_Training_Module_7.pdf | Child health and common illness training topics |
| Additional modules | https://nhm.gov.in/index1.php?lang=1&level=3&sublinkid=184&lid=257 | ASHA books, English/Hindi |
| HBNC/HBYC resources | https://nhm.gov.in/index4.php?lang=1&level=0&linkid=522&lid=826 | NHM handbooks |

## Suggested safe demo questions

1. On which days are scheduled HBNC visits after an institutional delivery?
2. What extra HBNC visit is described for a home delivery?
3. At what child ages are HBYC visits scheduled?
4. What is ASHA's role in facilitating referral and follow-up?
5. Which subjects appear in ASHA Training Module 7?
6. Does the supplied material specify a patient-specific time to recover from fever? **Expected: no; abstain.**

## Clinical controls

- No real patients or protected health information in demo or external API requests.
- The system is document navigation, not diagnosis, triage, prescribing or treatment guidance.
- Source notes are **not full protocol retrieval**; for actual protocol RAG, ingest exact approved passages and page metadata, then evaluate retrieval.
- Clinical review and version approval are required before making health recommendations.
- Programme visit schedules do not establish individual treatment or recovery timelines.


## Version 1 — Maharashtra government material (2026-11-07)
- https://phd.maharashtra.gov.in/en/scheme/arogyam-paramam-dhanam/ — Maharashtra Public Health Department, Arogyam Paramam Dhanam (source page dated 04 Jan 2025). Summary notes cover continuity of care, SC-AAM staffing, listed service categories and teleconsultation hub/spoke programme. Notes are not clinical protocols.
- https://phd.maharashtra.gov.in/en/scheme/accredited-social-health-activist-asha/ — Maharashtra Public Health Department, Accredited Social Health Activist (ASHA) (source page dated 03 Jan 2025). Summary notes cover community-link objectives and examples of programme activities. Not a comprehensive regulatory job description.
- Knowledge entries: MAH-CPHC-2025-01/02/03 and MAH-ASHA-2025-01/02 in `knowledge_base/official_source_notes.json`. No treatment dosing or local antivenom availability claims are included.
