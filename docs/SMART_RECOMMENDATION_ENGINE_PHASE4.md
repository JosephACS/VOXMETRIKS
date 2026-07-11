# SMART RECOMMENDATION ENGINE — Fase 4

**Fecha:** 2026-07-05  
**Alcance:** Recomendaciones inteligentes, personalización, Home dinámica  
**Prerequisitos:** Fases 1–3 (sin modificaciones)

---

## Objetivo

Convertir VOXMETRIKS en una plataforma que **entiende los gustos** de cada usuario — sin chatbot, sin texto generativo. Mejora la experiencia musical con recomendaciones explicables y contenido distinto por usuario.

---

## Arquitectura (desacoplada)

```
SmartRecommendationService (facade)
        │
        ├── HomeComposer ──────────► secciones Home dinámicas
        ├── PersonalizationEngine ─► perfil musical + Audio DNA
        ├── RankingEngine ─────────► híbrido heuristic + content-based
        │       └── RecommendationEngine (existente, sin modificar)
        ├── SimilarityEngine ──────► cosine similarity audio features
        ├── FeatureExtractor ──────► vectores + centroides de gusto
        ├── DiscoverWeekly ────────► playlist semanal
        ├── DailyMix ──────────────► mixes por cluster (Rock/Pop/Chill/Instrumental)
        ├── BecauseYou ────────────► secciones contextuales
        └── TrendingModules ───────► trending today/week/genre/growth/saved
```

**Principio:** Reproducción (Fases 1–3) y recomendaciones (Fase 4) están **separadas**.

---

## Algoritmos

### Content-Based Filtering
- Vector de 8 dimensiones por track: `danceability`, `energy`, `speechiness`, `acousticness`, `instrumentalness`, `liveness`, `valence`, `tempo` (normalizado)
- **Centroide de gusto** = promedio de vectores de favoritos + reproducciones warehouse
- **Cosine similarity** entre centroide y candidatos

### Hybrid Ranking
```
score_final = 0.65 × heuristic_score + 0.25 × content_similarity + 0.15 × favorite_boost
```
Heuristic score = motor existente (popularity 35%, engagement 25%, collaborative 20%, trending 20%).

### Similar Artists
- Perfil audio promedio del artista
- Cosine similarity + bonus mismo género

### Discover Weekly
- Seed semanal determinista por usuario (`SHA256(user + ISO week)`)
- Mezcla: artistas conocidos + descubrimientos + trending

### Daily Mix
- Clusters por reglas de audio features:
  - Rock: energy ≥ 0.55
  - Pop: danceability ≥ 0.55
  - Chill: energy ≤ 0.45
  - Instrumental: instrumentalness ≥ 0.5

---

## Señales de usuario

| Señal | Fuente |
|-------|--------|
| Favoritos | `app_favorite` |
| Reproducciones | `fact_streaming` / `silver_streams` |
| Skips | `fact_streaming.skipped` |
| Géneros/artistas top | agregaciones warehouse |
| Audio features | `dim_track` |

Warehouse user: `1 + ((app_user_id - 1) % 5000)` (datos sintéticos alineados).

---

## API — `/api/v1/smart/*`

| Endpoint | Descripción |
|----------|-------------|
| `GET /smart/home` | Home personalizada (secciones + perfil) |
| `GET /smart/profile` | Top géneros/artistas/tracks + Audio DNA |
| `GET /smart/recommendations` | Tracks rankeados |
| `GET /smart/discover-weekly` | Playlist semanal |
| `GET /smart/daily-mixes` | Daily Mixes |
| `GET /smart/because-you` | Secciones "Porque escuchaste..." |
| `GET /smart/similar-tracks/{id}` | Similares por audio features |
| `GET /smart/similar-artists/{id}` | Artistas relacionados |
| `GET /smart/trending` | Módulos trending |

Requiere autenticación (excepto trending).

---

## Frontend

| Archivo | Rol |
|---------|-----|
| `packages/smart/services/smart-home.service.ts` | Cliente API |
| `packages/smart/models/smart-home.models.ts` | Tipos |
| `packages/smart/widgets/home-section-widget.component.ts` | Widget reutilizable por sección |
| `packages/streaming/home/home.component.*` | Home dinámica desde `/smart/home` + Audio DNA |
| `packages/streaming/track-detail/*` | Canciones similares vía `/smart/similar-tracks` |
| `packages/streaming/artist-detail/*` | Artistas relacionados vía `/smart/similar-artists` |

La Home ya **no hardcodea** el rail "For you" desde discover genérico — usa recomendaciones del engine cuando están disponibles.

---

## Audio DNA (ejemplo)

```json
{
  "energetic": 85,
  "dance": 70,
  "acoustic": 12,
  "instrumental": 25,
  "positive": 68
}
```

Generado automáticamente del centroide de gusto del usuario.

---

## Escalabilidad / Fase 5+

- Escribir eventos reales (play/skip/favorite) a `fact_user_activity`
- Mapeo 1:1 app_user → warehouse user
- Embeddings pre-computados en gold layer
- LightFM / implicit ALS offline (sin GPU)
- A/B testing de pesos de ranking
- Discover Weekly persistida como playlist en `app_playlist`

---

## Archivos creados

### Backend
- `packages/analytics/services/smart/` (10 módulos)
- `packages/analytics/routes/smart.py`
- `tests/test_smart_recommendations.py`

### Frontend
- `packages/smart/` (models, service, widget, tests)

---

## Pruebas ejecutadas

```bash
cd apps/backend
python -m pytest tests/test_smart_recommendations.py tests/test_recommendation_engine.py -q

cd apps/frontend
npm run test
npm run build
```

**Resultados (2026-07-05):** Backend 8/8 pytest OK · Frontend 51/51 vitest OK · Build OK

---

## Compatibilidad

- Fases 1–3: **sin cambios** en playback, audio resolver, favoritos
- `RecommendationEngine` original: **reutilizado**, no reemplazado
- API legacy `/analytics/recommendations`: intacta

---

*Fase 4 — Smart Recommendation Engine completada.*
