# J2 — Domain and use cases

**Status**: PASS

## Use case modules (consolidated)

| Module | Coverage |
|--------|----------|
| ProspectUseCases | create/list/get/update/status transitions |
| ContactUseCases | create/update/link to prospect |
| OpportunityUseCases | create/update/stage/close + stage history |
| ActivityUseCases | create/update/list timeline |
| QuotationUseCases | create/version/items/send/request-approval; immutability after sent; discount gate |
| ApprovalUseCases | approve/reject (manager); agent cannot self-approve discount |
| ConversionUseCases | prepare claim / confirm-link / claim; idempotent; CreateOrganization via 016 |
| ContractUseCases | create/approve/send/academic accept/reject/expire/terminate |

## State machines (as-implemented)

- Prospect: new → contacted → qualified → disqualified | converted  
- Opportunity: open → qualified → proposal → negotiation → won | lost | canceled  
- Quotation version: draft → pending_approval → approved → sent → accepted | rejected | expired | superseded  
- Conversion: pending → awaiting_customer_claim → processing → completed | failed | canceled  
- Contract: draft → pending_approval → approved → sent → accepted → active_handoff | rejected | expired | terminated  

## Tests
`test_crm_use_cases_j2.py` — PASS
