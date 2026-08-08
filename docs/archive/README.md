# Archivo documental

Los informes, auditorías, demos repetidas, exports GA07, reviews Omega y copias históricas se **retiraron del working tree** en la consolidación documental.

| Documento / carpeta retirada | Recuperable en Git |
|------------------------------|--------------------|
| Informes / demos / GA07 export bajo `docs/` (rutas históricas) | `git show d2f6a27f:<path>` |
| `docs/playback/*`, `docs/presentation/*`, `docs/portfolio/*`, `docs/screenshots/*` | `git show d2f6a27f:<path>` |
| Evidence / tasks / plans bajo historial Spec Kit | `git show d2f6a27f:<path>` cuando existían en ese commit |
| `archive/**` (código legacy + generated) | `git show d2f6a27f:<path>` |
| `.specify/audits`, `.specify/design`, `.specify/decisions` | `git show d2f6a27f:<path>` |

**Ejemplos reales (solo lectura vía `git show`; no hace falta mutar el working tree):**

```bash
git show d2f6a27f:docs/architecture/architecture.md
git show d2f6a27f:docs/STATUS.md
git show d2f6a27f:.specify/memory/constitution.md
```

**No** uses `git checkout <commit> -- <path>` sobre este working tree de consolidación salvo que se decida explícitamente restaurar un archivo.

**Nota:** Specs completas **032–044** no están en `d2f6a27f`; viven solo en el checkout antiguo read-only (ver [`.specify/history/README.md`](../../.specify/history/README.md)).

Estado vigente: [`../STATUS.md`](../STATUS.md).
