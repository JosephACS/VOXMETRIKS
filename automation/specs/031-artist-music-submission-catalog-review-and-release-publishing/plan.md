# Plan — Spec 031

## Audit decisions (pre-code)

| Area | Finding | Decision |
|------|---------|----------|
| Artists | `app_artist_profile` + assignments | Reuse; link submissions via `artist_profile_id` |
| Catalog assets/releases | Spec 021 thin releases | Keep; publishing owns `app_release_submission*` and links `catalog_asset_id` / `catalog_release_id` |
| Audio | URL cache YouTube/Audius only | Add `MediaStoragePort` + `local_published` provider row in `app_track_audio_source` |
| Covers | URL cache / gradients | Add local cover media; optional `app_track_cover` URL to media API |
| Rights | Contracts + parties + conflicts | **Gate** approve/publish; do not invent % |
| Uploads | None in FastAPI today | New `data/media/{private,published}/…` |
| Royalties 030 | Allocates by `asset_id` / `warehouse_track_id` | Publish creates/links asset; events only on real plays / explicit demo weights |
| Warehouse | `dim_track` imported | Never mutate low ids; demo warehouse ids use reserved high range `>= 9_000_000` with `[DEMO-SUBMIT]` if insert required |

## Package

**New:** `apps/backend/app/packages/catalog_publishing`
**Not:** extend royalties; not overload catalog_rights workflow tables.

## FE

Package `catalog-publishing` + artist portal routes under `/artist/*` and `/catalog-review/*`.
Nav mode for `demo.artist` (preferences / portal access).

## Storage

`LocalMediaStorageProvider` · env `MEDIA_STORAGE_*` · replaceable later by S3/MinIO.

## Accepted debt (from day one)

Antivirus · CDN · DRM · multi-bitrate transcoder · acoustic fingerprint · cloud object storage.
