# 046 — Validation / isolation tests (A–K)

| ID | Caso | Expectativa |
|----|------|-------------|
| A | `mine` vacío | `[]` para usuario sin memberships |
| B | `mine` uno | un item con permissions[] y org_id |
| C | `mine` muchos | N items solo del session user |
| D | Revoked desaparece | tras revoke, no en `mine` |
| E | Isolation A/B | user A no ve space de B |
| F | Pending claim | no membership, no space data |
| G | Approve claim | membership owner + datos space |
| H | Reject | sin membership |
| I | Invite expired/revoked/one-time | accept falla tras uso/expiración/revocación |
| J | Member no grant owner | 403/validation al promover/invitar owner |
| K | Engineer sin membership | mine vacío / 403 en space |
| L | Platform admin approve | no auto-member |

## FE

- vitest: canAccess / guards / space policy / artist context
- `npx ng build --configuration=development`

## Clean verify worktree

Tras push: worktree temp desde tip SHA → pytest críticos + vitest + ng build.
