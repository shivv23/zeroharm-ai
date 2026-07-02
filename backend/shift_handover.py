from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

import constants as C

DARK_BG = HexColor("#080c16")
ACCENT = HexColor("#00e5ff")
TEXT_SECONDARY = HexColor("#9ca3af")
WHITE = colors.white


def generate_shift_handover(
    plant_name: str,
    shift_label: str,
    alerts: List[Dict],
    permits: List[Dict],
    risk_trend: List[Dict],
    incidents: List[Dict],
    compliance_score: Optional[float] = None,
    health_index: Optional[Dict] = None,
    zone_risk_scores: Optional[Dict] = None,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"ZeroHarm AI — Shift Handover Report", styles["Title"]))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(
        f"Plant: {plant_name} | Shift: {shift_label} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Shift Summary", styles["Heading2"]))
    summary_data = [
        ["Metric", "Value"],
        ["Total Alerts", str(len(alerts))],
        ["Active Permits", str(len(permits))],
        ["Incidents", str(len(incidents))],
        ["Compliance Score", f"{compliance_score:.1f}%" if compliance_score is not None else "N/A"],
        ["Health Index", f"{health_index.get('overall', 0):.0f}% {health_index.get('label', '')}" if health_index else "N/A"],
    ]
    t = Table(summary_data, colWidths=[100*mm, 70*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Active Alerts", styles["Heading2"]))
    if alerts:
        alert_rows = [["Severity", "Zone", "Message", "Time"]]
        for a in alerts[:10]:
            alert_rows.append([
                a.get("severity", ""),
                a.get("zone_id", ""),
                a.get("message", "")[:60],
                a.get("timestamp", "")[-8:] if a.get("timestamp") else "",
            ])
        t2 = Table(alert_rows, colWidths=[20*mm, 25*mm, 85*mm, 30*mm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t2)
    else:
        elements.append(Paragraph("No active alerts.", styles["Normal"]))
    elements.append(Spacer(1, 6*mm))

    elements.append(Paragraph("Risk Trend (last 10 readings)", styles["Heading2"]))
    if risk_trend:
        trend_rows = [["Time", "Score", "Severity"]]
        for r in risk_trend[-10:]:
            trend_rows.append([
                r.get("timestamp", "")[-8:] if r.get("timestamp") else "",
                f"{r.get('score', 0):.2f}",
                r.get("severity", ""),
            ])
        t3 = Table(trend_rows, colWidths=[40*mm, 40*mm, 80*mm])
        t3.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(t3)
    else:
        elements.append(Paragraph("No trend data available.", styles["Normal"]))

    doc.build(elements)
    return buf.getvalue()
