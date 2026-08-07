# Spec 045 — Self-contained branch validation

## Platform Admin vs Data Ops (hotfix)

| Espacio | Elegibilidad FE |
|---------|-----------------|
| **Data Ops** | `hasEngineerAccess()` → identity `admin` **o** `engineer` |
| **Platform Admin** | identity `admin` **o** CRM `platform_admin` |

`platformAdminGuard` **no** usa `hasEngineerAccess()`. Un engineer puro:
- ve Data Ops;
- **no** ve el espacio Platform Admin;
- **no** entra a `/platform-ops` (acceso denegado).

Ver `platform-admin.guard.ts` + `canAccessPlatformAdmin`.

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
