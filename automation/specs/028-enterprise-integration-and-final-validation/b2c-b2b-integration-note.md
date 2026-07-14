## Spec 029 linkage + cierre integrado (2026-07-14)

Personal (B2C) subscriptions are delivered in Spec **029** and remain catalog/API/UI separated from enterprise (B2B) plans validated in Spec 028.

- 028 = enterprise integration closure (prospect → org → Professional → invoice → mock pay → full).
- 029 = personal music line (Free → Premium / Familiar) without reopening B2B commercial rules.
- Integrated local demo: `docs/DEMO-ACCOUNTS.md` + `apps/backend/scripts/seed_integrated_demo.py`.
- Metrics and demos label B2C vs B2B explicitly; never mix MRR currencies or segments without a labeled total.
- Canonical demo org: `voxmetriks-demo` / **VOXMETRIKS Demo** (`is_demo=true`). Pytest/Golden Path pollution is cleaned via `cleanup_test_organizations.py`.
