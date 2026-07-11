# I6 — Frontend validation

**Status**: PASS (with budget debt)  
**Date**: 2026-07-11

## Commands

| Gate | Result |
|------|--------|
| `npm run lint` | **0 errors**, 13 warnings (preexistentes; max-warnings 50) |
| `npm run test` | **14 files / 77 tests PASS** |
| `npm run build` | **OK** |

## Organizations coverage (unit + routes)

Rutas registradas (I4/I5):

- `/organizations/new|onboarding|none|suspended|closed`
- `/organizations/:id/settings|members|invitations|roles|audit`
- `/access-denied`, `/invitations/accept`
- Selector shell + context clear-on-switch (I4/I5 tests)

## Budget warnings (accepted debt)

```text
bundle initial exceeded maximum budget: 644.42 kB > 550.00 kB (+94.42 kB)
home.component.css exceeded maximum budget: 17.39 kB > 16.00 kB (+1.39 kB)
```

Preexistentes a 016; no bloquean cierre si se registran como deuda.

Artifacts: `_i6_fe_lint.txt`, `_i6_fe_test.txt`, `_i6_fe_build.txt`
