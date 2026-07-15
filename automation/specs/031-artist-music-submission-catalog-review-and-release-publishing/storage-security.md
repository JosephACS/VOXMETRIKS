# Storage & security — Spec 031

## Env

| Var | Default / note |
|-----|----------------|
| `MEDIA_STORAGE_PROVIDER` | `local` |
| `MEDIA_STORAGE_ROOT` | `<repo>/data/media` |
| `MEDIA_MAX_AUDIO_SIZE_MB` | `50` |
| `MEDIA_MAX_IMAGE_SIZE_MB` | `10` |
| `MEDIA_MIN_COVER_PX` | `500` |
| `MEDIA_PUBLIC_BASE_URL` | optional API public base |
| `ALLOW_DEMO_SELF_APPROVE` | `0` (demo-only override) |

## Layout

```
data/media/
  private/{organization_id}/{uuid}.ext
  published/{organization_id}/{uuid}.ext
```

## Controls

- Extension + MIME + magic where possible
- Size caps · empty rejected · sanitized names · UUID final names
- Path traversal blocked · no executables
- Private content not listable as public catalog
- API never returns OS absolute paths
- IDOR: org + artist portal + reviewer ACL on media content

## Debt

Antivirus · cloud object store · CDN · DRM · professional transcoding · acoustic fingerprint
