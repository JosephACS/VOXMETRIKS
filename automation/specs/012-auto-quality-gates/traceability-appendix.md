# Traceability Appendix — Spec 012: Calidad Automática y Tests de Hotspots

**Version**: 1.0.0  
**Date**: 2026-06-29  
**Spec**: [spec.md](./spec.md)

## FR → Implementation → Evidence

| FR ID | Requirement | Implementation | Evidence |
|-------|-------------|----------------|----------|
| FR-QG01 | Ruff backend config | `backend/pyproject.toml` | `python -m ruff check .` → pass |
| FR-QG02 | Makefile scripts | `backend/Makefile` | `make check` |
| FR-QG03 | ruff + pytest-cov deps | `backend/requirements.txt` | pip install |
| FR-QG04 | Angular ESLint | `frontend/eslint.config.js` | `npm run lint` |
| FR-QG05 | npm scripts | `frontend/package.json` | `npm run check` |
| FR-QG06 | Vitest estándar | `angular.json`, `vitest.config.ts` | `npm run test` |
| FR-QG07 | Backend hotspot tests | `backend/tests/test_quality_hotspots.py` | 13 pytest cases |
| FR-QG08 | Frontend hotspot test | `music-player.service.spec.ts` | 6 vitest cases |
| FR-QG09 | Sin cambio lógica | Solo tests + tooling + auto-fix mecánico | diff review |
| FR-QG10 | check exit 0 | Validación 2026-06-29 | CI-ready |

## User Story → Test Mapping

| Story | Acceptance | Test / Command |
|-------|------------|----------------|
| US1 Backend gate | `make check` | pytest 74 + ruff |
| US2 Frontend gate | `npm run check` | eslint + vitest 8 + build |
| US3 Hotspots | Isolated tests | `test_quality_hotspots.py`, `music-player.service.spec.ts` |

## Hotspot Coverage

| Hotspot | Module | Test file | Approx. coverage |
|---------|--------|-----------|------------------|
| `generate_synthetic_activity` | `synthetic/generator.py` | `test_quality_hotspots.py::TestGenerateSyntheticActivity` | 49% (guards) |
| `get_tracks_cursor` | `tracks/list.py` | `test_quality_hotspots.py::TestGetTracksCursor` | 100% |
| `get_recommendations` | `recommendations/service.py` | `test_quality_hotspots.py::TestGetRecommendations` | 77% |
| `MusicPlayerService.loadTrack` | `music-player.service.ts` | `music-player.service.spec.ts` | Observable behavior |

## SC Verification

| SC ID | Criterion | Result |
|-------|-----------|--------|
| SC-QG01 | backend check < 2 min | ~10s observed |
| SC-QG02 | frontend check exit 0 | ✅ |
| SC-QG03 | ≥ 70 backend tests | 74 passed |
| SC-QG04 | ≥ 8 frontend tests | 8 passed |
| SC-QG05 | cov ≥ 60% | 65% total |
| SC-QG06 | SDD docs complete | ✅ this appendix |
