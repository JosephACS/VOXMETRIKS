# Data model — Spec 031

Additive tables in `catalog_publishing.infrastructure.schema`:

| Table | Purpose |
|-------|---------|
| `app_release_submission` | Release lifecycle + org/artist scope |
| `app_release_submission_track` | Tracks in submission |
| `app_release_contributor` | Roles on release/track |
| `app_release_review` | Review decisions |
| `app_release_review_issue` | Issues / blocks |
| `app_release_status_history` | Append-only transitions |
| `app_release_publication` | Idempotent publish record |
| `app_release_takedown` | Suspend/withdraw reasons |
| `app_media_asset` | Metadata for stored files |
| `app_media_upload` | Upload receipt |
| `app_media_validation` | Check results |
| `app_catalog_duplicate_candidate` | Dup warnings/blocks |
| `app_catalog_publication_event` | Publish audit events |
| `app_artist_portal_access` | User ↔ artist portal scope |

Reused: `app_artist_profile`, `app_catalog_asset`, `app_rights_contract*`, `app_track_audio_source`, optional `app_track_cover`.

Filesystem (default): `data/media/private/...` · `data/media/published/...`
