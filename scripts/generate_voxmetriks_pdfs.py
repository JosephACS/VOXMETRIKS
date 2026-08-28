"""Create the three handoff PDFs for the Voxmetriks demo.

The documents are intentionally written for a live demo: concise, visual, and
explicit about which data is synthetic.  They are generated with vector shapes
so the architecture diagrams stay crisp when printed or projected.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)

PAGE_W, PAGE_H = A4
AMBER = colors.HexColor("#C8750A")
AMBER_LIGHT = colors.HexColor("#E8A33D")
CREAM = colors.HexColor("#F3F1EA")
PAPER = colors.HexColor("#FFFDF8")
INK = colors.HexColor("#1A1712")
MUTED = colors.HexColor("#7A725F")
LINE = colors.HexColor("#E7D9C2")
DARK = colors.HexColor("#0B0C0B")
DARK_CARD = colors.HexColor("#17130C")
WHITE = colors.HexColor("#F5F2EA")


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="CoverKicker", parent=styles["Normal"], fontName="Helvetica-Bold",
    fontSize=8.5, leading=11, textColor=AMBER, tracking=1.4, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="CoverTitle", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=29, leading=31, textColor=INK, alignment=TA_LEFT, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=12, leading=17, textColor=MUTED, spaceAfter=14,
))
styles.add(ParagraphStyle(
    name="H1Vox", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=19, leading=22, textColor=INK, spaceBefore=5, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="H2Vox", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=12.5, leading=15, textColor=AMBER, spaceBefore=9, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="BodyVox", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.5, leading=14, textColor=INK, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="SmallVox", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8, leading=11, textColor=MUTED, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="CalloutVox", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=10, leading=14, textColor=INK, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="CodeVox", parent=styles["BodyText"], fontName="Courier",
    fontSize=8, leading=11, textColor=INK, backColor=colors.HexColor("#F7EFE2"),
    borderColor=LINE, borderWidth=0.5, borderPadding=6, spaceAfter=7,
))


def P(text: str, style: str = "BodyVox") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet_lines(items: Iterable[str]) -> list[Paragraph]:
    return [P(f"- {item}", "BodyVox") for item in items]


class RoundedBox(Flowable):
    def __init__(self, title: str, body: str, width: float = 53 * mm, height: float = 25 * mm,
                 fill=PAPER, stroke=LINE, title_color=INK, body_color=MUTED):
        super().__init__()
        self.width, self.height = width, height
        self.title, self.body = title, body
        self.fill, self.stroke = fill, stroke
        self.title_color, self.body_color = title_color, body_color

    def draw(self) -> None:
        c = self.canv
        c.setFillColor(self.fill)
        c.setStrokeColor(self.stroke)
        c.setLineWidth(0.8)
        c.roundRect(0, 0, self.width, self.height, 4 * mm, fill=1, stroke=1)
        c.setFillColor(self.title_color)
        c.setFont("Helvetica-Bold", 9.5)
        c.drawString(5 * mm, self.height - 8 * mm, self.title)
        c.setFillColor(self.body_color)
        c.setFont("Helvetica", 7.4)
        y = self.height - 14 * mm
        for line in self.body.split("\n"):
            c.drawString(5 * mm, y, line)
            y -= 4 * mm


class FlowDiagram(Flowable):
    def __init__(self, nodes: list[tuple[str, str]], arrows: list[tuple[int, int]],
                 width: float = 170 * mm, height: float = 88 * mm, dark: bool = False):
        super().__init__()
        self.width, self.height = width, height
        self.nodes, self.arrows, self.dark = nodes, arrows, dark

    def draw(self) -> None:
        c = self.canv
        bg = DARK if self.dark else CREAM
        c.setFillColor(bg)
        c.roundRect(0, 0, self.width, self.height, 5 * mm, fill=1, stroke=0)
        cols = 3
        rows = (len(self.nodes) + cols - 1) // cols
        box_w, box_h = 46 * mm, 22 * mm
        gap_x, gap_y = 8 * mm, 12 * mm
        origin_x, origin_y = 8 * mm, self.height - 30 * mm
        centers: list[tuple[float, float]] = []
        positions: list[tuple[float, float]] = []
        for i, (title, body) in enumerate(self.nodes):
            row, col = divmod(i, cols)
            x = origin_x + col * (box_w + gap_x)
            y = origin_y - row * (box_h + gap_y)
            positions.append((x, y))
            centers.append((x + box_w / 2, y + box_h / 2))
        # Draw connectors first so cards keep their text legible.
        for start, end in self.arrows:
            x1, y1 = centers[start]
            x2, y2 = centers[end]
            c.setStrokeColor(AMBER_LIGHT if self.dark else AMBER)
            c.setFillColor(AMBER_LIGHT if self.dark else AMBER)
            c.setLineWidth(1.3)
            c.line(x1, y1, x2, y2)
            import math
            angle = math.atan2(y2 - y1, x2 - x1)
            size = 3 * mm
            p1 = (x2 - size * math.cos(angle - 0.45), y2 - size * math.sin(angle - 0.45))
            p2 = (x2 - size * math.cos(angle + 0.45), y2 - size * math.sin(angle + 0.45))
            path = c.beginPath()
            path.moveTo(x2, y2)
            path.lineTo(*p1)
            path.lineTo(*p2)
            path.close()
            c.drawPath(path, fill=1, stroke=0)
        for i, (title, body) in enumerate(self.nodes):
            x, y = positions[i]
            fill = DARK_CARD if self.dark else PAPER
            stroke = colors.HexColor("#674419") if self.dark else LINE
            title_color = AMBER_LIGHT if self.dark else AMBER
            body_color = colors.HexColor("#B8AF9D") if self.dark else MUTED
            c.setFillColor(fill)
            c.setStrokeColor(stroke)
            c.setLineWidth(0.8)
            c.roundRect(x, y, box_w, box_h, 3 * mm, fill=1, stroke=1)
            c.setFillColor(title_color)
            c.setFont("Helvetica-Bold", 8.5)
            c.drawString(x + 4 * mm, y + box_h - 7 * mm, title)
            c.setFillColor(body_color)
            c.setFont("Helvetica", 6.8)
            yy = y + box_h - 12 * mm
            for line in body.split("\n")[:2]:
                c.drawString(x + 4 * mm, yy, line)
                yy -= 3.4 * mm


class Waveform(Flowable):
    def __init__(self, width: float = 160 * mm, height: float = 18 * mm, dark: bool = False):
        super().__init__()
        self.width, self.height, self.dark = width, height, dark

    def draw(self) -> None:
        c = self.canv
        c.setStrokeColor(AMBER_LIGHT if self.dark else AMBER)
        c.setFillColor(colors.Color(0.9, 0.55, 0.15, alpha=0.2))
        c.setLineWidth(1.2)
        path = c.beginPath()
        path.moveTo(0, self.height * 0.48)
        points = [
            (0.08, .70), (.16, .30), (.24, .72), (.32, .32), (.40, .62),
            (.48, .26), (.56, .70), (.64, .36), (.72, .64), (.80, .28),
            (.90, .68), (1.0, .48),
        ]
        for frac, y in points:
            path.curveTo(self.width * (frac - .035), self.height * y,
                         self.width * (frac - .015), self.height * y,
                         self.width * frac, self.height * y)
        path.lineTo(self.width, 0)
        path.lineTo(0, 0)
        path.close()
        c.drawPath(path, fill=1, stroke=1)


def header_footer(c: canvas.Canvas, doc: BaseDocTemplate, title: str, dark: bool = False) -> None:
    c.saveState()
    if dark:
        c.setFillColor(DARK)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        fg, subtle = WHITE, colors.HexColor("#A09A88")
    else:
        c.setFillColor(CREAM)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        fg, subtle = INK, MUTED
    c.setFillColor(fg)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(18 * mm, PAGE_H - 13 * mm, "VOXMETRIKS")
    c.setFillColor(AMBER if not dark else AMBER_LIGHT)
    c.setFont("Helvetica", 7)
    c.drawRightString(PAGE_W - 18 * mm, PAGE_H - 13 * mm, title.upper())
    c.setStrokeColor(colors.HexColor("#D7CBB8") if not dark else colors.HexColor("#2D261A"))
    c.setLineWidth(0.5)
    c.line(18 * mm, PAGE_H - 17 * mm, PAGE_W - 18 * mm, PAGE_H - 17 * mm)
    c.setFillColor(subtle)
    c.setFont("Helvetica", 7)
    c.drawString(18 * mm, 11 * mm, "Demo académico - datos sintéticos - 28 agosto 2026")
    c.drawRightString(PAGE_W - 18 * mm, 11 * mm, f"{doc.page}")
    c.restoreState()


def build_doc(path: Path, title: str, story: list[Flowable], dark: bool = False) -> None:
    doc = BaseDocTemplate(
        str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=24 * mm, bottomMargin=18 * mm, title=title, author="Voxmetriks",
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame,
                                       onPage=lambda c, d: header_footer(c, d, title, dark))])
    doc.build(story)


def cover(title: str, subtitle: str, label: str) -> list[Flowable]:
    return [
        Spacer(1, 20 * mm),
        P(label.upper(), "CoverKicker"),
        P(title, "CoverTitle"),
        P(subtitle, "CoverSubtitle"),
        Table([[P("Voxmetriks Studio", "CalloutVox"), P("Guía de demostración", "SmallVox")]],
              colWidths=[75 * mm, 75 * mm], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), PAPER), ("BOX", (0, 0), (-1, -1), 0.7, LINE),
                  ("ROUNDEDCORNERS", [5 * mm, 5 * mm, 5 * mm, 5 * mm]),
                  ("LEFTPADDING", (0, 0), (-1, -1), 7 * mm), ("RIGHTPADDING", (0, 0), (-1, -1), 7 * mm),
                  ("TOPPADDING", (0, 0), (-1, -1), 6 * mm), ("BOTTOMPADDING", (0, 0), (-1, -1), 6 * mm),
              ])),
        Spacer(1, 10 * mm),
        Waveform(),
        Spacer(1, 7 * mm),
        P("Una guía breve y visual para explicar el producto con claridad, sin vender humo y sin perder el encanto de la experiencia.", "BodyVox"),
        PageBreak(),
    ]


def architecture_pdf() -> None:
    story: list[Flowable] = cover(
        "Arquitectura de Voxmetriks",
        "Qué piezas existen, cómo se conectan y qué ocurre cuando una persona busca, escucha o analiza una canción.",
        "Documento 01 / arquitectura",
    )
    story += [
        P("La vista completa", "H1Vox"),
        P("Voxmetriks separa la experiencia de escucha de la operación empresarial. La interfaz Angular consume una API Python/FastAPI; esa API lee el warehouse analítico y coordina los proveedores de audio. Así podemos mostrar una app musical atractiva y, al mismo tiempo, un espacio de decisiones para una organización.", "BodyVox"),
        FlowDiagram([
            ("Usuario", "Busca, escucha y" "\n" "consulta su historial"),
            ("Angular", "Vistas, temas, player" "\n" "y navegación"),
            ("FastAPI", "Reglas, permisos y" "\n" "resolución de audio"),
            ("Warehouse", "DuckDB: catálogo," "\n" "eventos y métricas"),
            ("Spotify", "Playback completo" "\n" "si hay sesión"),
            ("Deezer", "Preview de 30 s" "\n" "sin autenticación"),
        ], [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5)]),
        Spacer(1, 4 * mm),
        P("Diagrama 1 - mapa de alto nivel", "SmallVox"),
        P("Flujo de reproducción", "H1Vox"),
        P("La app no depende de YouTube. Primero intenta usar Spotify Web Playback SDK cuando la sesión está conectada. Si no hay sesión o el track no se puede reproducir en Spotify, usa Deezer para un preview de 30 segundos. El aviso de preview se mantiene visible de forma discreta porque es parte de sus términos de uso.", "BodyVox"),
        FlowDiagram([
            ("1. Búsqueda", "Título, artista o" "\n" "género"),
            ("2. Resolver", "Normaliza y prueba" "\n" "fuentes"),
            ("Spotify SDK", "Sesión conectada" "\n" "-> pista completa"),
            ("Deezer API", "Fallback -> preview" "\n" "de 30 s"),
            ("Auto-skip", "Si falla todo, salta" "\n" "a la siguiente"),
            ("Player", "Controles propios y" "\n" "estado consistente"),
        ], [(0, 1), (1, 2), (1, 3), (2, 5), (3, 5), (1, 4)], dark=True),
        Spacer(1, 4 * mm),
        P("Diagrama 2 - reproducción y fallback", "SmallVox"),
        PageBreak(),
        P("Datos y módulos empresariales", "H1Vox"),
        P("El área empresarial comparte el mismo warehouse, pero aplica permisos por organización. Los módulos consultan tablas enfocadas en su dominio y dejan trazabilidad de cambios relevantes.", "BodyVox"),
        Table([
            [P("Capa", "CalloutVox"), P("Qué guarda o hace", "CalloutVox"), P("Ejemplo en la demo", "CalloutVox")],
            [P("Catálogo", "SmallVox"), P("Artistas, tracks, assets, releases y derechos", "SmallVox"), P("3 artistas, 4 assets, 2 releases", "SmallVox")],
            [P("Operación", "SmallVox"), P("Prospectos, oportunidades, campañas y soporte", "SmallVox"), P("5 prospectos, 3 oportunidades, 2 campañas", "SmallVox")],
            [P("Finanzas", "SmallVox"), P("Plan, facturas, pagos, ledger y perfil fiscal", "SmallVox"), P("2 facturas, 1 pago, 1 perfil fiscal", "SmallVox")],
            [P("Analítica", "SmallVox"), P("Reproducciones, KPIs, reportes y snapshots", "SmallVox"), P("Reporte generado y decisión registrada", "SmallVox")],
        ], colWidths=[31 * mm, 75 * mm, 52 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AMBER), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), PAPER), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])),
        Spacer(1, 8 * mm),
        P("Controles de confianza", "H2Vox"),
        *bullet_lines([
            "La cuenta admin entra con permisos de propietario y administrador en Voxmetriks Studio.",
            "La cola auto-skip evita que una canción sin fuente congele el reproductor.",
            "El proveedor activo queda registrado en el estado del player y en la trazabilidad técnica.",
            "La semilla empresarial está marcada como sintética y académica; no representa cobros reales.",
        ]),
        Spacer(1, 5 * mm),
        P("La base de datos, sin rodeos", "H2Vox"),
        P("La demo usa un solo archivo DuckDB: data/warehouse/voxmetrik.duckdb. Dentro viven tanto el estado operativo de la app como el warehouse analítico; no son dos bases de negocio separadas.", "BodyVox"),
        Table([
            [P("Grupo", "CalloutVox"), P("Qué significa", "CalloutVox")],
            [P("app_*", "SmallVox"), P("Cuentas, sesiones, organizaciones, roles, facturas, campañas, soporte y decisiones.", "SmallVox")],
            [P("dim_*", "SmallVox"), P("Catálogos ordenados: tracks, artistas, géneros, playlists y usuarios.", "SmallVox")],
            [P("fact_*", "SmallVox"), P("Hechos que ocurrieron: reproducciones, búsquedas, favoritos y actividad.", "SmallVox")],
            [P("agg_* / ctl_*", "SmallVox"), P("Métricas resumidas, controles de calidad y estado del pipeline.", "SmallVox")],
        ], colWidths=[34 * mm, 126 * mm], style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), AMBER), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, -1), PAPER), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
            ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])),
        PageBreak(),
        P("Resumen para una pregunta técnica", "H1Vox"),
        P("Si alguien pregunta 'qué hay debajo', la respuesta corta es: Angular en el navegador, FastAPI/Python en el backend, DuckDB como warehouse local de demostración, Spotify Web Playback SDK para sesiones conectadas y Deezer como respaldo de preview. La autorización se controla por usuario, organización y roles; el cache reduce llamadas repetidas y hace que la demo se sienta rápida.", "BodyVox"),
        P("La arquitectura en una frase", "H2Vox"),
        P("Una sola experiencia visual, dos espacios de valor: escuchar en personal y convertir señales de catálogo, audiencia y operación en decisiones dentro de la empresa.", "CalloutVox"),
        Spacer(1, 12 * mm),
        Waveform(width=160 * mm, dark=False),
        Spacer(1, 10 * mm),
        P("Nota de uso", "H2Vox"),
        P("Este PDF acompaña una demostración local. Los nombres, cifras y movimientos empresariales fueron preparados para enseñar el flujo de producto; no son datos de clientes ni transacciones productivas.", "SmallVox"),
    ]
    build_doc(OUT / "voxmetriks-arquitectura.pdf", "Arquitectura", story)


def internal_pdf() -> None:
    story: list[Flowable] = cover(
        "Cómo me explico Voxmetriks",
        "Una explicación sencilla para no perderme cuando tenga que contar qué hace la app y por qué importa.",
        "Documento 02 / explicación personal",
    )
    story += [
        P("La idea central", "H1Vox"),
        P("Voxmetriks es un lugar donde la música deja señales. En el espacio personal, una persona descubre y escucha. En el espacio de empresa, un equipo usa esas señales para saber qué funciona, qué necesita atención y cuál es el siguiente paso.", "BodyVox"),
        P("Yo lo pienso así", "H2Vox"),
        P("La app tiene dos caras que se entienden entre sí:", "BodyVox"),
        *bullet_lines([
            "Personal: catálogo, búsqueda, recomendaciones, favoritos e historial.",
            "Empresa: clientes, campañas, derechos, facturación, reportes y decisiones.",
            "Puente: la actividad musical se convierte en información útil para operar mejor.",
        ]),
        P("Cómo son las bases", "H2Vox"),
        P("Yo lo explicaría así: DuckDB es el archivo central de la demo. Ahí están los datos que la app necesita para funcionar y también los datos resumidos para los reportes.", "BodyVox"),
        *bullet_lines([
            "app_* = la operación: usuarios, sesiones, organizaciones, facturas, campañas y permisos.",
            "dim_* = el catálogo ordenado: canciones, artistas, géneros y playlists.",
            "fact_* = lo que ocurrió: reproducciones, búsquedas, favoritos y actividad.",
            "agg_* = los resúmenes que hacen rápidos los KPI y gráficos.",
        ]),
        P("PocketBase o Parquet solo sirven como fuente de entrada del pipeline; Airflow, si se usa, guarda su propia metadata. El audio no se guarda en la base: se reproduce desde Spotify o desde el preview de Deezer.", "SmallVox"),
        P("Qué pasa cuando pulso reproducir", "H1Vox"),
        Table([[P("1", "CoverKicker"), P("Busco o elijo una canción.", "BodyVox")],
               [P("2", "CoverKicker"), P("La app intenta reproducirla en Spotify si mi cuenta está conectada.", "BodyVox")],
               [P("3", "CoverKicker"), P("Si no puede, usa un preview de Deezer y me lo avisa de forma discreta.", "BodyVox")],
               [P("4", "CoverKicker"), P("Si ninguna fuente sirve, la app salta esa canción y continúa la cola.", "BodyVox")],
               [P("5", "CoverKicker"), P("Yo sigo viendo la misma portada, controles y estado; la complejidad queda detrás.", "BodyVox")]],
              colWidths=[15 * mm, 145 * mm], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, -1), PAPER), ("BOX", (0, 0), (-1, -1), 0.6, LINE),
                  ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                  ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                  ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
              ])),
        Spacer(1, 7 * mm),
        P("No tengo que explicar proveedores; tengo que explicar el resultado: la canción sigue sonando o la cola sigue avanzando.", "CalloutVox"),
        PageBreak(),
        P("Cómo leo el espacio de empresa", "H1Vox"),
        P("Cuando entro a Voxmetriks Studio, no estoy viendo otra app aislada. Estoy entrando a una sala de control: arriba veo el estado general y abajo puedo abrir el detalle que necesite.", "BodyVox"),
        FlowDiagram([
            ("Estado", "Qué está pasando" "\n" "ahora"),
            ("Clientes", "A quién acompaño" "\n" "y qué necesita"),
            ("Catálogo", "Qué se publicó," "\n" "revisó o bloqueó"),
            ("Campañas", "Qué acción está" "\n" "en marcha"),
            ("Finanzas", "Qué se facturó y" "\n" "qué falta"),
            ("Decisiones", "Qué hago después" "\n" "y quién lo toma"),
        ], [(0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (2, 5), (3, 5), (4, 5)]),
        Spacer(1, 5 * mm),
        P("Diagrama - de señal a decisión", "SmallVox"),
        P("Palabras que sí usaría", "H2Vox"),
        *bullet_lines([
            "'La app me ayuda a ver qué está pasando y qué debo hacer después.'",
            "'No es solo un reproductor: conecta catálogo, audiencia y operación.'",
            "'Los reportes no están de adorno; sirven para decidir con contexto.'",
        ]),
        P("Palabras que evitaría", "H2Vox"),
        *bullet_lines([
            "No prometería reproducción completa cuando la fuente es un preview de Deezer.",
            "No diría que los números son ventas reales: son datos de demostración.",
            "No diría que Spotify comparte una cuenta con usuarios nuevos; cada sesión se conecta por separado.",
        ]),
        PageBreak(),
        P("Mi respuesta de 30 segundos", "H1Vox"),
        P("Voxmetriks reúne la experiencia musical y la operación del negocio. Una persona puede descubrir y escuchar canciones; una organización puede entender su catálogo, sus campañas, sus clientes y sus resultados. La app intenta reproducir desde Spotify cuando hay sesión y usa Deezer como respaldo de preview cuando no la hay. Todo queda en una interfaz clara para pasar de escuchar a tomar decisiones.", "BodyVox"),
        P("Si me preguntan por la parte técnica", "H2Vox"),
        P("Diría: 'El front es Angular, el backend es Python con FastAPI y los datos de la demo viven en DuckDB. La reproducción usa Spotify Web Playback SDK y tiene un fallback de Deezer. Los roles de la organización protegen cada área y el cache evita repetir trabajo.'", "BodyVox"),
        Spacer(1, 10 * mm),
        Waveform(width=160 * mm),
    ]
    build_doc(OUT / "voxmetriks-flujo-interno.pdf", "Explicación personal", story)


def fair_pdf() -> None:
    story: list[Flowable] = cover(
        "Guion para la feria",
        "Un flujo corto para recibir a alguien, entender qué le interesa y mostrarle valor en menos de dos minutos.",
        "Documento 03 / presentación hablada",
    )
    story += [
        P("1. Romper el hielo", "H1Vox"),
        P("'Hola, esto es Voxmetriks. Antes de enseñarte botones, dime: ¿te interesa más descubrir música, conocer datos de artistas o ver cómo una empresa organiza su operación?'") ,
        P("La pregunta hace que la demo se sienta personal. Según su respuesta, elijo una de estas tres rutas:", "BodyVox"),
        Table([[P("Si dice...", "CalloutVox"), P("Yo muestro...", "CalloutVox"), P("Y digo...", "CalloutVox")],
               [P("'Me gusta escuchar'", "SmallVox"), P("Descubrir + player", "SmallVox"), P("'Busca una canción y mira cómo la experiencia se adapta.'", "SmallVox")],
               [P("'Soy artista'", "SmallVox"), P("Perfil, catálogo y reportes", "SmallVox"), P("'Aquí puedes ver tu catálogo y entender qué está funcionando.'", "SmallVox")],
               [P("'Tengo un negocio'", "SmallVox"), P("Espacio empresa", "SmallVox"), P("'Aquí el equipo convierte señales en tareas y decisiones.'", "SmallVox")]],
              colWidths=[42 * mm, 45 * mm, 73 * mm], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), AMBER), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("BACKGROUND", (0, 1), (-1, -1), PAPER), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 6),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
              ])),
        PageBreak(),
        P("2. Demo musical de 60 segundos", "H1Vox"),
        *bullet_lines([
            "Abro Descubrir y enseño una portada grande, una fila recomendada y la búsqueda.",
            "Busco una canción conocida por la persona y pulso reproducir.",
            "Señalo que los controles son de Voxmetriks y que el proveedor se resuelve detrás.",
            "Si aparece preview, digo: 'En esta sesión está entrando como preview de Deezer; con Spotify conectado la pista puede continuar completa.'",
            "Cambio de canción y enseño que la cola avanza sin quedarse congelada si una fuente no está disponible.",
        ]),
        P("Frase puente", "H2Vox"),
        P("'La parte bonita es escuchar; la parte útil es que cada interacción deja una señal que después se puede entender.'", "CalloutVox"),
        Spacer(1, 8 * mm),
        P("3. Demo empresarial de 60 segundos", "H1Vox"),
        *bullet_lines([
            "Cambio al espacio Voxmetriks Studio desde el selector, no desde un enlace perdido.",
            "Enseño el resumen: equipo, plan, facturación y accesos principales.",
            "Abro reportes y enseño un informe con periodo, métricas, gráfico y detalle.",
            "Abro campañas o clientes para mostrar que la información termina en una acción.",
        ]),
        PageBreak(),
        P("4. Preguntas que pueden hacerme", "H1Vox"),
        Table([[P("Pregunta", "CalloutVox"), P("Respuesta corta", "CalloutVox")],
               [P("¿De dónde sale la música?", "SmallVox"), P("'El catálogo se inspira en Spotify; la reproducción usa Spotify cuando hay sesión y Deezer como preview de respaldo.'", "SmallVox")],
               [P("¿Por qué no suena completa siempre?", "SmallVox"), P("'Porque Deezer entrega previews de 30 segundos sin autenticación. La app lo avisa y no bloquea la cola.'", "SmallVox")],
               [P("¿La cuenta admin es real?", "SmallVox"), P("'Es una cuenta de demo local con datos sintéticos preparados para enseñar el flujo.'", "SmallVox")],
               [P("¿Qué gana una empresa?", "SmallVox"), P("'Ordena catálogo, clientes, campañas, finanzas y reportes en un mismo espacio para decidir más rápido.'", "SmallVox")],
               [P("¿Un artista necesita cuenta?", "SmallVox"), P("'Para administrar su propio espacio y permisos, sí. La empresa puede gestionar varios perfiles según sus roles.'", "SmallVox")]],
              colWidths=[52 * mm, 108 * mm], style=TableStyle([
                  ("BACKGROUND", (0, 0), (-1, 0), AMBER), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                  ("BACKGROUND", (0, 1), (-1, -1), PAPER), ("GRID", (0, 0), (-1, -1), 0.5, LINE),
                  ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
                  ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 6),
                  ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
              ])),
        Spacer(1, 8 * mm),
        P("5. Cerrar con una invitación", "H1Vox"),
        P("'Si tuvieras que elegir una sola cosa para mejorar en tu proyecto musical - descubrir, entender a tu audiencia u ordenar la operación -, ¿cuál sería? Voxmetriks está pensado para acompañar justo ese siguiente paso.'", "BodyVox"),
        Spacer(1, 8 * mm),
        Waveform(width=160 * mm),
        P("Checklist antes de empezar", "H2Vox"),
        *bullet_lines([
            "Entrar con admin / VoxDemo2026! y seleccionar Voxmetriks Studio.",
            "Tener abierta la pantalla Descubrir y el espacio de empresa listo.",
            "Recordar: datos sintéticos, demo local, no prometer producción.",
        ]),
    ]
    build_doc(OUT / "voxmetriks-flujo-feria.pdf", "Guion de feria", story)


if __name__ == "__main__":
    architecture_pdf()
    internal_pdf()
    fair_pdf()
    for pdf in sorted(OUT.glob("voxmetriks-*.pdf")):
        print(f"created {pdf} ({pdf.stat().st_size} bytes)")
