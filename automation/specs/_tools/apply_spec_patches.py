#!/usr/bin/env python3
"""Apply traceability and CU homogenization patches to spec.md files."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

US_RENAMES = {
    "002": [
        (r"### User Story 1 — Crear y gestionar playlists", "### User Story US-P01 — Crear y gestionar playlists"),
        (r"### User Story 2 — Gestionar tracks en playlist", "### User Story US-P02 — Gestionar tracks en playlist"),
        (r"### User Story 3 — Gestionar favoritos", "### User Story US-F01 — Gestionar favoritos"),
        (r"### User Story 4 — Reproducir desde biblioteca", "### User Story US-P03 — Reproducir desde biblioteca"),
    ],
    "003": [
        (r"### User Story 1 — Explorar artistas y géneros", "### User Story US-C01 — Explorar artistas y géneros"),
        (r"### User Story 2 — Explorar tracks y detalle", "### User Story US-C02 — Explorar tracks y detalle"),
        (r"### User Story 3 — Buscar música", "### User Story US-S01 — Buscar música"),
        (r"### User Story 4 — Explorar audio features", "### User Story US-AF01 — Explorar audio features"),
        (r"### User Story 5 — Acciones contextuales desde catálogo", "### User Story US-C03 — Acciones contextuales desde catálogo"),
    ],
    "004": [
        (r"### User Story 1 — Controles básicos reproductor", "### User Story US-R01 — Controles básicos reproductor"),
        (r"### User Story 2 — Cola y modos shuffle/repeat", "### User Story US-R02 — Cola y modos shuffle/repeat"),
        (r"### User Story 3 — Hub Home operativo", "### User Story US-H01 — Hub Home operativo"),
        (r"### User Story 4 — Now playing view", "### User Story US-R03 — Now playing view"),
        (r"### User Story 5 — Historial local escucha", "### User Story US-R04 — Historial local escucha"),
    ],
    "005": [
        (r"### User Story 1 — Ver recomendaciones personalizadas", "### User Story US-RC01 — Ver recomendaciones personalizadas"),
        (r"### User Story 2 — Reproducir y favoritar desde recomendaciones", "### User Story US-RC02 — Reproducir y favoritar desde recomendaciones"),
        (r"### User Story 3 — Historial de escucha unificado", "### User Story US-HI01 — Historial de escucha unificado"),
        (r"### User Story 4 — Historial actividad y búsquedas", "### User Story US-HI02 — Historial actividad y búsquedas"),
        (r"### User Story 5 — Acciones desde historial", "### User Story US-HI03 — Acciones desde historial"),
        (r"### User Story 6 — Limpiar historial local", "### User Story US-HI04 — Limpiar historial local"),
    ],
    "006": [
        (r"### User Story 1 — Ver perfil de usuario", "### User Story US-PF01 — Ver perfil de usuario"),
        (r"### User Story 2 — Tema e idioma", "### User Story US-ST01 — Tema e idioma"),
        (r"### User Story 3 — Preferencias de negocio sincronizadas", "### User Story US-ST02 — Preferencias de negocio sincronizadas"),
        (r"### User Story 4 — Toggles UI locales", "### User Story US-ST03 — Toggles UI locales"),
        (r"### User Story 5 — Transparencia sistema", "### User Story US-ST04 — Transparencia sistema"),
        (r"### User Story 6 — Settings engineer", "### User Story US-ST05 — Settings engineer"),
    ],
    "001": [
        (r"### User Story 1 - Registro", "### User Story US-01 — Registro"),
        (r"### User Story 2 - Inicio de sesión", "### User Story US-02 — Inicio de sesión"),
        (r"### User Story 3 - Consulta de perfil", "### User Story US-03 — Consulta de perfil"),
        (r"### User Story 4 - Actualización de preferencias", "### User Story US-04 — Actualización de preferencias"),
        (r"### User Story 5 - Cierre de sesión", "### User Story US-05 — Cierre de sesión"),
        (r"### User Story 6 - Protección de rutas", "### User Story US-06 — Protección de rutas"),
        (r"### User Story 7 - Acceso por rol Engineer", "### User Story US-07 — Acceso por rol Engineer"),
    ],
}


def replace_cu_section(content: str, new_cu: str) -> str:
    pattern = r"## Casos de Uso.*?(?=\n## User Scenarios)"
    return re.sub(pattern, new_cu.rstrip() + "\n\n---\n\n", content, count=1, flags=re.DOTALL)


def replace_traceability_matrix(content: str, appendix: str) -> str:
    # Remove old matrix sections between ### Matriz and next ## (not User Scenarios)
    content = re.sub(
        r"### Matriz de trazabilidad.*?(?=\n## )",
        "",
        content,
        count=1,
        flags=re.DOTALL,
    )
    content = re.sub(
        r"### Matriz\n.*?(?=\n## )",
        "",
        content,
        count=1,
        flags=re.DOTALL,
    )
    # Insert appendix after Trazabilidad Empresarial cadena table
    marker = "### Cadena oficial"
    if marker in content:
        # insert after first table block following cadena - simpler: before ## Actores
        content = re.sub(
            r"(## Trazabilidad Empresarial\n\n(?:### Cadena oficial.*?\n\n(?:\|.*?\n)+))",
            r"\1\n" + appendix + "\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        # 002 style - after eslabón table
        content = re.sub(
            r"(## Trazabilidad Empresarial\n\n(?:\| ID \| Eslabón.*?\n\n(?:\|.*?\n)+))",
            r"\1\n" + appendix + "\n",
            content,
            count=1,
            flags=re.DOTALL,
        )
    return content


def insert_fr_ca_if_missing(content: str, appendix: str) -> str:
    if "## Matriz CU → HU → FR → CA" in content:
        return content
    anchor = "## Criterios de Aceptación Globales"
    if anchor not in content:
        anchor = "## Success Criteria"
    fr_section = appendix.split("## Matriz CU → HU → FR → CA")[1]
    block = "## Matriz CU → HU → FR → CA" + fr_section.split("### Matriz de trazabilidad")[0]
    return content.replace(anchor, block + anchor)


def patch_spec(spec_id: str):
    d = list(ROOT.glob(f"{spec_id}-*"))[0]
    spec_path = d / "spec.md"
    content = spec_path.read_text(encoding="utf-8")
    appendix = (d / "traceability-appendix.md").read_text(encoding="utf-8")

    cu_file = d / "_generated-cu-section.md"
    if cu_file.exists():
        content = replace_cu_section(content, cu_file.read_text(encoding="utf-8"))

    content = replace_traceability_matrix(content, appendix)
    content = insert_fr_ca_if_missing(content, appendix)

    for old, new in US_RENAMES.get(spec_id, []):
        content = content.replace(old, new)

    # 006: split US-PF02 for preview - add note in US-PF01 maps to CU-PF01-02, US-PF02 for CU-PF03
    if spec_id == "006":
        content = content.replace(
            "**Maps to**: CU-PF01–PF03 | FR-PF01–FR-PF04 | M-11A",
            "**Maps to**: CU-PF01, CU-PF02 | FR-PF01–FR-PF04 | M-11A",
        )
        # Insert US-PF02 story after US-PF01 if not present
        if "### User Story US-PF02" not in content:
            pf02 = """
### User Story US-PF02 — Preview playlists recientes (Priority: P2)

Como **Usuario Registrado**, quiero **ver un preview de mis playlists recientes en perfil**, para **acceder rápidamente a mi biblioteca**.

**Independent Test**: Usuario con ≥1 playlist ve hasta 6 items en preview.

**Acceptance Scenarios**:

1. **Given** playlists en API preview, **When** perfil carga, **Then** muestra hasta 6 nombres.
2. **Given** sin playlists, **When** perfil carga, **Then** empty state sin error.

**Maps to**: CU-PF03 | FR-PF05 | M-11A

---

"""
            content = content.replace(
                "### User Story US-ST01 — Tema e idioma",
                pf02 + "### User Story US-ST01 — Tema e idioma",
            )

    # Add master ref in header area
    if "TRACEABILITY-MASTER" not in content:
        content = content.replace(
            "**Status**: Draft",
            "**Status**: Draft\n**Trazabilidad maestra**: [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md)",
        )

    spec_path.write_text(content, encoding="utf-8")
    print(f"Patched {spec_path}")


if __name__ == "__main__":
    import subprocess
    subprocess.run(["python", str(ROOT / "_tools" / "generate_cu_sections.py")], check=True)
    for sid in ["001", "002", "003", "004", "005", "006"]:
        patch_spec(sid)
