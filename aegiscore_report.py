"""
AegisCore PDF Report Generator
================================
Usage:
    python aegiscore_report.py

Edit the REPORT_DATA dict below to fill in real findings.
Output: aegiscore_report_{company}_{date}.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate
import datetime
import os

# ─────────────────────────────────────────────
#  REPORT DATA  ← Edit this to fill in real info
# ─────────────────────────────────────────────

REPORT_DATA = {
    "client_name":    "Acme SaaS Pvt Ltd",
    "client_domain":  "acme-startup.io",
    "contact_name":   "Arjun Sharma",
    "contact_role":   "CTO",
    "assessment_type": "Web Application VAPT",
    "scope":          "External — acme-startup.io and api.acme-startup.io",
    "start_date":     "12 Feb 2026",
    "end_date":       "14 Feb 2026",
    "report_date":    "17 Feb 2026",
    "assessor":       "AegisCore Security Team",
    "risk_score":     6.4,     # out of 10
    "risk_rating":    "MEDIUM-HIGH",

    # Executive summary paragraph
    "executive_summary": (
        "AegisCore conducted a Web Application Vulnerability Assessment and Penetration Test (VAPT) "
        "against the external attack surface of acme-startup.io between 12–14 February 2026. "
        "The assessment identified 14 findings across four severity levels, including 2 Critical "
        "vulnerabilities that require immediate remediation. "
        "The most significant risks include an unauthenticated admin panel, an SQL injection vulnerability "
        "in the login flow, and a live AWS API key exposed in the frontend JavaScript bundle. "
        "AegisCore recommends addressing all Critical and High findings within 7 days. "
        "Medium and Low findings should be addressed within 30 days as part of routine hardening."
    ),

    # findings: severity in CRITICAL / HIGH / MEDIUM / LOW / INFO
    "findings": [
        {
            "id": "AC-001",
            "severity": "CRITICAL",
            "title": "Unauthenticated Admin Panel Exposed",
            "description": (
                "The administrative dashboard located at /admin is publicly accessible without any "
                "authentication mechanism. Any unauthenticated user on the internet can access this "
                "panel and view, modify, or delete customer data and system configuration."
            ),
            "impact": (
                "Full compromise of customer data. An attacker can enumerate users, export records, "
                "modify account data, or disrupt service availability."
            ),
            "remediation": (
                "Immediately restrict access to /admin behind strong authentication (MFA recommended). "
                "Consider IP allowlisting for admin access if the panel is only needed internally. "
                "Review server access logs for any unauthorized access that may have already occurred."
            ),
            "cvss": "9.8",
        },
        {
            "id": "AC-002",
            "severity": "CRITICAL",
            "title": "SQL Injection in Login Endpoint",
            "description": (
                "The POST /api/auth/login endpoint is vulnerable to SQL injection via the 'email' "
                "parameter. Unsanitized user input is passed directly into a database query, allowing "
                "an attacker to bypass authentication or extract the entire user database."
            ),
            "impact": (
                "Authentication bypass, full database dump including passwords and PII, "
                "potential for database server command execution depending on configuration."
            ),
            "remediation": (
                "Replace raw SQL queries with parameterized queries or a prepared statement ORM. "
                "Validate and sanitize all user inputs server-side. "
                "Deploy a Web Application Firewall (WAF) as a short-term mitigation while the fix is deployed."
            ),
            "cvss": "9.1",
        },
        {
            "id": "AC-003",
            "severity": "HIGH",
            "title": "AWS API Key Hardcoded in Frontend JS Bundle",
            "description": (
                "A live AWS IAM API key (AKIA...) was identified hardcoded inside the compiled "
                "frontend JavaScript bundle (main.bundle.js). This file is publicly downloadable "
                "by any visitor to the site."
            ),
            "impact": (
                "Any attacker who downloads your JS bundle gains access to your AWS account "
                "with the permissions attached to this key — potentially including S3 buckets, "
                "Lambda functions, RDS databases, and billing."
            ),
            "remediation": (
                "Immediately revoke the exposed key in AWS IAM console. "
                "Rotate all credentials. Never store secrets in frontend code — use environment "
                "variables server-side and secret management tools (AWS Secrets Manager, Vault). "
                "Add secret scanning to your CI/CD pipeline (e.g. truffleHog, GitGuardian)."
            ),
            "cvss": "8.6",
        },
        {
            "id": "AC-004",
            "severity": "HIGH",
            "title": "Server Accepts Deprecated TLS 1.0",
            "description": (
                "The web server is configured to accept TLS 1.0 and TLS 1.1 connections. "
                "Both versions are deprecated and contain known cryptographic vulnerabilities "
                "including POODLE and BEAST attacks."
            ),
            "impact": (
                "An attacker in a privileged network position can downgrade the TLS version "
                "and decrypt traffic in transit, exposing session tokens and sensitive user data."
            ),
            "remediation": (
                "Disable TLS 1.0 and 1.1 in your server configuration. "
                "Only accept TLS 1.2 and TLS 1.3. "
                "Update your SSL/TLS configuration to follow Mozilla's modern compatibility profile."
            ),
            "cvss": "7.4",
        },
        {
            "id": "AC-005",
            "severity": "HIGH",
            "title": "Broken Object Level Authorization on API",
            "description": (
                "The GET /api/users/{id}/profile endpoint does not verify that the authenticated "
                "user is authorized to access the requested profile. Any authenticated user can "
                "access any other user's profile by iterating numeric IDs (IDOR)."
            ),
            "impact": (
                "Mass enumeration and exfiltration of all user profile data including email "
                "addresses, phone numbers, and account history."
            ),
            "remediation": (
                "Implement server-side authorization checks on every resource access. "
                "Verify that the requesting user owns or has permission to access the "
                "requested object. Use non-sequential UUIDs instead of numeric IDs."
            ),
            "cvss": "7.1",
        },
        {
            "id": "AC-006",
            "severity": "MEDIUM",
            "title": "Missing HTTP Security Headers",
            "description": (
                "The application responses are missing several critical security headers: "
                "Content-Security-Policy (CSP), X-Frame-Options, X-Content-Type-Options, "
                "and HTTP Strict Transport Security (HSTS)."
            ),
            "impact": (
                "Absence of these headers enables clickjacking attacks (X-Frame-Options), "
                "MIME-type sniffing attacks, cross-site scripting escalation (CSP), "
                "and SSL-stripping attacks (HSTS)."
            ),
            "remediation": (
                "Add the following headers to all HTTP responses: "
                "Strict-Transport-Security: max-age=31536000; includeSubDomains, "
                "X-Frame-Options: DENY, X-Content-Type-Options: nosniff, "
                "and a Content-Security-Policy appropriate to your application."
            ),
            "cvss": "5.4",
        },
        {
            "id": "AC-007",
            "severity": "MEDIUM",
            "title": "Verbose Error Messages Expose Stack Traces",
            "description": (
                "Application error pages return full stack traces and internal file paths "
                "when unhandled exceptions occur. These were triggered via malformed API requests."
            ),
            "impact": (
                "Stack traces reveal framework versions, internal file structure, "
                "and code logic that assist attackers in crafting targeted exploits."
            ),
            "remediation": (
                "Disable debug/verbose error mode in production. "
                "Return generic error messages to users. "
                "Log full error details server-side for internal debugging only."
            ),
            "cvss": "4.3",
        },
        {
            "id": "AC-008",
            "severity": "LOW",
            "title": "Subdomain Takeover Risk on staging.acme-startup.io",
            "description": (
                "The subdomain staging.acme-startup.io has a dangling CNAME record pointing to "
                "a decommissioned cloud resource that is no longer claimed."
            ),
            "impact": (
                "An attacker can claim the cloud resource and serve malicious content "
                "from your subdomain, enabling phishing attacks against your users."
            ),
            "remediation": (
                "Remove the dangling DNS CNAME record for staging.acme-startup.io immediately, "
                "or re-claim the underlying cloud resource if the subdomain is still needed."
            ),
            "cvss": "3.1",
        },
    ],

    # Remediation summary table
    "remediation_timeline": [
        ("Immediate (24–48 hrs)",  ["AC-001", "AC-002", "AC-003"]),
        ("Short-term (7 days)",    ["AC-004", "AC-005"]),
        ("Medium-term (30 days)",  ["AC-006", "AC-007"]),
        ("Maintenance",            ["AC-008"]),
    ],
}

# ─────────────────────────────────────────────
#  BRAND COLORS
# ─────────────────────────────────────────────
C_BG        = colors.HexColor("#07080B")
C_SURFACE   = colors.HexColor("#0E1016")
C_SURFACE2  = colors.HexColor("#141720")
C_BORDER    = colors.HexColor("#1E2330")
C_ACCENT    = colors.HexColor("#00E87A")
C_TEXT      = colors.HexColor("#E8ECF0")
C_MUTED     = colors.HexColor("#6B7589")
C_RED       = colors.HexColor("#FF4757")
C_ORANGE    = colors.HexColor("#FF8C42")
C_YELLOW    = colors.HexColor("#FFD166")
C_BLUE      = colors.HexColor("#38B6FF")
C_WHITE     = colors.white

SEV_COLORS = {
    "CRITICAL": C_RED,
    "HIGH":     C_ORANGE,
    "MEDIUM":   C_YELLOW,
    "LOW":      C_BLUE,
    "INFO":     C_MUTED,
}

SEV_BG = {
    "CRITICAL": colors.HexColor("#2A0A0E"),
    "HIGH":     colors.HexColor("#1F1208"),
    "MEDIUM":   colors.HexColor("#1F1A08"),
    "LOW":      colors.HexColor("#081420"),
    "INFO":     colors.HexColor("#111318"),
}

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

# ─────────────────────────────────────────────
#  STYLES
# ─────────────────────────────────────────────
def make_styles():
    return {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=36,
            textColor=C_TEXT,
            leading=42,
            spaceAfter=6,
        ),
        "cover_accent": ParagraphStyle(
            "cover_accent",
            fontName="Helvetica-Bold",
            fontSize=36,
            textColor=C_ACCENT,
            leading=42,
            spaceAfter=20,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=10,
            textColor=C_MUTED,
            leading=16,
        ),
        "cover_meta_val": ParagraphStyle(
            "cover_meta_val",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=C_TEXT,
            leading=16,
        ),
        "section_tag": ParagraphStyle(
            "section_tag",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=C_ACCENT,
            leading=12,
            spaceBefore=4,
            spaceAfter=4,
            letterSpacing=2,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Helvetica-Bold",
            fontSize=22,
            textColor=C_TEXT,
            leading=28,
            spaceAfter=12,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=9,
            textColor=C_MUTED,
            leading=15,
            spaceAfter=6,
        ),
        "body_white": ParagraphStyle(
            "body_white",
            fontName="Helvetica",
            fontSize=9,
            textColor=C_TEXT,
            leading=15,
            spaceAfter=4,
        ),
        "finding_id": ParagraphStyle(
            "finding_id",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=C_MUTED,
            leading=12,
        ),
        "finding_title": ParagraphStyle(
            "finding_title",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=C_TEXT,
            leading=18,
            spaceAfter=8,
        ),
        "label": ParagraphStyle(
            "label",
            fontName="Helvetica-Bold",
            fontSize=8,
            textColor=C_ACCENT,
            leading=12,
            spaceBefore=8,
            spaceAfter=3,
            letterSpacing=1,
        ),
        "footer_text": ParagraphStyle(
            "footer_text",
            fontName="Helvetica",
            fontSize=7,
            textColor=C_MUTED,
            leading=10,
        ),
        "toc_item": ParagraphStyle(
            "toc_item",
            fontName="Helvetica",
            fontSize=10,
            textColor=C_TEXT,
            leading=20,
        ),
        "toc_num": ParagraphStyle(
            "toc_num",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=C_ACCENT,
            leading=20,
        ),
        "cvss": ParagraphStyle(
            "cvss",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=C_MUTED,
            leading=14,
        ),
    }

# ─────────────────────────────────────────────
#  PAGE BACKGROUND + HEADER/FOOTER CANVAS
# ─────────────────────────────────────────────
def draw_page(canv, doc, data):
    canv.saveState()
    # Dark background
    canv.setFillColor(C_BG)
    canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Subtle grid
    canv.setStrokeColor(colors.HexColor("#0D0F14"))
    canv.setLineWidth(0.5)
    step = 20 * mm
    for x in range(0, int(PAGE_W) + int(step), int(step)):
        canv.line(x, 0, x, PAGE_H)
    for y in range(0, int(PAGE_H) + int(step), int(step)):
        canv.line(0, y, PAGE_W, y)

    # Top accent bar
    canv.setFillColor(C_ACCENT)
    canv.rect(0, PAGE_H - 3, PAGE_W, 3, fill=1, stroke=0)

    # Header — logo left, doc title right
    if doc.page > 1:
        canv.setFillColor(C_SURFACE)
        canv.rect(0, PAGE_H - 14*mm, PAGE_W, 11*mm, fill=1, stroke=0)
        canv.setStrokeColor(C_BORDER)
        canv.setLineWidth(0.5)
        canv.line(0, PAGE_H - 14*mm, PAGE_W, PAGE_H - 14*mm)

        canv.setFont("Helvetica-Bold", 9)
        canv.setFillColor(C_TEXT)
        canv.drawString(MARGIN, PAGE_H - 10*mm, "AEGIS")
        canv.setFillColor(C_ACCENT)
        canv.drawString(MARGIN + 24, PAGE_H - 10*mm, "CORE")

        canv.setFont("Helvetica", 8)
        canv.setFillColor(C_MUTED)
        title_str = "SECURITY ASSESSMENT REPORT — CONFIDENTIAL"
        canv.drawRightString(PAGE_W - MARGIN, PAGE_H - 10*mm, title_str)

    # Footer
    canv.setFillColor(C_SURFACE)
    canv.rect(0, 0, PAGE_W, 12*mm, fill=1, stroke=0)
    canv.setStrokeColor(C_BORDER)
    canv.setLineWidth(0.5)
    canv.line(0, 12*mm, PAGE_W, 12*mm)

    canv.setFont("Helvetica", 7)
    canv.setFillColor(C_MUTED)
    canv.drawString(MARGIN, 4*mm, f"© 2026 AegisCore  •  Confidential — For authorised recipients only")
    canv.drawString(MARGIN + 120*mm, 4*mm, f"Client: {data['client_name']}")
    canv.setFillColor(C_ACCENT)
    canv.drawRightString(PAGE_W - MARGIN, 4*mm, f"Page {doc.page}")

    canv.restoreState()

# ─────────────────────────────────────────────
#  SEVERITY BADGE helper
# ─────────────────────────────────────────────
def sev_badge_table(severity):
    c = SEV_COLORS.get(severity, C_MUTED)
    bg = SEV_BG.get(severity, C_SURFACE)
    style = ParagraphStyle("sb", fontName="Helvetica-Bold", fontSize=8,
                           textColor=c, leading=10, letterSpacing=1)
    t = Table([[Paragraph(severity, style)]],
              colWidths=[22*mm], rowHeights=[6*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0), (-1,-1), bg),
        ("BOX",         (0,0), (-1,-1), 0.5, c),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",  (0,0), (-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))
    return t

# ─────────────────────────────────────────────
#  FINDING COUNT SUMMARY TABLE
# ─────────────────────────────────────────────
def build_summary_table(findings, styles):
    counts = {"CRITICAL":0,"HIGH":0,"MEDIUM":0,"LOW":0,"INFO":0}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"],0) + 1

    header_style = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=8,
                                  textColor=C_MUTED, leading=12, letterSpacing=1)
    rows = []
    for sev in ["CRITICAL","HIGH","MEDIUM","LOW","INFO"]:
        c = SEV_COLORS[sev]
        num_style = ParagraphStyle("ns", fontName="Helvetica-Bold", fontSize=22,
                                   textColor=c, leading=24)
        lbl_style = ParagraphStyle("ls", fontName="Helvetica", fontSize=8,
                                   textColor=C_MUTED, leading=12)
        rows.append(
            Table([[Paragraph(str(counts[sev]), num_style)],
                   [Paragraph(sev, lbl_style)]],
                  colWidths=[28*mm])
        )

    t = Table([rows], colWidths=[28*mm]*5)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE2),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("INNERGRID",     (0,0),(-1,-1), 0.5, C_BORDER),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 8),
        ("BOTTOMPADDING", (0,0),(-1,-1), 8),
    ]))
    return t

# ─────────────────────────────────────────────
#  RISK SCORE VISUAL
# ─────────────────────────────────────────────
def build_risk_score_table(score, rating, styles):
    score_color = C_RED if score >= 7 else C_ORANGE if score >= 4 else C_ACCENT
    score_style = ParagraphStyle("rs", fontName="Helvetica-Bold", fontSize=40,
                                 textColor=score_color, leading=44, alignment=TA_CENTER)
    denom_style = ParagraphStyle("rd", fontName="Helvetica", fontSize=12,
                                 textColor=C_MUTED, leading=16, alignment=TA_CENTER)
    rating_style = ParagraphStyle("rr", fontName="Helvetica-Bold", fontSize=9,
                                  textColor=score_color, leading=12, alignment=TA_CENTER,
                                  letterSpacing=1)
    t = Table([
        [Paragraph(str(score), score_style)],
        [Paragraph("/10", denom_style)],
        [Paragraph(rating, rating_style)],
    ], colWidths=[40*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE2),
        ("BOX",           (0,0),(-1,-1), 1, score_color),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
    ]))
    return t

# ─────────────────────────────────────────────
#  COVER PAGE
# ─────────────────────────────────────────────
def build_cover(data, styles):
    story = []
    story.append(Spacer(1, 32*mm))

    # Logo text
    logo_style = ParagraphStyle("logo", fontName="Helvetica-Bold", fontSize=14,
                                textColor=C_TEXT, leading=18, letterSpacing=3)
    accent_logo = ParagraphStyle("logo2", fontName="Helvetica-Bold", fontSize=14,
                                 textColor=C_ACCENT, leading=18, letterSpacing=3)

    logo_row = Table([[
        Paragraph("AEGIS", logo_style),
        Paragraph("CORE", accent_logo),
    ]], colWidths=[18*mm, 20*mm])
    logo_row.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "LEFT"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
    ]))
    story.append(logo_row)
    story.append(Spacer(1, 6*mm))

    # Accent line
    story.append(HRFlowable(width="100%", thickness=1, color=C_ACCENT, spaceAfter=8*mm))

    # Title
    story.append(Paragraph("SECURITY ASSESSMENT", styles["cover_title"]))
    story.append(Paragraph("REPORT", styles["cover_accent"]))
    story.append(Spacer(1, 4*mm))

    # Assessment type tag
    tag_style = ParagraphStyle("tag", fontName="Helvetica-Bold", fontSize=9,
                               textColor=C_ACCENT, leading=12, letterSpacing=2)
    story.append(Paragraph(data["assessment_type"].upper(), tag_style))
    story.append(Spacer(1, 16*mm))

    # Meta table
    meta_items = [
        ("Client",       data["client_name"]),
        ("Contact",      f"{data['contact_name']}  •  {data['contact_role']}"),
        ("Target",       data["client_domain"]),
        ("Scope",        data["scope"]),
        ("Test Period",  f"{data['start_date']} — {data['end_date']}"),
        ("Report Date",  data["report_date"]),
        ("Assessor",     data["assessor"]),
        ("Classification", "CONFIDENTIAL"),
    ]
    lbl_s = ParagraphStyle("ml", fontName="Helvetica", fontSize=9,
                           textColor=C_MUTED, leading=16)
    val_s = ParagraphStyle("mv", fontName="Helvetica-Bold", fontSize=9,
                           textColor=C_TEXT, leading=16)
    meta_rows = [[Paragraph(k, lbl_s), Paragraph(v, val_s)] for k,v in meta_items]
    mt = Table(meta_rows, colWidths=[38*mm, 110*mm])
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("LINEBELOW",     (0,0),(-1,-2), 0.5, C_BORDER),
        ("ALIGN",         (0,0),(0,-1),  "LEFT"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 6),
        ("BOTTOMPADDING", (0,0),(-1,-1), 6),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
        ("RIGHTPADDING",  (0,0),(-1,-1), 10),
    ]))
    story.append(mt)
    story.append(PageBreak())
    return story

# ─────────────────────────────────────────────
#  EXEC SUMMARY PAGE
# ─────────────────────────────────────────────
def build_exec_summary(data, styles):
    story = []
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("EXECUTIVE SUMMARY", styles["section_tag"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4*mm))
    story.append(Paragraph("Summary & Risk Overview", styles["section_title"]))
    story.append(Paragraph(data["executive_summary"], styles["body"]))
    story.append(Spacer(1, 8*mm))

    # Two-column: finding counts + risk score
    left = [
        [Paragraph("FINDINGS BY SEVERITY", styles["section_tag"])],
        [build_summary_table(data["findings"], styles)],
    ]
    left_t = Table(left, colWidths=[120*mm])
    left_t.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))

    right = [
        [Paragraph("OVERALL RISK SCORE", styles["section_tag"])],
        [build_risk_score_table(data["risk_score"], data["risk_rating"], styles)],
    ]
    right_t = Table(right, colWidths=[50*mm])
    right_t.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 2),
        ("BOTTOMPADDING",(0,0),(-1,-1), 2),
    ]))

    two_col = Table([[left_t, right_t]], colWidths=[120*mm, 50*mm])
    two_col.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "LEFT"),
        ("VALIGN", (0,0),(-1,-1), "TOP"),
        ("LEFTPADDING",  (0,0),(-1,-1), 0),
        ("RIGHTPADDING", (0,0),(-1,-1), 0),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
    ]))
    story.append(two_col)
    story.append(Spacer(1, 8*mm))

    # Remediation timeline table
    story.append(Paragraph("REMEDIATION TIMELINE", styles["section_tag"]))
    story.append(Spacer(1, 3*mm))
    t_header_s = ParagraphStyle("th2", fontName="Helvetica-Bold", fontSize=8,
                                textColor=C_MUTED, leading=12, letterSpacing=1)
    t_body_s   = ParagraphStyle("tb2", fontName="Helvetica", fontSize=9,
                                textColor=C_TEXT, leading=14)
    ids_s      = ParagraphStyle("ti2", fontName="Helvetica-Bold", fontSize=9,
                                textColor=C_ACCENT, leading=14)

    rows = [[Paragraph("TIMEFRAME", t_header_s), Paragraph("FINDING IDs", t_header_s)]]
    for timeframe, ids in data["remediation_timeline"]:
        rows.append([Paragraph(timeframe, t_body_s), Paragraph("  •  ".join(ids), ids_s)])

    rt = Table(rows, colWidths=[60*mm, 110*mm])
    rt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1, 0), C_SURFACE2),
        ("BACKGROUND",    (0,1),(-1,-1), C_SURFACE),
        ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
        ("LINEBELOW",     (0,0),(-1,-2), 0.5, C_BORDER),
        ("ALIGN",         (0,0),(-1,-1), "LEFT"),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1), 7),
        ("BOTTOMPADDING", (0,0),(-1,-1), 7),
        ("LEFTPADDING",   (0,0),(-1,-1), 10),
    ]))
    story.append(rt)
    story.append(PageBreak())
    return story

# ─────────────────────────────────────────────
#  DETAILED FINDINGS
# ─────────────────────────────────────────────
def build_findings(data, styles):
    story = []
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("DETAILED FINDINGS", styles["section_tag"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4*mm))
    story.append(Paragraph("Vulnerability Details & Remediation", styles["section_title"]))
    story.append(Spacer(1, 4*mm))

    for i, finding in enumerate(data["findings"]):
        sev   = finding["severity"]
        color = SEV_COLORS[sev]
        bg    = SEV_BG[sev]

        block = []

        # Finding header row: ID + severity badge
        id_s = ParagraphStyle("fid", fontName="Helvetica-Bold", fontSize=8,
                              textColor=C_MUTED, leading=12, letterSpacing=1)
        sev_s = ParagraphStyle("fsev", fontName="Helvetica-Bold", fontSize=8,
                               textColor=color, leading=12, letterSpacing=1)
        cvss_s = ParagraphStyle("fcvss", fontName="Helvetica-Bold", fontSize=8,
                                textColor=C_MUTED, leading=12)

        header_row = Table([[
            Paragraph(finding["id"], id_s),
            Paragraph(sev, sev_s),
            Paragraph(f"CVSS {finding['cvss']}", cvss_s),
        ]], colWidths=[20*mm, 30*mm, 120*mm])
        header_row.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg),
            ("TOPPADDING",    (0,0),(-1,-1), 6),
            ("BOTTOMPADDING", (0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        block.append(header_row)

        # Title
        title_t = Table([[Paragraph(finding["title"], styles["finding_title"])]],
                         colWidths=[170*mm])
        title_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE2),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        block.append(title_t)

        # Body sections
        sections = [
            ("DESCRIPTION", finding["description"]),
            ("IMPACT",       finding["impact"]),
            ("REMEDIATION",  finding["remediation"]),
        ]
        for lbl, txt in sections:
            lbl_t  = Table([[Paragraph(lbl, styles["label"])]],  colWidths=[170*mm])
            body_t = Table([[Paragraph(txt, styles["body_white"])]], colWidths=[170*mm])
            for t in (lbl_t, body_t):
                t.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,-1), C_SURFACE),
                    ("LEFTPADDING",   (0,0),(-1,-1), 10),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                    ("TOPPADDING",    (0,0),(-1,-1), 3),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 3),
                ]))
            block.append(lbl_t)
            block.append(body_t)

        # Bottom border
        border_t = Table([[""]], colWidths=[170*mm], rowHeights=[1])
        border_t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), color),
            ("TOPPADDING",    (0,0),(-1,-1), 0),
            ("BOTTOMPADDING", (0,0),(-1,-1), 0),
        ]))
        block.append(border_t)
        block.append(Spacer(1, 6*mm))

        story.append(KeepTogether(block))

    story.append(PageBreak())
    return story

# ─────────────────────────────────────────────
#  CLOSING PAGE
# ─────────────────────────────────────────────
def build_closing(data, styles):
    story = []
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("ABOUT THIS REPORT", styles["section_tag"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4*mm))
    story.append(Paragraph("Scope, Methodology & Disclaimer", styles["section_title"]))

    paras = [
        ("Scope", f"This assessment was limited to the domains and endpoints agreed upon in the "
                  f"authorization agreement signed before testing commenced. Scope: {data['scope']}."),
        ("Methodology", "AegisCore follows the OWASP Testing Guide (v4.2) and PTES (Penetration Testing "
                        "Execution Standard) methodology. Testing included automated scanning followed by "
                        "manual validation of all findings to eliminate false positives."),
        ("Confidentiality", "This report contains sensitive information about security vulnerabilities "
                            "in the client's systems. It must be treated as strictly confidential and "
                            "shared only with authorised personnel on a need-to-know basis."),
        ("Disclaimer", "AegisCore provides this report for informational purposes based on testing "
                       "conducted within the agreed scope and timeframe. Security assessments are "
                       "point-in-time evaluations. New vulnerabilities may emerge after the assessment date."),
        ("Retest Policy", "One complimentary retest is included for all Critical and High findings "
                          "within 30 days of this report. Contact your AegisCore assessor to schedule."),
    ]

    for heading, text in paras:
        story.append(Paragraph(heading.upper(), styles["label"]))
        story.append(Paragraph(text, styles["body"]))
        story.append(Spacer(1, 2*mm))

    story.append(Spacer(1, 10*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=6*mm))

    contact_s = ParagraphStyle("cs", fontName="Helvetica-Bold", fontSize=11,
                               textColor=C_TEXT, leading=16)
    story.append(Paragraph("Questions about this report?", contact_s))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("hello@aegiscore.in  •  +91 XXXXX XXXXX  •  aegiscore.in", styles["body"]))

    return story

# ─────────────────────────────────────────────
#  MAIN BUILD
# ─────────────────────────────────────────────
def build_report(data, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=18*mm,
        bottomMargin=16*mm,
        title=f"AegisCore Security Report — {data['client_name']}",
        author="AegisCore",
        subject="Security Assessment Report",
    )

    styles = make_styles()

    # Cover page needs no header/footer
    def cover_page(canv, doc):
        canv.saveState()
        canv.setFillColor(C_BG)
        canv.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Grid
        canv.setStrokeColor(colors.HexColor("#0D0F14"))
        canv.setLineWidth(0.5)
        step = 20 * mm
        for x in range(0, int(PAGE_W) + int(step), int(step)):
            canv.line(x, 0, x, PAGE_H)
        for y in range(0, int(PAGE_H) + int(step), int(step)):
            canv.line(0, y, PAGE_W, y)
        # Accent bar top
        canv.setFillColor(C_ACCENT)
        canv.rect(0, PAGE_H - 3, PAGE_W, 3, fill=1, stroke=0)
        # Accent bar bottom
        canv.rect(0, 0, PAGE_W, 3, fill=1, stroke=0)
        # Footer text
        canv.setFillColor(C_MUTED)
        canv.setFont("Helvetica", 7)
        canv.drawString(MARGIN, 5*mm, "CONFIDENTIAL — For authorised recipients only")
        canv.drawRightString(PAGE_W - MARGIN, 5*mm, f"© 2026 AegisCore")
        canv.restoreState()

    def inner_page(canv, doc):
        draw_page(canv, doc, data)

    # Build story
    story = []
    story += build_cover(data, styles)
    story += build_exec_summary(data, styles)
    story += build_findings(data, styles)
    story += build_closing(data, styles)

    # Use onFirstPage / onLaterPages
    doc.build(story, onFirstPage=cover_page, onLaterPages=inner_page)
    print(f"\n✓ Report generated: {output_path}")
    print(f"  Pages: check PDF viewer")
    print(f"  Client: {data['client_name']}")
    print(f"  Findings: {len(data['findings'])}")


if __name__ == "__main__":
    company_slug = REPORT_DATA["client_name"].lower().replace(" ", "_").replace(".", "")
    date_slug = datetime.date.today().strftime("%Y%m%d")
    output = f"aegiscore_report_{company_slug}_{date_slug}.pdf"
    build_report(REPORT_DATA, output)
