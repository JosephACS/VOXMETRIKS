# Playback architecture

**Estado:** parcial / implementado en capas (ver [`../STATUS.md`](../STATUS.md)).

## Capas vigentes

| Capa | Ubicación |
|------|-----------|
| UI player bar / now-playing | `apps/frontend/src/app/shared/components/` |
| Music player service | `apps/frontend/src/app/shared/services/music-player.service.ts` |
| Playback core / resolver | `apps/frontend/src/app/playback-core/` |
| Disponibilidad / listening API | `apps/backend` listening + playback helpers |

## Fuente de audio del producto

El flujo normal usa únicamente Spotify Web Playback SDK con OAuth PKCE. El
catálogo y el warehouse aportan metadatos, estadísticas y recomendaciones; no
se presentan como fuente de audio. Cuando Spotify no está conectado o no hay
una coincidencia reproducible, el reproductor termina con un mensaje claro y no
cae silenciosamente en YouTube, video, Audius ni audio demo.

**No** es un servicio de streaming comercial licenciado: cada usuario reproduce
desde su cuenta Spotify autorizada y Premium.

## Notas

- Documentos de fases históricas (Spotify UX, engine phase2, auditorías playback) se retiraron; recuperables en Git `d2f6a27f`.
- Decisiones Spec 014 phase-F históricas: ver `.specify/history/014-…` si se necesita el texto original.
