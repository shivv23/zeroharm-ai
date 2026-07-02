from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Frame, PageTemplate, BaseDocTemplate, KeepTogether,
)
from reportlab.platypus.frames import Frame
from reportlab.platypus.doctemplate import PageTemplate
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib import colors

from config_loader import get_agent_settings


DARK_BG = HexColor("#080c16")
ACCENT = HexColor("#00e5ff")
CRITICAL_COLOR = HexColor("#ff1744")
WARNING_COLOR = HexColor("#ff9100")
SUCCESS_COLOR = HexColor("#00e676")
DARK_CARD = HexColor("#0f1a2e")
ROW_ALT = HexColor("#1a2a44")
HEADER_BG = HexColor("#0d1a33")
TEXT_PRIMARY = HexColor("#e0e0e0")
TEXT_SECONDARY = HexColor("#8899aa")
TEXT_ACCENT = ACCENT
BORDER_COLOR = HexColor("#1e3050")

_page_width, _page_height = A4
_margin = 20 * mm


class _NumberedCanvas:
    def __init__(self, canvas, doc):
        canvas._saved = None
        self.canvas = canvas

    def __getattr__(self, name):
        return getattr(self.canvas, name)

    def showPage(self):
        self.canvas.saveState()
        self.canvas.setFont("Helvetica", 8)
        self.canvas.setFillColor(TEXT_SECONDARY)
        page_num = self.canvas.getPageNumber()
        text = f"Page {page_num}"
        self.canvas.drawRightString(_page_width - _margin, 12 * mm, text)
        self.canvas.drawString(_margin, 12 * mm, _REPORT_CFG.get("confidentiality_label", "CONFIDENTIAL"))
        self.canvas.restoreState()
        self.canvas.showPage()


class ReportGenerator:
    def __init__(self):
        self._styles = _build_styles()
        self._cfg = get_agent_settings().get("report_generation", {})

    def generate_compliance_report(self, compliance_data: Dict, plant_name: str, timestamp: str) -> bytes:
        buf = BytesIO()
        doc = BaseDocTemplate(
            buf, pagesize=A4,
            leftMargin=_margin, rightMargin=_margin,
            topMargin=15 * mm, bottomMargin=22 * mm,
        )
        frame = Frame(_margin, 22 * mm, _page_width - 2 * _margin, _page_height - 37 * mm, id="main")
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_footer_drawer)])

        story = []
        story.append(_build_header("COMPLIANCE REPORT"))
        story.append(Spacer(1, 4 * mm))
        story.append(_build_meta_block(plant_name, timestamp))
        story.append(Spacer(1, 6 * mm))

        score = compliance_data.get("overall_compliance_score", 0)
        story.append(_build_score_display(score))
        story.append(Spacer(1, 6 * mm))

        cat_scores = compliance_data.get("category_scores", {})
        if cat_scores:
            story.append(_build_section_title("Category Breakdown"))
            story.append(_build_category_table(cat_scores))
            story.append(Spacer(1, 6 * mm))

        violations = compliance_data.get("violations", [])
        critical_findings = compliance_data.get("critical_findings", [])
        max_v = self._cfg.get("max_violations_in_report", 50)

        if critical_findings:
            story.append(_build_section_title("Critical Findings"))
            story.append(_build_violation_list(critical_findings, is_critical=True))
            story.append(Spacer(1, 6 * mm))

        if violations:
            story.append(_build_section_title(f"Violations (showing up to {max_v})"))
            story.append(_build_violation_list(violations[:max_v], is_critical=False))
            story.append(Spacer(1, 6 * mm))

        if self._cfg.get("include_recommendations", True):
            recs = compliance_data.get("recommendations", [])
            story.append(_build_section_title("Recommendations"))
            story.append(_build_recommendations(recs))
            story.append(Spacer(1, 6 * mm))

        doc.build(story, canvasmaker=lambda c, d: _NumberedCanvas(canvasmaker(c, d)))
        return buf.getvalue()

    def generate_incident_report(self, incident_data: Dict, plant_name: str) -> bytes:
        buf = BytesIO()
        doc = BaseDocTemplate(
            buf, pagesize=A4,
            leftMargin=_margin, rightMargin=_margin,
            topMargin=15 * mm, bottomMargin=22 * mm,
        )
        frame = Frame(_margin, 22 * mm, _page_width - 2 * _margin, _page_height - 37 * mm, id="main")
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_footer_drawer)])

        story = []
        story.append(_build_header("INCIDENT REPORT"))
        story.append(Spacer(1, 4 * mm))
        story.append(_build_meta_block(plant_name, datetime.now().isoformat()))
        story.append(Spacer(1, 6 * mm))

        report_id = incident_data.get("report_id", "N/A")
        details = incident_data.get("details", {})
        classification = incident_data.get("classification", self._cfg.get("confidentiality_label", "CONFIDENTIAL"))

        story.append(_build_classification_banner(classification))
        story.append(Spacer(1, 4 * mm))

        incident_type = details.get("incident_type", "N/A")
        severity = incident_data.get("severity", "N/A")
        zone = details.get("location", "N/A")
        event_time = f"{details.get('date', 'N/A')} {details.get('time', 'N/A')}"

        story.append(_build_section_title("Incident Details"))
        story.append(_build_incident_details_table(report_id, incident_type, severity, zone, event_time))
        story.append(Spacer(1, 6 * mm))

        timeline = incident_data.get("timeline_of_events", [])
        if timeline:
            story.append(_build_section_title("Response Timeline"))
            story.append(_build_timeline_table(timeline))
            story.append(Spacer(1, 6 * mm))

        reg_refs = details.get("regulatory_references", [])
        if reg_refs:
            story.append(_build_section_title("Regulatory References"))
            story.append(_build_regulatory_refs(reg_refs))
            story.append(Spacer(1, 6 * mm))

        doc.build(story, canvasmaker=lambda c, d: _NumberedCanvas(canvasmaker(c, d)))
        return buf.getvalue()

    def generate_risk_report(self, risk_data: Dict, plant_state: Dict, timestamp: str) -> bytes:
        buf = BytesIO()
        doc = BaseDocTemplate(
            buf, pagesize=A4,
            leftMargin=_margin, rightMargin=_margin,
            topMargin=15 * mm, bottomMargin=22 * mm,
        )
        frame = Frame(_margin, 22 * mm, _page_width - 2 * _margin, _page_height - 37 * mm, id="main")
        doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=_footer_drawer)])

        plant_name = plant_state.get("plant_name", self._cfg.get("company_name", "Plant"))

        story = []
        story.append(_build_header("RISK ASSESSMENT REPORT"))
        story.append(Spacer(1, 4 * mm))
        story.append(_build_meta_block(plant_name, timestamp))
        story.append(Spacer(1, 6 * mm))

        risk_score = risk_data.get("risk_score", 0)
        severity = risk_data.get("severity", "normal")
        story.append(_build_risk_score_display(risk_score, severity))
        story.append(Spacer(1, 6 * mm))

        alerts = risk_data.get("alerts", [])
        if alerts:
            story.append(_build_section_title(f"Active Alerts ({len(alerts)})"))
            story.append(_build_alerts_table(alerts))
            story.append(Spacer(1, 6 * mm))

        zone_risks = plant_state.get("zone_risk_scores", {})
        if zone_risks:
            story.append(_build_section_title("Zone Risk Breakdown"))
            story.append(_build_zone_risk_table(zone_risks))
            story.append(Spacer(1, 6 * mm))

        permits = plant_state.get("active_permits", [])
        if permits:
            story.append(_build_section_title(f"Active Permits ({len(permits)})"))
            story.append(_build_permit_summary_table(permits))
            story.append(Spacer(1, 6 * mm))

        doc.build(story, canvasmaker=lambda c, d: _NumberedCanvas(canvasmaker(c, d)))
        return buf.getvalue()


def _build_styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("ZHHeader", fontName="Helvetica-Bold", fontSize=22, textColor=ACCENT, spaceAfter=0, leading=26))
    ss.add(ParagraphStyle("ZHTitle", fontName="Helvetica-Bold", fontSize=14, textColor=ACCENT, spaceAfter=4, leading=18))
    ss.add(ParagraphStyle("ZHSection", fontName="Helvetica-Bold", fontSize=12, textColor=ACCENT, spaceBefore=6, spaceAfter=4, leading=16))
    ss.add(ParagraphStyle("ZHSmall", fontName="Helvetica", fontSize=8, textColor=TEXT_SECONDARY, leading=10))
    ss.add(ParagraphStyle("ZHBody", fontName="Helvetica", fontSize=9, textColor=TEXT_PRIMARY, leading=13))
    ss.add(ParagraphStyle("ZHBold", fontName="Helvetica-Bold", fontSize=9, textColor=TEXT_PRIMARY, leading=13))
    ss.add(ParagraphStyle("ZHScore", fontName="Helvetica-Bold", fontSize=36, textColor=ACCENT, leading=42, alignment=TA_CENTER))
    ss.add(ParagraphStyle("ZHSmallBold", fontName="Helvetica-Bold", fontSize=8, textColor=TEXT_PRIMARY, leading=10))
    ss.add(ParagraphStyle("ZHMeta", fontName="Helvetica", fontSize=8, textColor=TEXT_SECONDARY, leading=11))
    ss.add(ParagraphStyle("ZHBanner", fontName="Helvetica-Bold", fontSize=11, textColor=white, leading=14, alignment=TA_CENTER))
    return ss


def _footer_drawer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_SECONDARY)
    text = f"Page {canvas.getPageNumber()}"
    canvas.drawRightString(_page_width - _margin, 12 * mm, text)
    canvas.drawString(_margin, 12 * mm, "CONFIDENTIAL")
    canvas.restoreState()


def canvasmaker(c, d):
    c._doc = d
    return c


def _build_header(subtitle):
    tbl = Table(
        [[Paragraph("ZeroHarm AI", _build_styles()["ZHHeader"]), Paragraph(subtitle, _build_styles()["ZHTitle"])]],
        colWidths=[80 * mm, None],
    )
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements = [tbl]
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=0, spaceBefore=2))
    return KeepTogether(elements)


def _build_meta_block(plant_name, timestamp):
    try:
        dt = datetime.fromisoformat(timestamp)
        ts = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        ts = str(timestamp)
    data = [[Paragraph(f"Plant: <b>{plant_name}</b>", _build_styles()["ZHMeta"]),
             Paragraph(f"Generated: {ts}", _build_styles()["ZHMeta"])]]
    tbl = Table(data, colWidths=[85 * mm, 85 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    return tbl


def _build_section_title(text):
    elements = [Paragraph(text, _build_styles()["ZHSection"])]
    elements.append(HRFlowable(width="100%", thickness=0.5, color=ACCENT, spaceAfter=2, spaceBefore=0))
    return KeepTogether(elements)


def _build_score_display(score):
    if score >= 80:
        color = SUCCESS_COLOR
        label = "GOOD"
    elif score >= 60:
        color = WARNING_COLOR
        label = "WARNING"
    else:
        color = CRITICAL_COLOR
        label = "CRITICAL"
    score_text = f'<font color="{color.hexval()}">{score:.1f}%</font>'
    data = [
        [Paragraph(score_text, _build_styles()["ZHScore"])],
        [Paragraph(f"Overall Compliance Score — {label}", _build_styles()["ZHSmall"])],
    ]
    tbl = Table(data, colWidths=[150 * mm])
    tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, 0), DARK_CARD),
        ("BACKGROUND", (0, 1), (-1, 1), DARK_BG),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _build_risk_score_display(score, severity):
    sev_colors = {"critical": CRITICAL_COLOR, "high": WARNING_COLOR, "warning": WARNING_COLOR,
                  "medium": WARNING_COLOR, "normal": SUCCESS_COLOR, "info": TEXT_SECONDARY}
    color = sev_colors.get(severity, TEXT_SECONDARY)
    score_val = score * 100
    data = [
        [Paragraph(f'<font color="{color.hexval()}">{score_val:.1f}%</font>', _build_styles()["ZHScore"])],
        [Paragraph(f"Risk Score — {severity.upper()}", _build_styles()["ZHSmall"])],
    ]
    tbl = Table(data, colWidths=[150 * mm])
    tbl.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, 0), DARK_CARD),
        ("BACKGROUND", (0, 1), (-1, 1), DARK_BG),
        ("TOPPADDING", (0, 0), (-1, 0), 12),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tbl


def _build_category_table(cat_scores):
    header = [Paragraph("Category", _build_styles()["ZHSmallBold"]),
              Paragraph("Score", _build_styles()["ZHSmallBold"]),
              Paragraph("Status", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for cat_id, cat in cat_scores.items():
        score_pct = cat.get("score", 0) * 100
        status = "PASS" if score_pct >= 70 else "FAIL"
        color = SUCCESS_COLOR if score_pct >= 70 else CRITICAL_COLOR
        rows.append([
            Paragraph(cat.get("title", cat_id), _build_styles()["ZHBody"]),
            Paragraph(f"{score_pct:.1f}%", _build_styles()["ZHBody"]),
            Paragraph(f'<font color="{color.hexval()}">{status}</font>', _build_styles()["ZHBody"]),
        ])
    col_w = [70 * mm, 35 * mm, 45 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_violation_list(findings, is_critical=False):
    if is_critical:
        header = [Paragraph("Category", _build_styles()["ZHSmallBold"]),
                  Paragraph("Finding", _build_styles()["ZHSmallBold"]),
                  Paragraph("Standard", _build_styles()["ZHSmallBold"])]
    else:
        header = [Paragraph("Category", _build_styles()["ZHSmallBold"]),
                  Paragraph("Check", _build_styles()["ZHSmallBold"]),
                  Paragraph("Severity", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for f in findings[:50]:
        if is_critical:
            rows.append([
                Paragraph(f.get("category", ""), _build_styles()["ZHBody"]),
                Paragraph(f.get("check", f.get("detail", "")), _build_styles()["ZHBody"]),
                Paragraph(f.get("standard", ""), _build_styles()["ZHBody"]),
            ])
        else:
            sev = f.get("severity", "info")
            sev_color = CRITICAL_COLOR if sev == "critical" else WARNING_COLOR if sev in ("high", "warning") else TEXT_PRIMARY
            rows.append([
                Paragraph(f.get("category", ""), _build_styles()["ZHBody"]),
                Paragraph(f.get("check", ""), _build_styles()["ZHBody"]),
                Paragraph(f'<font color="{sev_color.hexval()}">{sev.upper()}</font>', _build_styles()["ZHBody"]),
            ])
    col_w = [50 * mm, 60 * mm, 40 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_recommendations(recs):
    if not recs:
        recs = ["No recommendations at this time."]
    data = []
    for i, rec in enumerate(recs, 1):
        data.append([Paragraph(f"{i}. {rec}", _build_styles()["ZHBody"])])
    tbl = Table(data, colWidths=[150 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _build_classification_banner(text):
    data = [[Paragraph(text, _build_styles()["ZHBanner"])]]
    tbl = Table(data, colWidths=[150 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CRITICAL_COLOR),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, CRITICAL_COLOR),
    ]))
    return tbl


def _build_incident_details_table(report_id, incident_type, severity, zone, event_time):
    label_s = _build_styles()["ZHSmallBold"]
    body_s = _build_styles()["ZHBody"]
    data = [
        [Paragraph("Report ID", label_s), Paragraph(report_id, body_s),
         Paragraph("Incident Type", label_s), Paragraph(incident_type, body_s)],
        [Paragraph("Severity", label_s), Paragraph(severity, body_s),
         Paragraph("Location", label_s), Paragraph(zone, body_s)],
        [Paragraph("Date/Time", label_s), Paragraph(event_time, body_s), Paragraph("", label_s), Paragraph("", body_s)],
    ]
    tbl = Table(data, colWidths=[30 * mm, 45 * mm, 30 * mm, 45 * mm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_CARD),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    return tbl


def _build_timeline_table(timeline):
    header = [Paragraph("Time", _build_styles()["ZHSmallBold"]),
              Paragraph("Event", _build_styles()["ZHSmallBold"]),
              Paragraph("Details", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for entry in timeline:
        t = entry.get("time", "")
        try:
            dt = datetime.fromisoformat(t)
            t = dt.strftime("%H:%M:%S")
        except (ValueError, TypeError):
            pass
        rows.append([
            Paragraph(t, _build_styles()["ZHBody"]),
            Paragraph(entry.get("event", ""), _build_styles()["ZHBody"]),
            Paragraph(entry.get("details", ""), _build_styles()["ZHBody"]),
        ])
    col_w = [30 * mm, 50 * mm, 70 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_regulatory_refs(refs):
    data = []
    for r in refs:
        data.append([Paragraph(f"&bull;  {r}", _build_styles()["ZHBody"])])
    tbl = Table(data, colWidths=[150 * mm])
    tbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tbl


def _build_alerts_table(alerts):
    header = [Paragraph("Type", _build_styles()["ZHSmallBold"]),
              Paragraph("Message", _build_styles()["ZHSmallBold"]),
              Paragraph("Severity", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for a in alerts[:30]:
        sev = a.get("severity", "info")
        sev_color = CRITICAL_COLOR if sev == "critical" else WARNING_COLOR if sev in ("high", "warning") else ACCENT
        rows.append([
            Paragraph(a.get("type", ""), _build_styles()["ZHBody"]),
            Paragraph(a.get("message", ""), _build_styles()["ZHBody"]),
            Paragraph(f'<font color="{sev_color.hexval()}">{sev.upper()}</font>', _build_styles()["ZHBody"]),
        ])
    col_w = [40 * mm, 80 * mm, 30 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_zone_risk_table(zone_risks):
    header = [Paragraph("Zone", _build_styles()["ZHSmallBold"]),
              Paragraph("Risk Score", _build_styles()["ZHSmallBold"]),
              Paragraph("Status", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for zid, zscore in sorted(zone_risks.items()):
        pct = zscore * 100
        if pct >= 70:
            status = "CRITICAL"
            color = CRITICAL_COLOR
        elif pct >= 40:
            status = "WARNING"
            color = WARNING_COLOR
        else:
            status = "NORMAL"
            color = SUCCESS_COLOR
        rows.append([
            Paragraph(zid, _build_styles()["ZHBody"]),
            Paragraph(f"{pct:.1f}%", _build_styles()["ZHBody"]),
            Paragraph(f'<font color="{color.hexval()}">{status}</font>', _build_styles()["ZHBody"]),
        ])
    col_w = [50 * mm, 45 * mm, 55 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl


def _build_permit_summary_table(permits):
    header = [Paragraph("ID", _build_styles()["ZHSmallBold"]),
              Paragraph("Type", _build_styles()["ZHSmallBold"]),
              Paragraph("Zone", _build_styles()["ZHSmallBold"]),
              Paragraph("Risk Level", _build_styles()["ZHSmallBold"])]
    rows = [header]
    for p in permits[:30]:
        rl = p.get("risk_level", "Unknown")
        rl_color = CRITICAL_COLOR if rl == "Critical" else WARNING_COLOR if rl == "High" else ACCENT
        rows.append([
            Paragraph(p.get("id", ""), _build_styles()["ZHBody"]),
            Paragraph(p.get("type", ""), _build_styles()["ZHBody"]),
            Paragraph(f"{p.get('zone_id', '')} - {p.get('zone_name', '')}", _build_styles()["ZHBody"]),
            Paragraph(f'<font color="{rl_color.hexval()}">{rl}</font>', _build_styles()["ZHBody"]),
        ])
    col_w = [30 * mm, 35 * mm, 45 * mm, 40 * mm]
    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), ACCENT),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style_cmds.append(("BACKGROUND", (0, i), (-1, i), ROW_ALT))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl
