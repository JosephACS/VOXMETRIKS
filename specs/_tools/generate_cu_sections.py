#!/usr/bin/env python3
"""Generate full-format Casos de Uso sections (spec 001 standard) for specs 002-006."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CU_DEFS: dict[str, list[dict]] = {
    "002": [
        {"id": "CU-P01", "name": "Listar playlists propias", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida según spec 001", "flow": "1. Usuario solicita listado → 2. Sistema filtra por user_id → 3. Sistema retorna solo playlists propias",
         "post": "Lista playlists del usuario visible en UI", "alt": "2a. Sin sesión → 401 / redirect login (001)", "rb": "RB-P01, RB-P03"},
        {"id": "CU-P02", "name": "Crear playlist", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida; nombre no vacío", "flow": "1. Usuario ingresa nombre y descripción opcional → 2. Sistema valida → 3. Sistema persiste playlist con user_id",
         "post": "Playlist creada y visible en listado", "alt": "2a. Nombre vacío → error validación (RB-P02)", "rb": "RB-P01, RB-P02"},
        {"id": "CU-P03", "name": "Ver detalle playlist con tracks", "actor": "Usuario Registrado Autenticado",
         "pre": "Playlist pertenece al usuario", "flow": "1. Usuario solicita detalle → 2. Sistema verifica ownership → 3. Sistema retorna metadata y tracks ordenados",
         "post": "Detalle playlist mostrado", "alt": "2a. Playlist ajena o inexistente → 404 sin filtrar datos (RB-P03, FR-P12)", "rb": "RB-P03, RB-P04"},
        {"id": "CU-P04", "name": "Editar playlist", "actor": "Usuario Registrado Autenticado",
         "pre": "Ownership de playlist", "flow": "1. Usuario modifica nombre/descripción → 2. Sistema valida → 3. Sistema persiste cambios",
         "post": "Metadatos actualizados", "alt": "2a. Nombre inválido → error", "rb": "RB-P02, RB-P03"},
        {"id": "CU-P05", "name": "Eliminar playlist", "actor": "Usuario Registrado Autenticado",
         "pre": "Ownership de playlist", "flow": "1. Usuario confirma eliminación → 2. Sistema elimina playlist y junction tracks",
         "post": "Playlist eliminada", "alt": "2a. No owner → 404", "rb": "RB-P03, RB-P05"},
        {"id": "CU-P06", "name": "Añadir track a playlist", "actor": "Usuario Registrado Autenticado",
         "pre": "Playlist propia; track existe en catálogo (003)", "flow": "1. Usuario selecciona track → 2. Sistema valida → 3. Sistema añade junction si no duplicado",
         "post": "Track visible en detalle playlist", "alt": "2a. Track inexistente → 404; 2b. Duplicado → ignorar o rechazar (RB-P06)", "rb": "RB-P04, RB-P06"},
        {"id": "CU-P07", "name": "Quitar track de playlist", "actor": "Usuario Registrado Autenticado",
         "pre": "Ownership; track en playlist", "flow": "1. Usuario quita track → 2. Sistema elimina junction",
         "post": "Track removido de playlist", "alt": "2a. Track no en playlist → idempotente sin error", "rb": "RB-P03"},
        {"id": "CU-F01", "name": "Listar favoritos", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida", "flow": "1. Usuario abre biblioteca favoritos → 2. Sistema retorna tracks favoritos del user_id",
         "post": "Lista favoritos visible", "alt": "2a. Sin favoritos → empty state", "rb": "RB-F01, RB-F04"},
        {"id": "CU-F02", "name": "Añadir favorito", "actor": "Usuario Registrado Autenticado",
         "pre": "Track válido en catálogo", "flow": "1. Usuario marca favorito → 2. Sistema persiste par user-track único",
         "post": "Track en favoritos", "alt": "2a. Ya favorito → idempotente (RB-F03)", "rb": "RB-F01, RB-F02"},
        {"id": "CU-F03", "name": "Quitar favorito", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida", "flow": "1. Usuario desmarca favorito → 2. Sistema elimina relación",
         "post": "Track removido de favoritos", "alt": "2a. No existía → idempotente (RB-F03)", "rb": "RB-F03"},
        {"id": "CU-F04", "name": "Toggle favorito desde UI contextual", "actor": "Usuario Registrado Autenticado",
         "pre": "Usuario en contexto track (catálogo, detalle, recomendaciones)", "flow": "1. Usuario pulsa toggle → 2. Sistema invoca add/remove → 3. UI refleja estado",
         "post": "Estado favorito coherente UI/backend", "alt": "2a. Sin auth → redirect 001", "rb": "RB-F02, RB-F03"},
    ],
    "003": [
        {"id": "CU-C01", "name": "Listar artistas paginado", "actor": "Usuario Registrado",
         "pre": "Warehouse catálogo poblado", "flow": "1. Usuario abre listado artistas → 2. Sistema consulta dim con paginación → 3. UI muestra resultados",
         "post": "Lista artistas visible", "alt": "2a. Warehouse vacío → empty state", "rb": "RB-C01, RB-C03"},
        {"id": "CU-C02", "name": "Ver top artistas", "actor": "Usuario Registrado",
         "pre": "Datos agregados disponibles", "flow": "1. Usuario solicita ranking → 2. Sistema retorna top por popularidad",
         "post": "Ranking visible", "alt": "2a. Sin datos → empty state", "rb": "RB-C01"},
        {"id": "CU-C03", "name": "Listar géneros paginado", "actor": "Usuario Registrado",
         "pre": "Catálogo poblado", "flow": "1. Usuario abre géneros → 2. Sistema pagina dim géneros → 3. Opcional stats",
         "post": "Lista géneros visible", "alt": "2a. Filtro búsqueda vacío → lista completa paginada", "rb": "RB-C03"},
        {"id": "CU-C04", "name": "Listar tracks paginado", "actor": "Usuario Registrado",
         "pre": "Catálogo poblado", "flow": "1. Usuario abre tracks → 2. Sistema aplica filtros artista/género → 3. Retorna página",
         "post": "Lista tracks visible", "alt": "2a. Filtros sin match → empty state", "rb": "RB-C01, RB-C03"},
        {"id": "CU-C05", "name": "Ver detalle track", "actor": "Usuario Registrado",
         "pre": "Track ID válido", "flow": "1. Usuario abre detalle → 2. Sistema join artista/género/features → 3. UI renderiza",
         "post": "Detalle completo visible", "alt": "2a. ID inválido → 404", "rb": "RB-C01, RB-C05"},
        {"id": "CU-C06", "name": "Ver stats artista", "actor": "Usuario Registrado",
         "pre": "Artista existe", "flow": "1. Usuario solicita stats → 2. Sistema agrega métricas warehouse",
         "post": "Stats artista visibles", "alt": "2a. Artista inexistente → 404", "rb": "RB-C01"},
        {"id": "CU-S01", "name": "Buscar tracks por texto", "actor": "Usuario Registrado",
         "pre": "Query ≥ longitud mínima", "flow": "1. Usuario ingresa término → 2. Sistema busca en catálogo → 3. Retorna resultados",
         "post": "Resultados búsqueda visibles", "alt": "2a. Query corta → mensaje validación (RB-S01)", "rb": "RB-S01, RB-C04"},
        {"id": "CU-S02", "name": "Ver resultados búsqueda", "actor": "Usuario Registrado",
         "pre": "Búsqueda ejecutada", "flow": "1. Usuario revisa lista → 2. Selecciona track → 3. Navega detalle o play",
         "post": "Usuario accede track desde búsqueda", "alt": "2a. Sin resultados → empty state (FR-S04)", "rb": "RB-S01"},
        {"id": "CU-S03", "name": "Registrar búsqueda en historial", "actor": "Sistema Voxmetriks",
         "pre": "Búsqueda completada; usuario autenticado", "flow": "1. Sistema registra query local → 2. Hub warehouse complementa (005)",
         "post": "Entrada historial búsqueda disponible", "alt": "2a. Hub falla → solo local (005 FR-HI08)", "rb": "RB-S01"},
        {"id": "CU-AF01", "name": "Explorar distribución audio features", "actor": "Usuario Registrado",
         "pre": "Agregados warehouse disponibles", "flow": "1. Usuario abre vista features → 2. Sistema sirve agregados → 3. UI visualiza",
         "post": "Distribución visible", "alt": "2a. Sin agregados → empty state", "rb": "RB-AF01, RB-C02"},
        {"id": "CU-AF02", "name": "Consultar features de track", "actor": "Usuario Registrado",
         "pre": "Track con features en dim", "flow": "1. Usuario ve detalle → 2. Sistema expone features inline",
         "post": "Features track visibles", "alt": "2a. Sin features → sección vacía graceful", "rb": "RB-C02"},
    ],
    "004": [
        {"id": "CU-R01", "name": "Reproducir track desde contexto", "actor": "Usuario Registrado",
         "pre": "Track seleccionado con metadata válida (003/002)", "flow": "1. Usuario pulsa play → 2. Sistema resuelve demo audio URL → 3. Reproductor inicia",
         "post": "Audio en reproducción; barra activa", "alt": "2a. Asset demo ausente → error amigable (RB-R01)", "rb": "RB-R01, RB-R02"},
        {"id": "CU-R02", "name": "Pausar / reanudar", "actor": "Usuario Registrado",
         "pre": "Track cargado en reproductor", "flow": "1. Usuario toggle play/pause → 2. Sistema controla HTML5 Audio",
         "post": "Estado playing/paused coherente en UI", "alt": "—", "rb": "RB-R02"},
        {"id": "CU-R03", "name": "Ajustar volumen", "actor": "Usuario Registrado",
         "pre": "Reproductor activo", "flow": "1. Usuario ajusta volumen → 2. Sistema aplica y persiste local",
         "post": "Volumen persistido entre sesiones", "alt": "—", "rb": "RB-R04"},
        {"id": "CU-R04", "name": "Seek en progreso", "actor": "Usuario Registrado",
         "pre": "Duración conocida", "flow": "1. Usuario arrastra progreso → 2. Sistema seek audio",
         "post": "Posición actualizada", "alt": "2a. Duración desconocida → seek deshabilitado", "rb": "RB-R01"},
        {"id": "CU-R05", "name": "Siguiente / anterior en cola", "actor": "Usuario Registrado",
         "pre": "Cola con ≥1 track", "flow": "1. Usuario next/prev → 2. Sistema avanza cola",
         "post": "Track actual cambia", "alt": "2a. Cola vacía → no-op", "rb": "RB-R03"},
        {"id": "CU-R06", "name": "Activar shuffle / repeat", "actor": "Usuario Registrado",
         "pre": "Cola activa", "flow": "1. Usuario toggle modo → 2. Sistema aplica algoritmo cola",
         "post": "Modo shuffle/repeat activo", "alt": "—", "rb": "RB-R03"},
        {"id": "CU-R07", "name": "Reproducir cola completa", "actor": "Usuario Registrado",
         "pre": "Origen playlist/favoritos/lista (002/003)", "flow": "1. Usuario play all → 2. Sistema puebla cola → 3. Inicia primer track",
         "post": "Cola reproduciendo secuencialmente", "alt": "2a. Lista vacía → mensaje", "rb": "RB-R01"},
        {"id": "CU-R08", "name": "Ver now-playing expandido", "actor": "Usuario Registrado",
         "pre": "Track en reproducción o pausa", "flow": "1. Usuario expande player → 2. UI modal/sheet con controles ampliados",
         "post": "Vista expandida visible", "alt": "2a. Cierra → mini bar persiste", "rb": "RB-R02"},
        {"id": "CU-H01", "name": "Ver saludo personalizado", "actor": "Usuario Registrado",
         "pre": "Post-login en Home", "flow": "1. Home carga → 2. Sistema muestra saludo i18n time-based",
         "post": "Saludo visible", "alt": "—", "rb": "RB-H01"},
        {"id": "CU-H02", "name": "Ver KPIs resumen catálogo", "actor": "Usuario Registrado",
         "pre": "Stats API disponible o degradada", "flow": "1. Home fetch stats → 2. UI muestra KPIs",
         "post": "KPIs visibles", "alt": "2a. API falla → degradación parcial (FR-H06)", "rb": "RB-H02"},
        {"id": "CU-H03", "name": "Acceder shortcuts Home", "actor": "Usuario Registrado",
         "pre": "Home cargado", "flow": "1. Usuario navega secciones horizontales → 2. Accede playlists/recientes/top/géneros",
         "post": "Navegación o play desde shortcut", "alt": "—", "rb": "RB-H01"},
        {"id": "CU-H04", "name": "Continuar escuchando", "actor": "Usuario Registrado",
         "pre": "Historial local con entradas (004/005)", "flow": "1. Home muestra recientes → 2. Usuario retoma play",
         "post": "Reproducción desde historial", "alt": "2a. Historial vacío → sección oculta/empty", "rb": "RB-H01"},
    ],
    "005": [
        {"id": "CU-RC01", "name": "Ver listas recomendaciones", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida; agg scores o empty", "flow": "1. Usuario abre recommendations → 2. Sistema sirve listas con tracks",
         "post": "Listas visibles o empty state", "alt": "2a. Agg vacío → empty state (FR-RC06)", "rb": "RB-RC01, RB-RC04"},
        {"id": "CU-RC02", "name": "Ver recomendaciones user-aware", "actor": "Usuario Registrado Autenticado",
         "pre": "Bearer token en API", "flow": "1. API recibe auth → 2. Scores scoped user_id",
         "post": "Personalización aplicada", "alt": "2a. Sin token → genérico (RB-RC03)", "rb": "RB-RC02, RB-RC03"},
        {"id": "CU-RC03", "name": "Reproducir track recomendado", "actor": "Usuario Registrado Autenticado",
         "pre": "Track en lista", "flow": "1. Usuario play → 2. Invoca reproductor 004",
         "post": "Reproducción activa", "alt": "2a. Track inválido → error graceful", "rb": "RB-RC04"},
        {"id": "CU-RC04", "name": "Favoritar desde recomendaciones", "actor": "Usuario Registrado Autenticado",
         "pre": "Track en lista", "flow": "1. Usuario favorita → 2. Invoca API 002",
         "post": "Favorito persistido", "alt": "2a. Ya favorito → idempotente", "rb": "RB-RC04"},
        {"id": "CU-HI01", "name": "Ver historial escucha", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida", "flow": "1. Tab música → 2. Carga historial local por user key",
         "post": "Entradas escucha visibles", "alt": "2a. Vacío → empty state", "rb": "RB-HI01, RB-HI06"},
        {"id": "CU-HI02", "name": "Ver timeline actividad usuario", "actor": "Usuario Registrado Autenticado",
         "pre": "Hub API accesible", "flow": "1. Tab usuario → 2. Fetch hub → 3. Timeline scoped user",
         "post": "Actividad warehouse visible", "alt": "2a. 401 → solo local; 2b. Error → degradación", "rb": "RB-HI02, RB-HI04"},
        {"id": "CU-HI03", "name": "Ver historial búsquedas", "actor": "Usuario Registrado Autenticado",
         "pre": "Datos local y/o warehouse", "flow": "1. Tab búsqueda → 2. Merge local + hub",
         "post": "Búsquedas pasadas visibles", "alt": "2a. Duplicados → dedup en plan (RB-HI03)", "rb": "RB-HI03, RB-HI06"},
        {"id": "CU-HI04", "name": "Cambiar tabs historial", "actor": "Usuario Registrado Autenticado",
         "pre": "En pantalla history", "flow": "1. Usuario cambia tab → 2. UI carga contenido tab",
         "post": "Tab activo con counts", "alt": "—", "rb": "RB-HI06"},
        {"id": "CU-HI05", "name": "Limpiar historial local", "actor": "Usuario Registrado Autenticado",
         "pre": "Entradas locales existentes", "flow": "1. Usuario clear local → 2. Sistema elimina solo local",
         "post": "Local vacío; warehouse intacto", "alt": "2a. Sin entradas → no-op", "rb": "RB-HI05"},
    ],
    "006": [
        {"id": "CU-PF01", "name": "Ver pantalla perfil con identidad", "actor": "Usuario Registrado Autenticado",
         "pre": "Sesión válida (001)", "flow": "1. Usuario abre /users → 2. GET /users/me → 3. UI identidad sin secrets",
         "post": "Perfil identidad visible", "alt": "2a. Sin sesión → redirect login", "rb": "RB-PF01, RB-PF02"},
        {"id": "CU-PF02", "name": "Ver stats biblioteca en perfil", "actor": "Usuario Registrado Autenticado",
         "pre": "API perfil responde", "flow": "1. UI muestra favorites_count y playlists_count de API",
         "post": "Stats coherentes con 002", "alt": "2a. API error → mensaje retry", "rb": "RB-PF02"},
        {"id": "CU-PF03", "name": "Ver preview playlists recientes", "actor": "Usuario Registrado Autenticado",
         "pre": "Usuario tiene playlists", "flow": "1. API incluye preview → 2. UI muestra hasta 6 items",
         "post": "Preview visible", "alt": "2a. Sin playlists → empty state", "rb": "RB-PF02"},
        {"id": "CU-ST01", "name": "Cambiar tema", "actor": "Usuario Registrado Autenticado",
         "pre": "En settings general", "flow": "1. Usuario selecciona tema → 2. UI aplica y persiste local",
         "post": "Tema activo ≤1s", "alt": "2a. Conflicto dark_mode API → RB-ST05", "rb": "RB-ST03, RB-ST05"},
        {"id": "CU-ST02", "name": "Cambiar idioma ES/EN", "actor": "Usuario Registrado Autenticado",
         "pre": "En settings", "flow": "1. Usuario cambia idioma → 2. I18nService actualiza strings",
         "post": "Idioma persistido local", "alt": "—", "rb": "RB-ST02"},
        {"id": "CU-ST03", "name": "Actualizar prefs negocio vía API", "actor": "Usuario Registrado Autenticado",
         "pre": "Campos válidos 001 RB-010", "flow": "1. Usuario modifica toggles → 2. PATCH preferences → 3. Confirmación",
         "post": "preferences_json actualizado", "alt": "2a. PATCH inválido → error UI", "rb": "RB-ST01, RB-ST04"},
        {"id": "CU-ST04", "name": "Configurar toggles KPI locales", "actor": "Usuario Registrado Autenticado",
         "pre": "En settings", "flow": "1. Usuario toggle KPI → 2. UiPreferences persiste",
         "post": "Home respeta toggles (004)", "alt": "—", "rb": "RB-ST02"},
        {"id": "CU-ST05", "name": "Ver health API", "actor": "Usuario Registrado Autenticado",
         "pre": "Tab api settings", "flow": "1. Fetch /health → 2. UI status sin secrets",
         "post": "Health visible", "alt": "2a. Error → mensaje sin stack trace (RB-ST06)", "rb": "RB-ST06"},
        {"id": "CU-ST06", "name": "Ver warehouse/pipeline engineer", "actor": "Usuario Engineer",
         "pre": "Rol engineer 001 RB-015", "flow": "1. Engineer abre tabs → 2. UI estado datos read-only",
         "post": "Tabs visibles solo engineer", "alt": "2a. Usuario estándar → tabs ocultas", "rb": "RB-ST06"},
    ],
}


def render_cu_block(cu: dict) -> str:
    return f"""### {cu['id']}: {cu['name']}

| Campo | Descripción |
|-------|-------------|
| **ID** | {cu['id']} |
| **Actor principal** | {cu['actor']} |
| **Precondición** | {cu['pre']} |
| **Flujo principal** | {cu['flow']} |
| **Postcondición** | {cu['post']} |
| **Flujo alternativo** | {cu['alt']} |
| **Reglas de negocio** | {cu['rb']} |

"""


def render_section(spec_id: str) -> str:
    blocks = [render_cu_block(c) for c in CU_DEFS[spec_id]]
    return "## Casos de Uso\n\n" + "".join(blocks)


if __name__ == "__main__":
    for spec_id in CU_DEFS:
        d = list(ROOT.glob(f"{spec_id}-*"))[0]
        out = d / "_generated-cu-section.md"
        out.write_text(render_section(spec_id), encoding="utf-8")
        print(out)
