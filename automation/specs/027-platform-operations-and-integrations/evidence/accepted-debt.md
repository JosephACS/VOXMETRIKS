# Accepted Debt — Spec 027

- Playwright E2E NOT_VERIFIED
- Email: EmailPort implemented (`console` | `smtp` | `resend`); default `console` for tests.
  Real SMTP smoke **PASS** (see Spec 028 final-validation). Console remains the pytest default.
- Mock payment remains labeled `[MOCK]` / academic — never real money
- Backup files are conceptual paths — not real filesystem backup
- Job scheduler reuses existing `platform/jobs` asyncio loop; `app_background_job` is registry/metadata only
