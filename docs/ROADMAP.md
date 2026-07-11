# VOXMETRIKS — Roadmap Final

**Versión de referencia:** V2 RC1 (2026-07-10)  
**Detalle histórico:** [roadmap/roadmap.md](roadmap/roadmap.md)

---

## Corto plazo (0–6 semanas)

**Objetivo:** estabilizar la beta y pulir la demo.

| Ítem | Tipo |
|------|------|
| Corregir warnings ESLint restantes (any / unused) | calidad |
| Reducir warnings de budget (bundle / CSS Home) | performance |
| Sustituir `console.error` por logger/UI state donde aporte | polish |
| Suite Playwright smoke en CI (login → home → play) | tests |
| Auth en rutas enterprise analytics legacy si siguen públicas | seguridad |
| Documentar o marcar deprecación `/api/v2` | claridad |
| Screenshots reales en docs de presentación | docs |

---

## Mediano plazo (1–2 trimestres)

**Objetivo:** mejorar experiencia y proveedores sin reescribir el core.

| Ítem | Tipo |
|------|------|
| Más proveedores de audio (Jamendo, Archive.org, etc.) | audio |
| PWA / instalación móvil ligera | UX |
| Recomendaciones con embeddings ligeros (CPU) | ML |
| Sincronización multi-dispositivo (favoritos/cola vía API) | sync |
| Redis opcional para cache y rate-limit multi-worker | infra |
| WebSocket autenticado (reemplazo gradual de polling) | realtime |
| Observabilidad: Prometheus `/metrics` + traces básicos | ops |

---

## Largo plazo (6–18 meses)

**Objetivo:** producto comercializable / cloud.

| Ítem | Tipo |
|------|------|
| Licenciamiento musical real / acuerdos de catálogo | legal |
| Monetización (planes, límites, ads opcionales) | negocio |
| Multi-tenant SaaS | arquitectura |
| Infraestructura cloud (managed DB, object storage, CDN) | cloud |
| App desktop (Electron/Tauri) o nativa | clientes |
| IA avanzada (embeddings, radio continua, personalización profunda) | IA |
| Cumplimiento GDPR / auditoría de datos | compliance |

---

## Principios del roadmap

1. **Estabilidad antes que features**  
2. **IA siempre con fallback local**  
3. **No romper Fases 1–6**  
4. **Redis/GPU/cloud solo cuando el entorno lo justifique**  

---

## Fuera de roadmap inmediato

- Chatbot genérico tipo ChatGPT embebido  
- Entrenamiento de modelos gigantes en el monorepo  
- Reescritura completa del frontend o warehouse  
