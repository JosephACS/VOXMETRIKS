# 046 — Validation / isolation tests (A–K) + invitation lifecycle (A–L)

## Isolation / membership (existing)

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
| I | (legacy letter) | invite checks moved to invitation suite A–L |
| J | Member no grant owner | 403/validation al promover/invitar owner |
| K | Engineer sin membership | mine vacío / 403 en space |
| L | Platform admin approve | no auto-member |

## Invitation lifecycle (real tests)

| ID | Caso | Expectativa |
|----|------|-------------|
| A | invite → accept once | PASS; membership created |
| B | second accept same token | `InvitationAlreadyUsed` |
| C | expired invite | `InvitationExpired` |
| D | revoke via API then accept | `InvitationRevoked` |
| E | resend → old token | fails (`NotFoundError` / hash miss) |
| F | resend → new token | accept succeeds |
| G | email mismatch | `PermissionDenied`; no membership; invite stays `pending` |
| H | revoke invite of another artist | `NotFoundError` / `PermissionDenied` |
| I | reader/member without invite perm | blocked on list/revoke/resend/create |
| J | owner role never via invite | `ValidationError` |
| K | list pending | no `token_hash` / plaintext |
| L | accepted invite cannot be invitation-revoked | `ValidationError`; membership remains until team revoke |

API: `POST /artist-invitations/accept` with JSON `{ token }` works; old `/{token}/accept` path is gone (route 404).

## FE

- vitest: canAccess / guards / space policy / artist context / invitation token-in-body
- `npx ng build --configuration=development`

## Clean verify worktree

Tras push: worktree temp desde tip SHA → pytest críticos + vitest + ng build.
