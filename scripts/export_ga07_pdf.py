"""Build a printable HTML+PDF pack for GA07 from the master guides."""
from __future__ import annotations

import html
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [
    ROOT / "docs" / "GUIA-MAESTRA-VOXMETRIKS.md",
    ROOT / "docs" / "GUIA-PRESENTACION-NEGOCIO.md",
    ROOT / "docs" / "RESUMEN-RAPIDO-PRESENTACION.md",
    ROOT / "docs" / "AUDITORIA-CIERRE-FINAL.md",
    ROOT / "docs" / "INVENTARIO-FINAL-VERIFICADO.md",
    ROOT / "docs" / "MAPA-INTEGRAL-NEGOCIO.md",
    ROOT / "docs" / "GOLDEN-PATH-INTEGRAL.md",
    ROOT / "docs" / "DEUDAS-PRODUCCION.md",
]
OUT_DIR_CANDIDATES = [
    Path(r"C:\Users\Admin\Documents\Tarea\Ariosto\GA07"),
    Path(r"C:\Users\Admin\Documents\Tarea\Proyectos\Ariosto\GA07"),
    ROOT / "docs" / "export" / "GA07",
]


def md_to_html_simple(md: str) -> str:
    """Minimal Markdown → HTML (headings, lists, tables, code, paragraphs)."""
    lines = md.splitlines()
    out: list[str] = []
    in_code = False
    in_table = False
    list_type: str | None = None

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    def close_table() -> None:
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    def inline(s: str) -> str:
        s = html.escape(s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            close_list()
            close_table()
            if not in_code:
                in_code = True
                out.append("<pre><code>")
            else:
                in_code = False
                out.append("</code></pre>")
            i += 1
            continue
        if in_code:
            out.append(html.escape(line) + "\n")
            i += 1
            continue

        if re.match(r"^\|.*\|$", line):
            close_list()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if i + 1 < len(lines) and re.match(r"^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)+\|?$", lines[i + 1]):
                close_table()
                out.append("<table><thead><tr>")
                for c in cells:
                    out.append(f"<th>{inline(c)}</th>")
                out.append("</tr></thead><tbody>")
                in_table = True
                i += 2
                continue
            if in_table:
                if all(re.match(r"^:?-+:?$", c.replace(" ", "")) for c in cells):
                    i += 1
                    continue
                out.append("<tr>")
                for c in cells:
                    out.append(f"<td>{inline(c)}</td>")
                out.append("</tr>")
                i += 1
                continue

        close_table()

        if not line.strip():
            close_list()
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            close_list()
            level = len(m.group(1))
            out.append(f"<h{level}>{inline(m.group(2))}</h{level}>")
            i += 1
            continue

        if re.match(r"^---+$", line):
            close_list()
            out.append("<hr/>")
            i += 1
            continue

        m = re.match(r"^(\d+)\.\s+(.*)$", line)
        if m:
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{inline(m.group(2))}</li>")
            i += 1
            continue

        m = re.match(r"^[-*]\s+(.*)$", line)
        if m:
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        close_list()
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    close_list()
    close_table()
    return "\n".join(out)


def build_html() -> str:
    parts = [
        """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8"/>
<title>VOXMETRIKS — Guía Maestra y Presentación</title>
<style>
  @page { size: A4; margin: 18mm 14mm; }
  body { font-family: "Segoe UI", Calibri, Arial, sans-serif; font-size: 10.5pt; line-height: 1.35; color: #15202b; }
  h1 { font-size: 20pt; color: #0b3d2e; page-break-before: always; }
  h1:first-of-type { page-break-before: avoid; }
  h2 { font-size: 14pt; color: #0f5c45; margin-top: 1.2em; }
  h3 { font-size: 12pt; color: #1a6b52; }
  table { border-collapse: collapse; width: 100%; margin: 0.6em 0 1em; font-size: 9pt; }
  th, td { border: 1px solid #c5d0d6; padding: 4px 6px; vertical-align: top; }
  th { background: #e8f5ef; }
  code, pre { font-family: Consolas, "Courier New", monospace; font-size: 8.5pt; }
  pre { background: #f4f7f6; padding: 8px; overflow-x: auto; }
  .cover { text-align: center; padding: 40px 10px 20px; }
  .cover h1 { font-size: 26pt; page-break-before: avoid; }
  .muted { color: #445; font-size: 10pt; }
  .warn { background: #fff6e8; border-left: 4px solid #d48806; padding: 8px 10px; margin: 1em 0; }
</style>
</head>
<body>
<div class="cover">
  <h1>VOXMETRIKS</h1>
  <p><strong>Guía maestra · Presentación de negocio · Resumen rápido</strong></p>
  <p class="muted">Documento académico · inventarios verificados · pagos mock · sin contraseñas</p>
  <div class="warn">La contraseña de demos vive solo en la variable de entorno <code>DEMO_ACCOUNT_PASSWORD</code>. No se imprime aquí.</div>
</div>
"""
    ]
    for path in DOCS:
        md = path.read_text(encoding="utf-8")
        parts.append(f"<article data-src='{html.escape(path.name)}'>")
        parts.append(md_to_html_simple(md))
        parts.append("</article>")
    parts.append("</body></html>")
    return "\n".join(parts)


def find_browser() -> Path | None:
    candidates = [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Google/Chrome/Application/chrome.exe",
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
        / "Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
        / "Microsoft/Edge/Application/msedge.exe",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def main() -> int:
    html_doc = build_html()
    targets = [p for p in OUT_DIR_CANDIDATES]
    wrote = []
    for out_dir in targets:
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print("SKIP_DIR", out_dir, exc)
            continue
        html_path = out_dir / "GUIA-MAESTRA-VOXMETRIKS.html"
        html_path.write_text(html_doc, encoding="utf-8")
        # also copy markdown sources
        for d in DOCS:
            (out_dir / d.name).write_text(d.read_text(encoding="utf-8"), encoding="utf-8")
        wrote.append(str(html_path))

    browser = find_browser()
    pdf_paths = []
    if browser and wrote:
        for html_path_str in wrote:
            html_path = Path(html_path_str)
            pdf_path = html_path.with_suffix(".pdf")
            # file URL
            url = html_path.resolve().as_uri()
            cmd = [
                str(browser),
                "--headless=new",
                "--disable-gpu",
                f"--print-to-pdf={pdf_path}",
                "--no-pdf-header-footer",
                url,
            ]
            print("PRINT", " ".join(cmd))
            try:
                subprocess.run(cmd, check=False, timeout=120)
                if pdf_path.exists() and pdf_path.stat().st_size > 1000:
                    pdf_paths.append(str(pdf_path))
                    print("PDF_OK", pdf_path, pdf_path.stat().st_size)
                else:
                    print("PDF_FAIL", pdf_path)
            except Exception as exc:  # noqa: BLE001
                print("PDF_ERR", exc)
    else:
        print("NO_BROWSER_OR_HTML")

    print("HTML_WRITTEN", wrote)
    print("PDF_WRITTEN", pdf_paths)
    return 0 if pdf_paths else 1


if __name__ == "__main__":
    sys.exit(main())
