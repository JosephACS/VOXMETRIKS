# Artist and Catalog Model — Spec 015

**Status**: Diseñado (corrección NEEDS_CORRECTIONS)  
**Fecha**: 2026-07-11

---

## Distinción crítica

| Concepto | Estado |
|----------|--------|
| `dim_artista` / `dim_track` / `dim_album` (warehouse) | **Implementado/parcial** — analytics |
| `artist_profile` empresarial | **Diseñado** |
| Derechos (`rights_contract`, parties, territory) | **Diseñado** |
| Audio YT/Audius/demo | **Parcial** — no licencia comercial |

---

## Gestión artística

Registro → assignment → equipo → perfil → estado → relación org.  
Estados artista: draft · active · inactive · archived.

---

## Modelo mínimo de derechos

Todo derecho debe considerar:

| Elemento | Descripción |
|----------|-------------|
| catalog asset | Obra (ref opcional warehouse) |
| rights_type | Tipo de derecho |
| contract_party | Parte contractual |
| ownership_percentage | Porcentaje |
| territory | Territorio |
| valid_from / valid_to | Vigencia |
| exclusive / non-exclusive | Exclusividad |
| authorized_use | Usos autorizados |
| status / conflict | Incluye `disputed` |

### Validación del 100 %

La suma de `ownership_percentage` debe validarse por:

**asset + rights_type + territory + periodo aplicable**

No basta un total global sin territorio/periodo (BR-CAT-02).

Conflictos → `disputed` → bloqueo de campañas/usos nuevos (BR-CAT-03).

---

## Relación con engagement / ROI

Engagement warehouse puede informar lift; **no** se convierte en ingreso sin `attributable_revenue_record` aprobado.

---

## Fuera de alcance aquí

Migraciones DuckDB · tablas físicas · ownership legal real de Spotify.
