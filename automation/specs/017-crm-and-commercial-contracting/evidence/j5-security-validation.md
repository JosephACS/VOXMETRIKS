# J5 — Security validation

**Status**: PASS

## Covered / corrected

| Threat | Result |
|--------|--------|
| Normal user → CRM | 403 |
| Org owner without platform role → CRM | 403 |
| admin/engineer implicit CRM | Denied |
| sales_agent approve discount | Denied |
| sales_manager approve | Allowed |
| auditor write | Restricted to view |
| Sent quotation mutate | Blocked |
| Claim token replay | Blocked |
| Double conversion | Blocked |
| sales_agent as client owner after Path B | Not owner |
| Link without org owner confirm | Blocked |
| Secrets in audit | claim_token/token_hash forbidden keys |
| SQL injection surface | Parameterized SQL |

## Tests
`test_crm_security_j5.py` — PASS (26 cases in suite)
