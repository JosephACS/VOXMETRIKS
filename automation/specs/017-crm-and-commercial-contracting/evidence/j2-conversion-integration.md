# J2 — Conversion integration with Organizations

**Status**: PASS (integration tests)

## Path A — link existing org
- Requires authenticated **owner** of target organization (`confirm-link`)
- sales_agent alone cannot link
- Registers CRM↔organization; conversion `completed`
- No subscription created

## Path B — new org via claim
- Conversion `awaiting_customer_claim`
- Raw claim token returned **once**; only hash stored
- Claimant authenticates via identity; `CreateOrganization` with claimant as actor/owner
- sales_agent is **not** org owner after convert
- Token replay rejected
- Double conversion blocked

## Invariants preserved (016)
- Organization cannot exist active without real owner
- No orphan org from CRM path

## Tests
Covered in `test_crm_use_cases_j2.py` and `test_crm_security_j5.py`
