# State machine — Spec 031

## States

`draft` → `submitted` → `under_review` → (`changes_requested` ↔ `submitted`) → `approved` → (`scheduled` →) `published`

Also: `rejected`, `suspended`, `withdrawn`, `archived` from allowed sources.

## Valid transitions (canonical)

| From | To |
|------|----|
| draft | submitted, archived |
| submitted | under_review, changes_requested, rejected, withdrawn |
| under_review | changes_requested, approved, rejected, withdrawn |
| changes_requested | submitted, withdrawn, archived |
| approved | scheduled, published, withdrawn |
| scheduled | published, withdrawn, suspended |
| published | suspended, withdrawn |
| suspended | published, withdrawn, archived |
| rejected | draft, archived |
| withdrawn | archived |

Illegal jumps raise domain error. Self-approve (creator == reviewer) blocked unless `ALLOW_DEMO_SELF_APPROVE=1` and `is_demo`.

## Publish prerequisites

- status in {approved, scheduled}
- validate_ready passed
- rights gate OK (100% ownership, no blocking conflict)
- idempotent publication key
