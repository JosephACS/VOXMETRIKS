# Quickstart — 051 Verification

## Preconditions

1. Work on `codex/051-artist-professional-journey`.
2. Record `git status`, HEAD and canonical DB hash/mtime.
3. Use temporary databases for backend/E2E mutations.
4. Preserve unrelated Listener working-tree changes.

## Directed development gates

```powershell
cd apps/backend
python -m pytest -q tests/test_spec051_artist_identity.py tests/test_spec051_artist_publishing.py

cd ../frontend
npm test -- --include='**/artist-professional-journey*.spec.ts'
```

## Closure gates

```powershell
cd apps/backend
python -m pytest -q
python -c "from app.main import create_app; print(len(create_app().routes))"

cd ../frontend
npm run lint
npm test
npm run build

cd ../..
npm --prefix automation/playwright run e2e -- --grep "Artist professional journey"
git diff --check
```

## Required E2E personas

- listener with no artist
- claimant/new-artist applicant
- artist owner
- artist administrator
- artist collaborator
- artist reader
- label catalog manager with two artists
- Platform Admin/catalog reviewer

E2E runs on an isolated DB copy and covers 1366×768 plus 390×844. Never report manual/browser success without evidence.
