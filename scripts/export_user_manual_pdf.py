from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.utils import ImageReader

BASE_DIR = Path("/tmp/clm-manual")
SOURCE = BASE_DIR / "USER_MANUAL.md"
OUTPUT = BASE_DIR / "USER_MANUAL.pdf"
IMAGE_MAX_WIDTH = 6.6 * inch
IMAGE_MAX_HEIGHT = 4.6 * inch


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name="HandbookTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        name="HandbookSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=10,
    )
)
styles.add(
    ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#111827"),
    )
)
styles.add(
    ParagraphStyle(
        name="SubHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        spaceBefore=8,
        spaceAfter=6,
        textColor=colors.HexColor("#1f2937"),
    )
)
styles.add(
    ParagraphStyle(
        name="SubSubHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=13,
        spaceBefore=6,
        spaceAfter=4,
        textColor=colors.HexColor("#374151"),
    )
)
styles.add(
    ParagraphStyle(
        name="BodyTextHandbook",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    )
)
styles.add(
    ParagraphStyle(
        name="BulletHandbook",
        parent=styles["BodyTextHandbook"],
        leftIndent=12,
        firstLineIndent=0,
        bulletIndent=0,
    )
)
styles.add(
    ParagraphStyle(
        name="CaptionHandbook",
        parent=styles["Italic"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#6b7280"),
        spaceAfter=8,
    )
)


def inline_markup(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return escaped


def paragraph(text: str, style="BodyTextHandbook"):
    return Paragraph(inline_markup(text), styles[style])


def parse_table(lines: list[str]) -> Table:
    rows = []
    for raw in lines:
        stripped = raw.strip().strip("|")
        cells = [cell.strip() for cell in stripped.split("|")]
        if cells and all(set(cell) <= {"-"} for cell in cells):
            continue
        rows.append(cells)

    if not rows:
        return Table([[""]])

    col_count = max(len(row) for row in rows)
    normalized = [row + [""] * (col_count - len(row)) for row in rows]
    table = Table(normalized, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.8),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#9ca3af")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def parse_image(line: str):
    start = line.find("[")
    mid = line.find("](")
    end = line.rfind(")")
    alt = line[start + 1:mid]
    path = line[mid + 2:end]
    image_path = (BASE_DIR / path).resolve()
    if not image_path.exists():
        return paragraph(f"Missing image: {path}")

    img = Image(str(image_path))
    try:
        reader = ImageReader(str(image_path))
        iw, ih = reader.getSize()
        scale = min(IMAGE_MAX_WIDTH / iw, IMAGE_MAX_HEIGHT / ih, 1)
        img.drawWidth = iw * scale
        img.drawHeight = ih * scale
    except Exception:
        img.drawWidth = IMAGE_MAX_WIDTH
        img.drawHeight = IMAGE_MAX_HEIGHT
    return [img, Spacer(1, 4), Paragraph(inline_markup(alt), styles["CaptionHandbook"])]


def parse_markdown(md_text: str):
    blocks = []
    lines = md_text.splitlines()
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        if stripped == "---":
            blocks.append(Spacer(1, 8))
            i += 1
            continue

        if stripped.startswith("# "):
            blocks.append(paragraph(stripped[2:], "HandbookTitle"))
            i += 1
            continue

        if stripped.startswith("## "):
            blocks.append(paragraph(stripped[3:], "SectionHeading"))
            i += 1
            continue

        if stripped.startswith("### "):
            blocks.append(paragraph(stripped[4:], "SubHeading"))
            i += 1
            continue

        if stripped.startswith("#### "):
            blocks.append(paragraph(stripped[5:], "SubSubHeading"))
            i += 1
            continue

        if stripped.startswith("![") and "](" in stripped and stripped.endswith(")"):
            blocks.extend(parse_image(stripped))
            i += 1
            continue

        if stripped.startswith("|"):
            table_lines = [stripped]
            i += 1
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            blocks.append(parse_table(table_lines))
            blocks.append(Spacer(1, 8))
            continue

        if stripped.startswith("- "):
            items = []
            while i < len(lines):
                current = lines[i].strip()
                if not current.startswith("- "):
                    break
                items.append(ListItem(paragraph(current[2:], "BodyTextHandbook")))
                i += 1
            blocks.append(ListFlowable(items, bulletType="bullet", leftIndent=14))
            blocks.append(Spacer(1, 4))
            continue

        if re_numbered(stripped):
            items = []
            while i < len(lines) and re_numbered(lines[i].strip()):
                current = lines[i].strip()
                dot = current.find(". ")
                items.append(ListItem(paragraph(current[dot + 2:], "BodyTextHandbook")))
                i += 1
            blocks.append(ListFlowable(items, bulletType="1", leftIndent=14))
            blocks.append(Spacer(1, 4))
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].rstrip()
            nxt_stripped = nxt.strip()
            if not nxt_stripped:
                i += 1
                break
            if nxt_stripped.startswith(("#", "|", "- ", "![")) or re_numbered(nxt_stripped) or nxt_stripped == "---":
                break
            para_lines.append(nxt_stripped)
            i += 1
        blocks.append(paragraph(" ".join(para_lines)))

    return blocks


def re_numbered(text: str) -> bool:
    if ". " not in text:
        return False
    prefix = text.split(". ", 1)[0]
    return prefix.isdigit()


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(A4[0] - 1.5 * cm, 1.0 * cm, f"Page {doc.page}")
    canvas.restoreState()


def build_pdf():
    content = SOURCE.read_text(encoding="utf-8")
    flowables = []

    flowables.append(paragraph("LEGAL CLM HANDBOOK", "HandbookTitle"))
    flowables.append(paragraph("User Manual for PT Perfect Companion Indonesia", "HandbookSubtitle"))
    flowables.append(Spacer(1, 10))
    flowables.extend(parse_markdown(content))

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.4 * cm,
        title="LEGAL CLM HANDBOOK",
        author="CLM Project Team",
    )

    doc.build(flowables, onFirstPage=add_page_number, onLaterPages=add_page_number)


if __name__ == "__main__":
    build_pdf()
    print(f"Created {OUTPUT}")
