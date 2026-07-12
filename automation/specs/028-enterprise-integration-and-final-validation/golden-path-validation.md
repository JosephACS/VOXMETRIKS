# Golden Path Validation — Spec 028 (gap closure 2026-07-12)

```text
login → prospect → opportunity → accepted quotation → contract → conversion
→ organization → select plan → subscription → invoice → failed attempt
→ past_due → retry → mock payment settled → allocation → reconciliation
→ subscription active → access full → strategic MRR/ARR → report
→ business decision → Customer Success → support
```

## Automated smoke (`test_enterprise_golden_path_s028.py`)

| Suite | Status |
|------|--------|
| Smoke: login / org / plans / campaigns / analytics / compliance / ops | **PASS** |
| Smoke: report + decision (024) | **PASS** |
| Smoke: CS health + support + renewal/expansion (025) | **PASS** |
| Commercial: CRM→contract→conversion→plan→sub→invoice→dunning→recover→MRR | **PASS** |
| Negatives: duplicate sub, wrong currency, cross-tenant, anon, concurrent retry | **PASS** |
| Logout → `/me` 401 | **PASS** |

## Policy notes

- Trial excluded from Active MRR; Past-due MRR reported separately
- No FX; multi-currency → No disponible for single KPI
- Payment/email remain mock/manual only
