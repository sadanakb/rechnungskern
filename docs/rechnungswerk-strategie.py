#!/usr/bin/env python3
"""
RechnungsKern Strategie-Dokument PDF Generator
Erzeugt: docs/RechnungsKern_Strategie_2026.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime

# --- Farben ---
PRIMARY = HexColor("#1a1a2e")
ACCENT = HexColor("#0f3460")
HIGHLIGHT = HexColor("#e94560")
LIGHT_BG = HexColor("#f8f9fa")
BORDER = HexColor("#dee2e6")
SUBTLE = HexColor("#6c757d")
GREEN = HexColor("#28a745")
ORANGE = HexColor("#fd7e14")
RED = HexColor("#dc3545")
BLUE = HexColor("#0d6efd")
WHITE = white

# --- Output ---
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(OUTPUT_DIR, "RechnungsKern_Strategie_2026.pdf")


def build_pdf():
    doc = SimpleDocTemplate(
        OUTPUT_PATH,
        pagesize=A4,
        topMargin=20*mm,
        bottomMargin=20*mm,
        leftMargin=20*mm,
        rightMargin=20*mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_title = ParagraphStyle(
        "DocTitle", parent=styles["Title"],
        fontSize=28, leading=34, textColor=PRIMARY,
        spaceAfter=4*mm, alignment=TA_LEFT,
    )
    s_subtitle = ParagraphStyle(
        "DocSubtitle", parent=styles["Normal"],
        fontSize=13, leading=17, textColor=SUBTLE,
        spaceAfter=10*mm,
    )
    s_h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        fontSize=18, leading=22, textColor=PRIMARY,
        spaceBefore=10*mm, spaceAfter=4*mm,
        borderWidth=0, borderPadding=0,
    )
    s_h2 = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=14, leading=18, textColor=ACCENT,
        spaceBefore=6*mm, spaceAfter=3*mm,
    )
    s_h3 = ParagraphStyle(
        "H3", parent=styles["Heading3"],
        fontSize=12, leading=15, textColor=ACCENT,
        spaceBefore=4*mm, spaceAfter=2*mm,
    )
    s_body = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=10, leading=14, textColor=black,
        spaceAfter=2*mm, alignment=TA_JUSTIFY,
    )
    s_bullet = ParagraphStyle(
        "Bullet", parent=s_body,
        leftIndent=12, bulletIndent=4,
        spaceAfter=1.5*mm,
    )
    s_small = ParagraphStyle(
        "Small", parent=styles["Normal"],
        fontSize=8, leading=10, textColor=SUBTLE,
    )
    s_tag_green = ParagraphStyle(
        "TagGreen", parent=styles["Normal"],
        fontSize=9, textColor=GREEN,
    )
    s_tag_orange = ParagraphStyle(
        "TagOrange", parent=styles["Normal"],
        fontSize=9, textColor=ORANGE,
    )
    s_tag_red = ParagraphStyle(
        "TagRed", parent=styles["Normal"],
        fontSize=9, textColor=RED,
    )
    s_center = ParagraphStyle(
        "Center", parent=s_body,
        alignment=TA_CENTER,
    )

    elements = []

    # =========================================================================
    # COVER
    # =========================================================================
    elements.append(Spacer(1, 30*mm))
    elements.append(Paragraph("RechnungsKern", s_title))
    elements.append(Paragraph(
        "Produkt- & Strategiedokument 2026<br/>"
        "Internes Dokument | Stand: 07. Maerz 2026",
        s_subtitle
    ))
    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=2, color=HIGHLIGHT))
    elements.append(Spacer(1, 8*mm))

    # TOC
    toc_items = [
        "1. Was ist RechnungsKern?",
        "2. Vision & Ziel",
        "3. Zielgruppe",
        "4. Aktueller Feature-Umfang",
        "5. Wettbewerbsanalyse",
        "6. Feature-Gaps & Pain Points",
        "7. Roadmap: Was fehlt noch?",
        "8. App-Strategie (PWA + Native)",
        "9. Technische Architektur",
        "10. Naechste Schritte",
    ]
    elements.append(Paragraph("<b>Inhalt</b>", s_h2))
    for item in toc_items:
        elements.append(Paragraph(item, s_body))
    elements.append(PageBreak())

    # =========================================================================
    # 1. WAS IST RECHNUNGSKERN?
    # =========================================================================
    elements.append(Paragraph("1. Was ist RechnungsKern?", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))
    elements.append(Paragraph(
        "RechnungsKern ist eine <b>Open-Source E-Invoicing-Plattform fuer Deutschland</b>. "
        "Die Software digitalisiert den gesamten Rechnungsprozess: vom Scan einer Papierrechnung "
        "per OCR ueber die automatische Felderkennung bis hin zur Erzeugung "
        "gesetzeskonformer <b>XRechnung 3.0.2</b> (UBL-XML) und <b>ZUGFeRD 2.3.3</b> (PDF/A-3) Dokumente.",
        s_body
    ))
    elements.append(Paragraph(
        "RechnungsKern ist die kostenlose, selbst-hostbare Alternative zu kommerziellen "
        "Loesungen wie sevDesk, lexoffice oder easybill, die zwischen 500 und 2.000 EUR/Monat kosten. "
        "Ab 2025 muessen Unternehmen in Deutschland E-Rechnungen empfangen koennen, ab 2027/2028 "
        "muessen sie E-Rechnungen aktiv versenden (Rechnungspflicht). "
        "RechnungsKern macht diese Pflicht fuer jedes Unternehmen erschwinglich.",
        s_body
    ))

    # Key facts box
    facts_data = [
        ["Lizenz", "AGPL-3.0 (Open Source)"],
        ["Status", "Production-ready, 580+ Tests bestanden"],
        ["Deployment", "Self-Hosted (Docker) oder SaaS"],
        ["Preise (SaaS)", "Free (0 EUR) | Starter (9,90 EUR/Mo) | Pro (19,90 EUR/Mo)"],
        ["Compliance", "XRechnung 3.0.2, ZUGFeRD 2.3.3, GoBD, DSGVO, DATEV"],
    ]
    facts_table = Table(facts_data, colWidths=[45*mm, 120*mm])
    facts_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONT", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONT", (1, 0), (1, -1), "Helvetica"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    elements.append(Spacer(1, 4*mm))
    elements.append(facts_table)

    # =========================================================================
    # 2. VISION & ZIEL
    # =========================================================================
    elements.append(Paragraph("2. Vision & Ziel", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph("<b>Vision</b>", s_h3))
    elements.append(Paragraph(
        "Die zentrale Plattform fuer E-Invoicing in Deutschland werden &mdash; "
        "Open Source, selbst-hostbar, KI-gestuetzt und vollstaendig konform mit allen "
        "deutschen und europaeischen Rechnungsstandards.",
        s_body
    ))

    elements.append(Paragraph("<b>Strategische Ziele</b>", s_h3))
    goals = [
        "<b>Compliance-First:</b> Jedes deutsche Unternehmen soll die E-Rechnungspflicht 2027/2028 "
        "mit RechnungsKern erfuellen koennen &mdash; ohne teure SaaS-Abos.",
        "<b>All-in-One Rechnungsloesung:</b> Rechnungen erstellen, versenden, empfangen, validieren, "
        "archivieren und an den Steuerberater exportieren &mdash; ein Werkzeug fuer alles.",
        "<b>KI-Automatisierung:</b> OCR-Erkennung, automatische Kontierung (SKR03/04), "
        "Betrugserkennung und intelligente Zusammenfassungen reduzieren manuelle Arbeit um 80%.",
        "<b>Mobile-First:</b> PWA + native App, damit Rechnungen unterwegs per Foto erfasst, "
        "freigegeben und bezahlt werden koennen.",
        "<b>Community & Ecosystem:</b> Open-Source-Kern mit Plugin-System und API, "
        "damit Steuerberater, Entwickler und Partner das Oekosystem erweitern.",
    ]
    for g in goals:
        elements.append(Paragraph(f"&#8226;  {g}", s_bullet))

    # =========================================================================
    # 3. ZIELGRUPPE
    # =========================================================================
    elements.append(Paragraph("3. Zielgruppe", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    targets = [
        ["Freiberufler & Selbststaendige", "Einfache Rechnungserstellung, mobiler Scan, DATEV-Export zum Steuerberater"],
        ["KMU (1-50 MA)", "Multi-User, Angebote, Mahnwesen, wiederkehrende Rechnungen, Team-Verwaltung"],
        ["Steuerberater", "Mandanten-uebergreifender DATEV-Export, GoBD-Berichte, Audit-Trail"],
        ["E-Commerce", "Batch-Verarbeitung, API/Webhooks, automatische Rechnungserstellung"],
        ["Oeffentliche Verwaltung", "XRechnung-Pflicht, PEPPOL-Anbindung (geplant)"],
    ]
    target_table = Table(
        [["Segment", "Kernbeduerfnisse"]] + targets,
        colWidths=[50*mm, 115*mm]
    )
    target_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("BACKGROUND", (0, 1), (-1, -1), WHITE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
    ]))
    elements.append(target_table)

    # =========================================================================
    # 4. AKTUELLER FEATURE-UMFANG
    # =========================================================================
    elements.append(Paragraph("4. Aktueller Feature-Umfang", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    # Feature categories
    feature_sections = [
        ("E-Rechnung & Dokumentenverarbeitung", [
            "OCR-Erkennung (Surya, 97,7% Genauigkeit) + PaddleOCR Fallback",
            "Batch-OCR: bis zu 20 PDFs gleichzeitig verarbeiten",
            "XRechnung 3.0.2 XML-Erzeugung (EN 16931, UBL 2.1)",
            "ZUGFeRD 2.3.3 PDF/A-3 mit eingebettetem XML",
            "KoSIT-Validator (offizielle Schematron-Pruefung)",
            "Manuelle Rechnungseingabe + CSV-Massenimport",
            "KI-Kategorisierung (SKR03/SKR04) via Ollama/Claude/Mistral",
            "Betrugserkennung (Duplikate, IBAN-Aenderungen, Anomalien)",
        ]),
        ("Angebote & Kundenkommunikation", [
            "Angebotserstellung mit PDF-Export",
            "Lebenszyklus: Entwurf > Gesendet > Akzeptiert > Abgelehnt > Rechnung",
            "Angebot-zu-Rechnung Konvertierung (1 Klick)",
            "Kundenportal: Rechnungen per Link teilen (ohne Login)",
            "Online-Bezahlung via Stripe (Kreditkarte, SEPA, Sofort)",
        ]),
        ("Buchhaltung & Compliance", [
            "DATEV-Export (ASCII-Buchungsstapel + CSV)",
            "GoBD-konforme Archivierung (SHA256, revisionssicher)",
            "Mahnwesen: 3-stufige automatische Zahlungserinnerungen",
            "Wiederkehrende Rechnungen (monatlich/quartalsweise/jaehrlich)",
            "Audit-Log: lueckenlose Nachverfolgung aller Aktionen",
            "DSGVO: Datenexport (Art. 20) + Kontoloeschung (Art. 17)",
        ]),
        ("Administration & Zusammenarbeit", [
            "Multi-Tenant: Organisationen mit Rollenverwaltung (Owner/Admin/Member)",
            "Team-Management: E-Mail-Einladungen, Rollenzuweisung",
            "Lieferanten- und Kontaktverwaltung",
            "Rechnungsdesign-Templates (Farben, Logo, Fusszeile)",
            "Konfigurierbarer Rechnungsnummernkreis",
            "Analytics-Dashboard: Umsatz, Top-Lieferanten, MwSt, Cashflow",
        ]),
        ("Technik & Integrationen", [
            "REST-API mit OpenAPI-Dokumentation",
            "Webhooks (invoice.created, validated, mahnung.sent, etc.)",
            "API-Keys mit Scope-basierter Zugriffskontrolle",
            "WebSocket fuer Echtzeit-Benachrichtigungen",
            "Push-Notifications (Firebase FCM)",
            "Stripe-Billing (Subscriptions + Connect Express)",
            "PWA mit Offline-Support und Install-Prompt",
        ]),
    ]

    for section_title, features in feature_sections:
        elements.append(Paragraph(f"<b>{section_title}</b>", s_h3))
        for f in features:
            elements.append(Paragraph(f"&#10003;  {f}", s_bullet))

    # =========================================================================
    # 5. WETTBEWERBSANALYSE
    # =========================================================================
    elements.append(Paragraph("5. Wettbewerbsanalyse", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph(
        "Die folgende Tabelle vergleicht RechnungsKern mit den fuenf groessten "
        "deutschen Wettbewerbern anhand der wichtigsten Features.",
        s_body
    ))

    comp_header = ["Feature", "RechnungsKern", "sevDesk", "lexoffice", "easybill", "Billomat"]
    comp_data = [
        comp_header,
        ["Open Source",         "Ja",   "Nein", "Nein", "Nein", "Nein"],
        ["Self-Hosting",        "Ja",   "Nein", "Nein", "Nein", "Nein"],
        ["XRechnung 3.0.2",    "Voll", "Basis","Basis","Voll", "Nein"],
        ["ZUGFeRD 2.3.3",      "Extended","Basis","Basis","Basis","Nein"],
        ["KI-Kategorisierung",  "Ja",   "Nein", "Nein", "Nein", "Nein"],
        ["OCR-Belegerfassung",  "Ja",   "Ja",   "Nein", "Nein", "Nein"],
        ["DATEV-Export",        "Ja",   "Ja",   "Ja",   "Ja",   "Ja"],
        ["Mahnwesen",           "Ja",   "Ja",   "Ja",   "Ja",   "Ja"],
        ["Angebote",            "Ja",   "Ja",   "Ja",   "Ja",   "Ja"],
        ["Bankanbindung",       "Geplant","Ja", "Ja",   "Nein", "Ja"],
        ["Gutschriften",        "Geplant","Ja", "Ja",   "Ja",   "Ja"],
        ["Lieferscheine",       "Geplant","Ja", "Ja",   "Ja",   "Ja"],
        ["Multi-Waehrung",      "Geplant","Ja", "Nein", "Ja",   "Nein"],
        ["Marketplace-Anbindung","Nein", "Nein","Nein", "Ja",   "Nein"],
        ["Kundenportal",        "Ja",   "Begrenzt","Nein","Nein","Nein"],
        ["REST-API",            "Voll", "Begrenzt","Begrenzt","Ja","Begrenzt"],
        ["Webhooks",            "Ja",   "Nein", "Nein", "Ja",   "Nein"],
        ["Preis/Monat",         "0-19,90 EUR","7-50 EUR","4-35 EUR","10-65 EUR","8-42 EUR"],
    ]
    col_w = [38*mm, 28*mm, 22*mm, 22*mm, 22*mm, 22*mm]
    comp_table = Table(comp_data, colWidths=col_w)
    comp_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BACKGROUND", (1, 1), (1, -1), HexColor("#e8f5e9")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
    ]
    # Highlight "Geplant" cells in orange
    for row_idx, row in enumerate(comp_data):
        for col_idx, cell in enumerate(row):
            if cell == "Geplant":
                comp_styles.append(("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), ORANGE))
            elif cell == "Nein" and col_idx >= 1:
                comp_styles.append(("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), RED))
            elif cell in ("Ja", "Voll", "Extended") and col_idx >= 1:
                comp_styles.append(("TEXTCOLOR", (col_idx, row_idx), (col_idx, row_idx), GREEN))
    comp_table.setStyle(TableStyle(comp_styles))
    elements.append(comp_table)

    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("<b>Kernvorteil RechnungsKern:</b> Open Source + Self-Hosting + "
                              "KI-Kategorisierung + vollstaendige XRechnung/ZUGFeRD-Unterstuetzung "
                              "bei einem Bruchteil der Kosten.", s_body))

    # =========================================================================
    # 6. FEATURE-GAPS & PAIN POINTS
    # =========================================================================
    elements.append(Paragraph("6. Feature-Gaps & Pain Points der Konkurrenz", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph("<b>Was Nutzer bei Wettbewerbern am meisten stoert:</b>", s_h3))
    pain_points = [
        "<b>Hohe Kosten:</b> sevDesk/lexoffice kosten 7-65 EUR/Monat fuer Features, die bei RW kostenlos sind. "
        "Viele Nutzer zahlen fuer Funktionen, die sie nicht brauchen. <i>Unser Vorteil: Free-Tier + Self-Hosting.</i>",
        "<b>Eingeschraenkte API:</b> sevDesk und lexoffice bieten nur begrenzte APIs. "
        "Entwickler koennen ihre Workflows nicht automatisieren. <i>Unser Vorteil: Volle REST-API + Webhooks.</i>",
        "<b>Kein Self-Hosting:</b> Alle Wettbewerber sind reine Cloud-Loesungen. "
        "Datenschutz-sensible Unternehmen haben keine Wahl. <i>Unser Vorteil: Docker-basiertes Self-Hosting.</i>",
        "<b>Keine KI-Automatisierung:</b> Keiner der Wettbewerber bietet automatische "
        "Kontierung via KI. Manuelles Buchen kostet Stunden. <i>Unser Vorteil: KI-Kategorisierung ab Tag 1.</i>",
        "<b>Schlechte XRechnung-Unterstuetzung:</b> Viele Wettbewerber bieten nur Basis-Profile "
        "statt vollstaendiger EN 16931-Konformitaet. <i>Unser Vorteil: Volle XRechnung 3.0.2 + KoSIT-Validation.</i>",
    ]
    for p in pain_points:
        elements.append(Paragraph(f"&#8226;  {p}", s_bullet))

    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("<b>Top-Features der Konkurrenz, die uns noch fehlen:</b>", s_h3))

    gap_data = [
        ["Feature", "Wer hat es?", "Prioritaet", "Warum wichtig?"],
        ["Bankanbindung\n(FinTS/HBCI)",
         "sevDesk, Billomat,\nFastBill",
         "KRITISCH",
         "Automatischer Zahlungsabgleich ist\nDAS meistgenutzte Feature bei der Konkurrenz.\nOhne das bleiben wir ein Nischen-Tool."],
        ["Gutschriften &\nStornos",
         "Alle Wettbewerber",
         "KRITISCH",
         "Gesetzliche Pflicht bei Korrekturen.\nOhne Gutschriften ist das Produkt\nnicht geschaeftstauglich."],
        ["Lieferscheine",
         "sevDesk, lexoffice,\neasybill",
         "HOCH",
         "Standard-Feature in der Branche.\nErwartet von jedem KMU-Nutzer."],
        ["Multi-Waehrung",
         "sevDesk, easybill",
         "MITTEL",
         "Wichtig fuer international\ntaetige Unternehmen."],
        ["Marketplace-\nAnbindung",
         "easybill (Amazon,\neBay, Shopify)",
         "MITTEL",
         "E-Commerce-Segment. Grosses\nWachstumspotenzial."],
        ["ELSTER-\nSchnittstelle",
         "sevDesk",
         "NIEDRIG",
         "USt-Voranmeldung direkt abgeben.\nNice-to-have, kein Blocker."],
    ]
    gap_table = Table(gap_data, colWidths=[32*mm, 32*mm, 22*mm, 75*mm])
    gap_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), HIGHLIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]
    # Color priority column
    for i, row in enumerate(gap_data[1:], 1):
        prio = row[2]
        if prio == "KRITISCH":
            gap_styles.append(("TEXTCOLOR", (2, i), (2, i), RED))
            gap_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 8))
        elif prio == "HOCH":
            gap_styles.append(("TEXTCOLOR", (2, i), (2, i), ORANGE))
            gap_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 8))
        elif prio == "MITTEL":
            gap_styles.append(("TEXTCOLOR", (2, i), (2, i), BLUE))
        elif prio == "NIEDRIG":
            gap_styles.append(("TEXTCOLOR", (2, i), (2, i), SUBTLE))
    gap_table.setStyle(TableStyle(gap_styles))
    elements.append(gap_table)

    # =========================================================================
    # 7. ROADMAP
    # =========================================================================
    elements.append(PageBreak())
    elements.append(Paragraph("7. Roadmap: Was fehlt noch?", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph(
        "Die Roadmap priorisiert nach Business-Impact und Marktrelevanz. "
        "Kritische Features werden zuerst umgesetzt, da sie das Produkt "
        "von einem Nischen-Tool zu einer vollwertigen Rechnungsloesung machen.",
        s_body
    ))

    # Phase table
    roadmap_data = [
        ["Phase", "Inhalt", "Prioritaet", "Status"],
        ["Phase 13\nQ1 2026",
         "Gutschriften & Stornos\n"
         "- Negativ-Rechnungen mit Bezug zu Original\n"
         "- Eigener Nummernkreis\n"
         "- Automatische Gegenbuchung im DATEV-Export",
         "KRITISCH", "Geplant"],
        ["Phase 14\nQ1 2026",
         "Bankanbindung (FinTS/HBCI)\n"
         "- Automatischer Kontoabruf\n"
         "- Intelligenter Zahlungsabgleich\n"
         "- Offene-Posten-Liste mit Live-Status",
         "KRITISCH", "Geplant"],
        ["Phase 15\nQ2 2026",
         "Lieferscheine\n"
         "- Eigenes Dokumentenmodell\n"
         "- Verknuepfung mit Angeboten/Rechnungen\n"
         "- PDF-Erzeugung + Versand",
         "HOCH", "Geplant"],
        ["Phase 16\nQ2 2026",
         "E-Mail-Integration (SMTP)\n"
         "- Rechnungen/Angebote per E-Mail versenden\n"
         "- Zustellstatus-Tracking\n"
         "- Belegerfassung per E-Mail-Eingang",
         "HOCH", "Geplant"],
        ["Phase 17\nQ2 2026",
         "Mobile App (PWA + Native)\n"
         "- Foto-Scan per Kamera\n"
         "- Offline-Sync\n"
         "- Push-Benachrichtigungen\n"
         "- React Native / Capacitor Wrapper",
         "HOCH", "Geplant"],
        ["Phase 18\nQ3 2026",
         "Multi-Waehrung\n"
         "- USD, CHF, GBP, weitere\n"
         "- Wechselkurs-API\n"
         "- Reporting in Heimatwaehrung",
         "MITTEL", "Geplant"],
        ["Phase 19\nQ3 2026",
         "Marketplace-Anbindung\n"
         "- Amazon, eBay, Shopify\n"
         "- Automatische Rechnungserstellung\n"
         "- Bestandssynchronisation",
         "MITTEL", "Geplant"],
        ["Phase 20\nQ4 2026",
         "Erweiterte Buchhaltung\n"
         "- Einnahmen-Ueberschuss-Rechnung (EUeR)\n"
         "- Gewinn-/Verlustrechnung (GuV)\n"
         "- ELSTER-Schnittstelle (USt-VA)",
         "NIEDRIG", "Geplant"],
        ["Phase 21\nQ4 2026",
         "Plugin-System & White-Label\n"
         "- API-basiertes Plugin-System\n"
         "- Custom Branding / Custom Domain\n"
         "- Steuerberater-Mandantenportal",
         "NIEDRIG", "Geplant"],
    ]
    rm_col_w = [22*mm, 85*mm, 22*mm, 18*mm]
    rm_table = Table(roadmap_data, colWidths=rm_col_w)
    rm_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]
    for i, row in enumerate(roadmap_data[1:], 1):
        prio = row[2]
        if prio == "KRITISCH":
            rm_styles.append(("TEXTCOLOR", (2, i), (2, i), RED))
            rm_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 8))
        elif prio == "HOCH":
            rm_styles.append(("TEXTCOLOR", (2, i), (2, i), ORANGE))
            rm_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 8))
        elif prio == "MITTEL":
            rm_styles.append(("TEXTCOLOR", (2, i), (2, i), BLUE))
        elif prio == "NIEDRIG":
            rm_styles.append(("TEXTCOLOR", (2, i), (2, i), SUBTLE))
    rm_table.setStyle(TableStyle(rm_styles))
    elements.append(rm_table)

    # =========================================================================
    # 8. APP-STRATEGIE
    # =========================================================================
    elements.append(PageBreak())
    elements.append(Paragraph("8. App-Strategie (PWA + Native)", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph("<b>Aktueller Stand: PWA</b>", s_h3))
    elements.append(Paragraph(
        "RechnungsKern ist bereits als Progressive Web App (PWA) installierbar. "
        "Service Worker, App-Icons (192x192, 512x512), Offline-Support und "
        "Standalone-Modus sind implementiert. Push-Notifications laufen ueber Firebase FCM.",
        s_body
    ))

    pwa_status = [
        ["Komponente", "Status", "Details"],
        ["Web App Manifest", "Fertig", "Name, Icons, Shortcuts, Screenshots, Standalone-Modus"],
        ["Service Worker", "Fertig", "Serwist (@serwist/next), Offline-Caching"],
        ["App Icons", "Fertig", "192x192 + 512x512, maskable"],
        ["Install Prompt", "Fertig", "Automatischer Install-Banner auf Android/Desktop"],
        ["Push Notifications", "Fertig", "Firebase FCM, 4 Event-Trigger"],
        ["Kamera-Scan", "Fehlt", "Foto-Aufnahme per PWA Camera API"],
        ["Offline-Sync", "Fehlt", "Background Sync fuer offline erstellte Rechnungen"],
        ["iOS Support", "Teilweise", "PWA auf iOS hat Einschraenkungen (kein Push vor iOS 16.4)"],
    ]
    pwa_table = Table(pwa_status, colWidths=[38*mm, 22*mm, 100*mm])
    pwa_styles_list = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]
    for i, row in enumerate(pwa_status[1:], 1):
        if row[1] == "Fertig":
            pwa_styles_list.append(("TEXTCOLOR", (1, i), (1, i), GREEN))
        elif row[1] == "Fehlt":
            pwa_styles_list.append(("TEXTCOLOR", (1, i), (1, i), RED))
        elif row[1] == "Teilweise":
            pwa_styles_list.append(("TEXTCOLOR", (1, i), (1, i), ORANGE))
    pwa_table.setStyle(TableStyle(pwa_styles_list))
    elements.append(pwa_table)

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("<b>Strategie: Hybrid-Ansatz (PWA + Native Wrapper)</b>", s_h3))
    elements.append(Paragraph(
        "Der empfohlene Ansatz kombiniert die Staerken beider Welten:",
        s_body
    ))

    strategy_points = [
        "<b>Phase A &mdash; PWA verbessern (sofort):</b> Kamera-API fuer Belegerfassung, "
        "Background Sync fuer Offline-Rechnungen, verbesserte iOS-Unterstuetzung. "
        "Kosten: gering, da nur Frontend-Arbeit.",
        "<b>Phase B &mdash; Capacitor Wrapper (Q2 2026):</b> Die bestehende Next.js-App in eine "
        "native Huelle verpacken mit Capacitor (Ionic). Zugang zu nativen APIs: Kamera, "
        "Dateisystem, biometrische Auth (Face ID / Fingerprint). Veroeffentlichung im "
        "App Store und Google Play Store.",
        "<b>Phase C &mdash; Native Features (Q3-Q4 2026):</b> Widgets (z.B. offene Rechnungen auf dem Homescreen), "
        "Siri/Google Assistant Integration, Apple Watch Companion fuer Zahlungsbenachrichtigungen. "
        "Optional: Teilweise React Native Migration fuer performance-kritische Screens.",
    ]
    for p in strategy_points:
        elements.append(Paragraph(f"&#8226;  {p}", s_bullet))

    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("<b>Warum Capacitor statt React Native?</b>", s_h3))
    cap_comp = [
        ["Kriterium", "Capacitor", "React Native", "Flutter"],
        ["Code-Wiederverwendung", "95%+ (nutzt bestehende\nNext.js-Codebase)", "30-50% (neues UI\nmit RN-Komponenten)", "0% (komplett neues\nDart-Projekt)"],
        ["Time-to-Market", "2-4 Wochen", "3-6 Monate", "4-8 Monate"],
        ["Native APIs", "Ja (Plugins)", "Ja (nativ)", "Ja (Plugins)"],
        ["Performance", "Gut (WebView)", "Sehr gut (nativ)", "Sehr gut (nativ)"],
        ["Wartungsaufwand", "Minimal (1 Codebase)", "Hoch (2 Codebases)", "Mittel (1 Codebase,\nneue Sprache)"],
        ["App Store", "Ja", "Ja", "Ja"],
        ["Empfehlung", "Bester ROI fuer\nuns jetzt", "Spaeter fuer\nPerformance-Screens", "Nicht empfohlen"],
    ]
    cap_table = Table(cap_comp, colWidths=[35*mm, 40*mm, 40*mm, 40*mm])
    cap_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8),
        ("BACKGROUND", (1, 1), (1, -1), HexColor("#e8f5e9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]))
    elements.append(cap_table)

    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph("<b>Mobile-First Features (Komplett-Paket):</b>", s_h3))
    mobile_features = [
        "<b>Beleg-Scan:</b> Kamera oeffnen, Rechnung fotografieren, OCR laeuft sofort im Hintergrund",
        "<b>Freigabe-Workflow:</b> Push-Notification bei neuer Rechnung, Freigabe per Swipe",
        "<b>Offline-Modus:</b> Rechnungen erstellen ohne Internet, automatische Synchronisation",
        "<b>Biometrische Auth:</b> Face ID / Fingerprint statt Passwort",
        "<b>Schnellaktionen:</b> 3D Touch / Long Press fuer 'Neue Rechnung', 'Scannen', 'Dashboard'",
        "<b>Dark Mode:</b> Systemweite Unterstuetzung fuer dunkles Design",
        "<b>Widgets:</b> Offene Rechnungen, faellige Betraege, Umsatz-KPI auf dem Homescreen",
        "<b>Share Extension:</b> PDFs aus anderen Apps direkt in RechnungsKern importieren",
        "<b>Apple Watch:</b> Zahlungseingang-Benachrichtigungen am Handgelenk",
    ]
    for f in mobile_features:
        elements.append(Paragraph(f"&#8226;  {f}", s_bullet))

    # =========================================================================
    # 9. TECHNISCHE ARCHITEKTUR
    # =========================================================================
    elements.append(PageBreak())
    elements.append(Paragraph("9. Technische Architektur", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    arch_data = [
        ["Schicht", "Technologie", "Details"],
        ["Frontend", "Next.js 16 + React 19\n+ TypeScript 5", "App Router, Tailwind CSS v4,\nShadcn/ui, Radix UI"],
        ["Backend", "Python 3.11+\nFastAPI 0.133", "33 API-Router, Uvicorn,\nasync/await"],
        ["Datenbank", "PostgreSQL 17", "SQLAlchemy 2.0 ORM,\nRow-Level Tenant Isolation"],
        ["Cache/Queue", "Redis 7 + ARQ", "Background Jobs:\nOCR, Kategorisierung, E-Mail"],
        ["OCR", "Surya + PaddleOCR", "97,7% Genauigkeit,\nDual-Engine mit Fallback"],
        ["KI", "Ollama / Claude /\nMistral / OpenAI", "Hybrid-Strategie:\nLokal + Cloud"],
        ["E-Rechnung", "lxml + factur-x +\nWeasyPrint", "XRechnung 3.0.2 (UBL 2.1)\nZUGFeRD 2.3.3 (PDF/A-3)"],
        ["Auth", "JWT + bcrypt_sha256", "Access (30min) + Refresh (7d)\nRole-based (Owner/Admin/Member)"],
        ["Payments", "Stripe", "Subscriptions + Connect Express\n+ Kundenportal-Zahlung"],
        ["E-Mail", "Brevo", "Transaktional: Einladungen,\nMahnungen, Passwort-Reset"],
        ["Monitoring", "Uptime Kuma", "Self-hosted, HTTP/TCP Checks"],
        ["Deployment", "Docker Compose", "5 Services: DB, Redis,\nBackend, Frontend, Monitoring"],
    ]
    arch_table = Table(arch_data, colWidths=[28*mm, 38*mm, 90*mm])
    arch_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 9),
        ("FONT", (1, 1), (-1, -1), "Helvetica", 8),
        ("TEXTCOLOR", (0, 1), (0, -1), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
    ]))
    elements.append(arch_table)

    elements.append(Spacer(1, 5*mm))
    elements.append(Paragraph("<b>Sicherheit & Compliance</b>", s_h3))
    sec_points = [
        "Tenant Isolation: Row-Level org_id Filtering + JWT org Claims",
        "580+ automatisierte Tests (Backend + Frontend + E2E)",
        "Security Audit: 41 Backend + 62 Frontend Findings behoben",
        "Rate Limiting (SlowAPI), CORS, Security Headers, SSRF-Schutz",
        "GoBD: Revisionssichere Archivierung mit SHA256",
        "DSGVO: Datenexport (Art. 20) + Kontoloeschung (Art. 17)",
        "Webhook-Signierung: HMAC-SHA256 (X-Signature-256)",
    ]
    for s in sec_points:
        elements.append(Paragraph(f"&#10003;  {s}", s_bullet))

    # =========================================================================
    # 10. NAECHSTE SCHRITTE
    # =========================================================================
    elements.append(Spacer(1, 6*mm))
    elements.append(Paragraph("10. Naechste Schritte", s_h1))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 3*mm))

    elements.append(Paragraph(
        "Die folgenden Schritte haben hoechste Prioritaet, um RechnungsKern "
        "von einem starken MVP zu einer marktreifen Loesung zu machen:",
        s_body
    ))

    next_steps = [
        ["#", "Aufgabe", "Prioritaet", "Geschaetzter Aufwand"],
        ["1", "Gutschriften & Stornos implementieren\n(gesetzliche Pflicht bei Korrekturen)", "KRITISCH", "Backend + Frontend\nPhase 13"],
        ["2", "Bankanbindung FinTS/HBCI\n(automatischer Zahlungsabgleich)", "KRITISCH", "Backend + Integration\nPhase 14"],
        ["3", "Lieferscheine\n(Standard-Feature, Kundenerwartung)", "HOCH", "Backend + Frontend\nPhase 15"],
        ["4", "E-Mail-Versand (SMTP)\n(Rechnungen/Angebote per E-Mail)", "HOCH", "Backend + Templates\nPhase 16"],
        ["5", "Mobile App (Capacitor Wrapper)\n(App Store + Google Play)", "HOCH", "Frontend + Native\nPhase 17"],
        ["6", "Alembic DB-Migrationen\n(Production-Readiness)", "HOCH", "Backend\nDevOps"],
        ["7", "Deployment-Guide\n(Hetzner + Coolify)", "MITTEL", "Dokumentation\nDevOps"],
        ["8", "Multi-Waehrung\n(internationale Kunden)", "MITTEL", "Backend + Frontend\nPhase 18"],
    ]
    ns_table = Table(next_steps, colWidths=[10*mm, 68*mm, 24*mm, 42*mm])
    ns_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), HIGHLIGHT),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 9),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 9),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
    ]
    for i, row in enumerate(next_steps[1:], 1):
        prio = row[2]
        if prio == "KRITISCH":
            ns_styles.append(("TEXTCOLOR", (2, i), (2, i), RED))
            ns_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 9))
        elif prio == "HOCH":
            ns_styles.append(("TEXTCOLOR", (2, i), (2, i), ORANGE))
            ns_styles.append(("FONT", (2, i), (2, i), "Helvetica-Bold", 9))
        elif prio == "MITTEL":
            ns_styles.append(("TEXTCOLOR", (2, i), (2, i), BLUE))
    ns_table.setStyle(TableStyle(ns_styles))
    elements.append(ns_table)

    elements.append(Spacer(1, 8*mm))
    elements.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    elements.append(Spacer(1, 4*mm))
    elements.append(Paragraph(
        "<b>Fazit:</b> RechnungsKern hat bereits einen beeindruckenden Feature-Umfang, "
        "der in vielen Bereichen ueber die Konkurrenz hinausgeht (Open Source, Self-Hosting, "
        "KI-Kategorisierung, volle XRechnung/ZUGFeRD-Unterstuetzung). "
        "Um den Sprung von einem starken MVP zur marktreifen Loesung zu schaffen, "
        "muessen die kritischen Luecken (Gutschriften, Bankanbindung) geschlossen und "
        "die Mobile-Strategie (Capacitor + PWA) umgesetzt werden. "
        "Mit diesen Erweiterungen positioniert sich RechnungsKern als die beste "
        "Open-Source-Alternative im deutschen E-Invoicing-Markt.",
        s_body
    ))

    elements.append(Spacer(1, 15*mm))
    elements.append(Paragraph(
        "RechnungsKern | Internes Strategiedokument | Stand: 07.03.2026 | Vertraulich",
        s_small
    ))

    # Build
    doc.build(elements)
    print(f"PDF erstellt: {OUTPUT_PATH}")


if __name__ == "__main__":
    build_pdf()
