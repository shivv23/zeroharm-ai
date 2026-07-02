from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from config_loader import get_incident_records, get_compliance_checklist, get_regulatory_standards

DARK_BG = HexColor("#080c16")
ACCENT = HexColor("#00e5ff")
CRITICAL_C = HexColor("#ff1744")
SUCCESS_C = HexColor("#00e676")
DARK_CARD = HexColor("#0f1a2e")
ROW_ALT = HexColor("#1a2a44")
TEXT_PRI = HexColor("#e0e0e0")
TEXT_SEC = HexColor("#8899aa")
BORDER_C = HexColor("#1e3050")

_margin = 20 * mm
_page_width, _page_height = A4

STYLES = getSampleStyleSheet()
STYLES.add(ParagraphStyle("ReportTitle", fontName="Helvetica-Bold", fontSize=16,
                          textColor=ACCENT, spaceAfter=6))
STYLES.add(ParagraphStyle("ReportSubtitle", fontName="Helvetica", fontSize=9,
                          textColor=TEXT_SEC, spaceAfter=12))
STYLES.add(ParagraphStyle("SectionH", fontName="Helvetica-Bold", fontSize=11,
                          textColor=ACCENT, spaceBefore=12, spaceAfter=6))
STYLES.add(ParagraphStyle("BodyText", fontName="Helvetica", fontSize=8,
                          textColor=TEXT_PRI, leading=11))
STYLES.add(ParagraphStyle("SmallText", fontName="Helvetica", fontSize=7,
                          textColor=TEXT_SEC, leading=9))
STYLES.add(ParagraphStyle("StatusOK", fontName="Helvetica-Bold", fontSize=8,
                          textColor=SUCCESS_C))
STYLES.add(ParagraphStyle("StatusFail", fontName="Helvetica-Bold", fontSize=8,
                          textColor=CRITICAL_C))


def _make_table(headers, rows, col_widths=None):
    data = [[Paragraph(h, STYLES["SmallText"]) for h in headers]]
    for row in rows:
        data.append([Paragraph(str(c), STYLES["BodyText"]) for c in row])
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), DARK_CARD),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_C),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [DARK_CARD, ROW_ALT]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]
    if col_widths:
        style_cmds.append(("LEFTPADDING", (0, 0), (-1, -1), 4))
    t.setStyle(TableStyle(style_cmds))
    return t


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(TEXT_SEC)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(_margin, 12 * mm, "ZeroHarm AI — Regulatory Compliance Report")
    canvas.drawRightString(_page_width - _margin, 12 * mm,
                           f"Page {canvas.getPageNumber()} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.restoreState()


def generate_oisd_report(incidents: Optional[List] = None,
                          compliance_data: Optional[Dict] = None) -> BytesIO:
    return _generate_standard_report("OISD", "OISD-STD", incidents, compliance_data)


def generate_factory_act_report(incidents: Optional[List] = None,
                                 compliance_data: Optional[Dict] = None) -> BytesIO:
    return _generate_standard_report("Factory Act", "Factory Act 1948", incidents, compliance_data)


def generate_iso45001_report(incidents: Optional[List] = None,
                              compliance_data: Optional[Dict] = None) -> BytesIO:
    return _generate_standard_report("ISO 45001", "ISO 45001:2018", incidents, compliance_data)


def _generate_standard_report(standard_name: str, standard_ref: str,
                               incidents: Optional[List],
                               compliance_data: Optional[Dict]) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=_margin, rightMargin=_margin,
                            topMargin=20 * mm, bottomMargin=20 * mm)
    doc.title = f"ZeroHarm AI - {standard_name} Compliance Report"

    all_incidents = incidents or get_incident_records()
    checklist = get_compliance_checklist()
    standards = get_regulatory_standards()

    elements = []

    elements.append(Paragraph(f"{standard_name} Compliance Report", STYLES["ReportTitle"]))
    elements.append(Paragraph(
        f"Standard: {standard_ref} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        STYLES["ReportSubtitle"]))
    elements.append(HRFlowable(width="100%", color=BORDER_C, thickness=0.5))
    elements.append(Spacer(1, 6 * mm))

    if incidents:
        elements.append(Paragraph("1. Incident Summary", STYLES["SectionH"]))
        rows = []
        for inc in all_incidents:
            rows.append([
                inc.get("date", "N/A"), inc.get("type", "N/A").replace("_", " ").title(),
                inc.get("zone", "N/A"), inc.get("severity", "N/A").title(),
                inc.get("description", "")[:60],
            ])
        elements.append(_make_table(
            ["Date", "Type", "Zone", "Severity", "Description"], rows,
            col_widths=[55, 65, 40, 50, 150],
        ))
        elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph("2. Compliance Checklist", STYLES["SectionH"]))
    checklist_rows = []
    for item in checklist or []:
        status = item.get("status", "unknown")
        status_text = status.upper()
        checklist_rows.append([
            item.get("category", ""), item.get("requirement", ""),
            status_text,
        ])
    if checklist_rows:
        elements.append(_make_table(
            ["Category", "Requirement", "Status"], checklist_rows,
            col_widths=[80, 200, 50],
        ))
    else:
        elements.append(Paragraph("No compliance checklist data available.", STYLES["BodyText"]))

    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("3. Regulatory Standards Reference", STYLES["SectionH"]))
    std_rows = []
    for std_id, desc in (standards or {}).items():
        std_rows.append([std_id, desc[:80]])
    if std_rows:
        elements.append(_make_table(
            ["Standard ID", "Description"], std_rows,
            col_widths=[90, 250],
        ))

    elements.append(Spacer(1, 6 * mm))
    elements.append(HRFlowable(width="100%", color=BORDER_C, thickness=0.5))
    elements.append(Paragraph(
        "This report is auto-generated by ZeroHarm AI Platform. "
        "For verification, contact the safety department.",
        STYLES["SmallText"]))

    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
    buf.seek(0)
    return buf
