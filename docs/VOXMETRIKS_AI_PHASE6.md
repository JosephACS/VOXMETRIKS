# VOXMETRIKS AI — Fase 6

**Fecha:** 2026-07-05  
**Alcance:** AI Provider desacoplado, búsqueda natural, playlist por prompt, explicaciones, mood, AI DJ  
**Sin dependencia obligatoria de APIs pagas**

---

## Arquitectura AI Provider

```
AIService (facade)
    └── AIProvider (interface)
            ├── LocalRuleBasedAIProvider  ← DEFAULT (offline)
            ├── ExternalLLMProvider       ← opcional si AI_LLM_API_KEY
            └── MockAIProvider            ← tests
```

La app **nunca** importa OpenAI directamente fuera de `providers/external.py`.

---

## Qué funciona localmente (sin API key)

| Feature | Método |
|---------|--------|
| Búsqueda natural | Reglas ES/EN → filtros audio (`nl_search.py`) |
| Playlist por prompt | Preview + confirmación manual |
| Explicaciones | Códigos `reason` → texto humano |
| Mood profile | Audio DNA + traits |
| AI DJ | Bloques de escucha por energía/gusto |
| Smart Home widgets | Para estudiar / entrenar / relajarte |

---

## Qué requiere API externa (opcional)

| Feature | Mejora con LLM |
|---------|----------------|
| Explicaciones | Frases más naturales |
| Nombre/descripción playlist | Texto más creativo |

Configuración:

```env
AI_PROVIDER=external
AI_LLM_API_KEY=sk-...
AI_LLM_BASE_URL=https://api.openai.com/v1
AI_LLM_MODEL=gpt-4o-mini
```

Si falla o no hay key → **fallback automático a reglas locales**.

---

## API — `/api/v1/ai/*`

| Endpoint | Descripción |
|----------|-------------|
| `GET /ai/provider/status` | Provider activo |
| `POST /ai/search/natural` | NL → tracks |
| `POST /ai/playlist/preview` | Preview sin guardar |
| `POST /ai/playlist/confirm` | Guardar tras confirmación |
| `GET /ai/explain/recommendation/{id}` | Explicación |
| `GET /ai/mood-profile` | Perfil mood extendido |
| `GET /ai/dj/session` | Bloques AI DJ |
| `GET /ai/widgets/intent` | Widgets Home por intención |

---

## Privacidad

`sanitizer.py` elimina antes de LLM externo:

- passwords, tokens, emails completos
- username parcialmente enmascarado

Documentado en código — no enviar datos sensibles.

---

## Frontend

| Archivo | Rol |
|---------|-----|
| `packages/ai/services/ai.service.ts` | Cliente API |
| `packages/ai/components/ai-playlist-dialog.component.ts` | Crear playlist con confirmación |
| `packages/streaming/search/search.component.*` | Búsqueda natural + botón playlist |
| `packages/smart/widgets/home-section-widget.component.ts` | Muestra `reason` en meta |

---

## Tests

```bash
cd apps/backend
python -m pytest tests/test_ai_phase6.py -q

cd apps/frontend
npm run test -- ai-phase5-6
```

---

## Pendientes

- Embeddings / vector search (roadmap v3.0)
- SSE auth para eventos AI en tiempo real
- Voz real para AI DJ (opcional)

---

*Fase 6 — VOXMETRIKS AI con fallback local obligatorio.*
