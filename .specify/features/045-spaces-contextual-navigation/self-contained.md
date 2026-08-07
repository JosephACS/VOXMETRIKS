# Spec 045 — Self-contained branch validation

## Claim

`feature/045-spaces-contextual-navigation` is intended to be **self-contained for frontend compile**: a clean checkout of the branch tip must resolve all relative imports reachable from Spec 045 / shell entrypoints without relying on uncommitted WT files.

## What was missing before

Tracked `app.routes.ts` and commercial `*.routes.ts` already referenced Spec 043/044 surfaces (workpanel, simple/complex reports, profiles layout, staff/platform guards, org module guards, catalog hub, unresolved audio, activity) whose implementing files were still **untracked** on the branch.

## What this commit does

1. Adds the FE dependency closure listed in `dependency-closure.md`.
2. Aligns org commercial routes with `organizationRequiredGuard` + `organizationModuleGuard`.
3. Documents decisions A/B/C for include/exclude.

## How to re-verify

```powershell
git worktree add ../voxmetriks-045-verify HEAD
cd ../voxmetriks-045-verify/apps/frontend
npm ci   # or npm install
npx vitest run src/app/core/spaces src/app/core/guards/product-surface.guard.spec.ts src/app/core/navigation/nav-access.policy.spec.ts src/app/packages/organizations/organization-access.spec.ts
npx ng build --configuration=development
cd ../..
# from main repo:
git worktree remove ../voxmetriks-045-verify
```

Spaces / product-surface sources that only differed by CRLF were **not** re-committed.
