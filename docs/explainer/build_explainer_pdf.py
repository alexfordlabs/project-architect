#!/usr/bin/env python3
# Author: Alexander Ford <alex@alexfordlabs.com>
# Repository: https://github.com/alexfordlabs/project-architect
# License: MIT
"""Render the project-architect explainer PDF in the brand style.

Brand basis: the workspace brand style guide + press-kit brand-kit
             (brand-guidelines.html, the canonical reference render) — kept
             locally, not vendored into this repo.

Palette V5 only — pure black ink + paper + violet. Typography is Geist +
Geist Mono (OTFs converted to TTF via otf2ttf, stored alongside this script
under ./fonts/). Page geometry is A4 portrait with Pseudo's mm-based margins.
"""

import os

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
OUTFILE = os.path.join(HERE, "project-architect-explainer.pdf")


# ── Palette V5 ─────────────────────────────────────────────────────────────
INK = HexColor("#0A0A0A")
INK_SOFT = HexColor("#1F2333")
INK_2 = HexColor("#555E78")
HAIRLINE = HexColor("#E5E5EA")
PAPER = HexColor("#FFFFFF")
PAPER_SOFT = HexColor("#FAFBFD")
GRID = HexColor("#F3F3F6")
VIOLET = HexColor("#7C3AED")
VIOLET_DARK = HexColor("#8B5CF6")
CODE_BG = HexColor("#0F1322")
CODE_INK = HexColor("#E4E7F1")


# ── Fonts ──────────────────────────────────────────────────────────────────
def register_fonts():
    pairs = [
        ("Geist", "Geist-Regular.ttf"),
        ("Geist-Medium", "Geist-Medium.ttf"),
        ("Geist-Semi", "Geist-SemiBold.ttf"),
        ("Geist-Bold", "Geist-Bold.ttf"),
        ("Geist-Italic", "Geist-Italic.ttf"),
        ("GeistMono", "GeistMono-Regular.ttf"),
        ("GeistMono-Medium", "GeistMono-Medium.ttf"),
        ("GeistMono-Semi", "GeistMono-SemiBold.ttf"),
        ("GeistMono-Bold", "GeistMono-Bold.ttf"),
        ("GeistMono-XB", "GeistMono-ExtraBold.ttf"),
    ]
    for name, fn in pairs:
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fn)))


# ── Page geometry (A4 portrait, Pseudo brand margins) ──────────────────────
PAGE = A4  # 210 × 297 mm
M_LEFT = 20 * mm
M_RIGHT = 20 * mm
M_TOP = 22 * mm
M_BOTTOM = 22 * mm
CONTENT_W = PAGE[0] - M_LEFT - M_RIGHT


# ── Styles ─────────────────────────────────────────────────────────────────
def make_styles():
    s = getSampleStyleSheet()
    body = ParagraphStyle(
        "body",
        parent=s["BodyText"],
        fontName="Geist",
        fontSize=10.5,
        leading=16,
        textColor=INK_SOFT,
        spaceBefore=0,
        spaceAfter=2.5 * mm,
        alignment=TA_LEFT,
    )
    return {
        "body": body,
        "lede": ParagraphStyle(
            "lede",
            parent=body,
            fontSize=11.5,
            leading=18,
            textColor=INK_SOFT,
            spaceAfter=4 * mm,
        ),
        "kicker": ParagraphStyle(
            "kicker",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=9,
            leading=11,
            textColor=VIOLET,
            spaceBefore=0,
            spaceAfter=3 * mm,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=body,
            fontName="GeistMono-XB",
            fontSize=28,
            leading=32,
            textColor=INK,
            spaceBefore=0,
            spaceAfter=4 * mm,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=body,
            fontName="GeistMono-Bold",
            fontSize=10,
            leading=13,
            textColor=INK,
            spaceBefore=5 * mm,
            spaceAfter=2.5 * mm,
        ),
        "h3": ParagraphStyle(
            "h3",
            parent=body,
            fontName="GeistMono-Bold",
            fontSize=9,
            leading=12,
            textColor=INK,
            spaceBefore=3.5 * mm,
            spaceAfter=1.2 * mm,
        ),
        "small": ParagraphStyle(
            "small",
            parent=body,
            fontSize=9,
            leading=13,
            textColor=INK_2,
        ),
        "code": ParagraphStyle(
            "code",
            parent=body,
            fontName="GeistMono",
            fontSize=8.5,
            leading=13,
            textColor=CODE_INK,
            spaceBefore=2 * mm,
            spaceAfter=4 * mm,
        ),
        "callout": ParagraphStyle(
            "callout",
            parent=body,
            fontSize=10,
            leading=15,
            textColor=INK_SOFT,
            spaceBefore=0,
            spaceAfter=0,
        ),
        "quote": ParagraphStyle(
            "quote",
            parent=body,
            fontName="Geist-Italic",
            fontSize=12,
            leading=18,
            textColor=INK,
            leftIndent=6 * mm,
            spaceBefore=3 * mm,
            spaceAfter=4 * mm,
        ),
        # Cover-specific
        "cover_topmark": ParagraphStyle(
            "cover_topmark",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=10,
            leading=12,
            textColor=INK_2,
            alignment=TA_LEFT,
        ),
        "cover_topright": ParagraphStyle(
            "cover_topright",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=10,
            leading=12,
            textColor=INK_2,
            alignment=TA_RIGHT,
        ),
        "cover_eyebrow": ParagraphStyle(
            "cover_eyebrow",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=10,
            leading=13,
            textColor=VIOLET,
            alignment=TA_CENTER,
        ),
        "cover_word": ParagraphStyle(
            "cover_word",
            parent=body,
            fontName="GeistMono-XB",
            fontSize=36,
            leading=42,
            textColor=INK,
            alignment=TA_CENTER,
        ),
        "cover_tag": ParagraphStyle(
            "cover_tag",
            parent=body,
            fontName="Geist",
            fontSize=14,
            leading=21,
            textColor=INK_SOFT,
            alignment=TA_CENTER,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=9,
            leading=12,
            textColor=INK_2,
            alignment=TA_CENTER,
        ),
        "footer_l": ParagraphStyle(
            "footer_l",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=10,
            leading=12,
            textColor=INK,
            alignment=TA_LEFT,
        ),
        "footer_r": ParagraphStyle(
            "footer_r",
            parent=body,
            fontName="GeistMono-Medium",
            fontSize=10,
            leading=12,
            textColor=INK_2,
            alignment=TA_RIGHT,
        ),
    }


# ── Page painters ──────────────────────────────────────────────────────────
def body_page(canv: canvas.Canvas, doc):
    canv.saveState()
    w, h = PAGE
    canv.setFont("GeistMono-Medium", 7.5)
    canv.setFillColor(INK_2)
    canv.drawString(
        M_LEFT, M_BOTTOM - 12, "project-architect · explainer v2.3.0"
    )
    total_pages_placeholder = ""  # rendered without total — keeps single-pass
    canv.drawRightString(
        w - M_RIGHT, M_BOTTOM - 12, f"{doc.page}{total_pages_placeholder}"
    )
    canv.restoreState()


def cover_page(canv: canvas.Canvas, doc):
    """Sparse cover — no header, no footer; the wordmark IS the page."""
    canv.saveState()
    # Page intentionally bare. Painters for body kick in from page 2 onward.
    canv.restoreState()


# ── Helpers ────────────────────────────────────────────────────────────────
def hairline_rule(width=CONTENT_W, color=HAIRLINE, height=0.4):
    t = Table([[""]], colWidths=[width], rowHeights=[height])
    t.setStyle(
        TableStyle(
            [
                ("LINEABOVE", (0, 0), (-1, -1), 0.4, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def violet_rule(width=14 * mm, height=1.2 * mm):
    t = Table([[""]], colWidths=[width], rowHeights=[height])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), VIOLET),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def code_block(text, styles):
    safe = (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
        .replace("  ", "&nbsp;&nbsp;")
    )
    p = Paragraph(safe, styles["code"])
    t = Table([[p]], colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )
    return t


def callout_panel(body_html, styles):
    inner = Paragraph(body_html, styles["callout"])
    t = Table([[inner]], colWidths=[CONTENT_W])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PAPER_SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 2, VIOLET),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]
        )
    )
    return t


def two_col_table(rows, header, key_w=58 * mm):
    val_w = CONTENT_W - key_w
    data = [list(header)] + list(rows)
    t = Table(data, colWidths=[key_w, val_w])
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONT", (0, 1), (-1, -1), "Geist", 10),
        ("TEXTCOLOR", (0, 1), (-1, -1), INK_SOFT),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6 * mm),
        ("TOPPADDING", (0, 1), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 2 * mm),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, HAIRLINE),
        # Header row
        ("FONT", (0, 0), (-1, 0), "GeistMono-Bold", 8.5),
        ("TEXTCOLOR", (0, 0), (-1, 0), INK_2),
        ("TOPPADDING", (0, 0), (-1, 0), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2 * mm),
        ("LINEBELOW", (0, 0), (-1, 0), 1.0, INK),
    ]
    t.setStyle(TableStyle(style))
    return t


def compare_table(rows):
    """Two-column comparison: bad vs good. Hairline-bordered, no fills."""
    t = Table(rows, colWidths=[CONTENT_W / 2.0, CONTENT_W / 2.0])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
                ("LINEABOVE", (0, 0), (-1, 0), 1.0, INK),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, HAIRLINE),
                ("LINEAFTER", (0, 0), (0, -1), 0.3, HAIRLINE),
            ]
        )
    )
    return t


# ── Content ────────────────────────────────────────────────────────────────
def build():
    register_fonts()
    styles = make_styles()

    doc = BaseDocTemplate(
        OUTFILE,
        pagesize=PAGE,
        leftMargin=M_LEFT,
        rightMargin=M_RIGHT,
        topMargin=M_TOP,
        bottomMargin=M_BOTTOM,
        title="project-architect — Explainer v2.3.0",
        author="Alexander Ford",
        subject="What project-architect is, why it works, and who it's for.",
        keywords="project-architect, Claude Code, vibe coding, ADR, architecture",
    )
    frame = Frame(
        M_LEFT,
        M_BOTTOM,
        PAGE[0] - M_LEFT - M_RIGHT,
        PAGE[1] - M_TOP - M_BOTTOM,
        id="body",
        showBoundary=0,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    cover_tpl = PageTemplate(id="cover", frames=[frame], onPage=cover_page)
    body_tpl = PageTemplate(id="body", frames=[frame], onPage=body_page)
    doc.addPageTemplates([cover_tpl, body_tpl])

    story = []

    # ── COVER ──────────────────────────────────────────────────────────
    # Top row: mark / version
    top_row = Table(
        [
            [
                Paragraph("project-architect", styles["cover_topmark"]),
                Paragraph("v2.3.0 · May 2026", styles["cover_topright"]),
            ]
        ],
        colWidths=[CONTENT_W / 2, CONTENT_W / 2],
    )
    top_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(top_row)
    story.append(Spacer(1, 50 * mm))

    story.append(Paragraph("AN&nbsp;&nbsp;EXPLAINER", styles["cover_eyebrow"]))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("project-architect", styles["cover_word"]))
    story.append(Spacer(1, 14 * mm))
    # Violet rule, centered
    rule_table = Table([[violet_rule(width=14 * mm, height=1.2 * mm)]], colWidths=[CONTENT_W])
    rule_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(rule_table)
    story.append(Spacer(1, 14 * mm))
    story.append(
        Paragraph(
            "An orchestrator that decides <i>what to build</i><br/>"
            "before Claude Code writes a single line.",
            styles["cover_tag"],
        )
    )
    story.append(Spacer(1, 8 * mm))
    story.append(
        Paragraph(
            "11 PHASES&nbsp;&nbsp;·&nbsp;&nbsp;6 SUBAGENTS&nbsp;&nbsp;·&nbsp;&nbsp;"
            "19+ PROJECT TYPES&nbsp;&nbsp;·&nbsp;&nbsp;16-CHECK QUALITY GATE",
            styles["cover_sub"],
        )
    )

    # Bottom row of cover
    story.append(Spacer(1, 50 * mm))
    foot_row = Table(
        [
            [
                Paragraph(
                    "ALEX FORD LABS<br/>"
                    '<font color="#555E78" size="9">ALEX FORD LABS · MIT</font>',
                    styles["footer_l"],
                ),
                Paragraph(
                    "GITHUB.COM/ALEXFORDLABS/<br/>"
                    '<font color="#555E78" size="9">PROJECT-ARCHITECT</font>',
                    styles["footer_r"],
                ),
            ]
        ],
        colWidths=[CONTENT_W / 2, CONTENT_W / 2],
    )
    foot_row.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(foot_row)

    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ── §1  What is it ─────────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;01 &nbsp; WHAT IT IS", styles["kicker"]))
    story.append(
        Paragraph(
            "A skill that interviews you<br/>before it builds anything.",
            styles["h1"],
        )
    )
    story.append(
        Paragraph(
            "<b>project-architect</b> is a Claude Code <i>orchestrator skill</i>. "
            "You install it, point it at an empty folder, and tell it what you want to "
            "build — in one sentence. From there it conducts a structured conversation "
            "across eleven phases, ending with a fully-committed repository: design docs, "
            "Architecture Decision Records, a per-folder <font name=\"GeistMono\">CLAUDE.md</font> "
            "router, a <font name=\"GeistMono\">.claude/</font> tooling configuration, and three "
            "router slash commands (<font name=\"GeistMono\">/scaffold</font>, "
            "<font name=\"GeistMono\">/implement</font>, "
            "<font name=\"GeistMono\">/iterate-design</font>) wired and ready.",
            styles["lede"],
        )
    )
    story.append(
        Paragraph(
            "Not a generator. Not a template. An <b>interview</b>. The skill asks you to "
            "decide — with research backing each option — what your stack should be, what "
            "your interface should feel like, what your authentication model is, what your "
            "deployment target is, what your error budget looks like. Every meaningful "
            "decision is filed as an ADR. By the time anyone writes code, the project has "
            "already been thought through.",
            styles["body"],
        )
    )
    story.append(
        callout_panel(
            "<b>The shortest definition.</b> &nbsp; project-architect makes the boring, "
            "important decisions <i>visible</i> — and then makes them <i>portable</i>, by "
            "writing them down in a form future-you and future-Claude can both read.",
            styles,
        )
    )

    # ── §2  Why it works ──────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;02 &nbsp; WHY IT WORKS", styles["kicker"]))
    story.append(
        Paragraph(
            "&ldquo;Vibe coding&rdquo;<br/>deserves a real architect.",
            styles["h1"],
        )
    )
    story.append(
        Paragraph(
            "There is a thing happening in software right now that the industry hasn't named "
            "well yet. People call it <b>vibe coding</b> — describing what you want in plain "
            "English and letting an AI write the code. It works astonishingly well for short "
            "tasks. It falls apart somewhere around hour three of a new project, when the "
            "model is confidently producing code that contradicts a decision it made an hour "
            "ago, in a file it has now forgotten exists.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "The failure mode isn't intelligence. The failure mode is <b>missing context</b>. "
            "Models, like people, work better when they know what's been decided. The "
            "difference is that a person remembers decisions implicitly — the AI does not.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "<b>project-architect's bet</b> is simple: front-load the decisions. Make them "
            "explicit. Write them down in a place the AI will re-read at the start of every "
            "future session. Then — and only then — start coding.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "&ldquo;The senior engineer's superpower isn't writing code faster. "
            "It's deciding which code <i>not</i> to write. project-architect is that "
            "decision conversation, captured.&rdquo;",
            styles["quote"],
        )
    )

    story.append(PageBreak())

    # ── §3  The shift ──────────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;03 &nbsp; THE SHIFT", styles["kicker"]))
    story.append(
        Paragraph("From code-first<br/>to decision-first.", styles["h1"])
    )
    story.append(
        Paragraph(
            "The industry-standard, mature way to start a serious project — long before AI "
            "entered the room — looks like this: you write a one-page brief, you do a "
            "tech-stack RFC, you draft a CLAUDE.md, you file an ADR or two, you produce a "
            "scaffold plan, and only after all of that do you start typing into "
            "<font name=\"GeistMono\">main.ts</font>. Most teams skip these steps because "
            "they are tedious, undirected, and easy to put off. project-architect's job is "
            "to make them <i>fast and pleasant</i> by turning them into a guided conversation.",
            styles["body"],
        )
    )

    rows = [
        [
            Paragraph(
                "<font name=\"GeistMono-Bold\" color=\"#0A0A0A\" size=\"8.5\">"
                "CODE&nbsp;-&nbsp;FIRST&nbsp;&nbsp;(THE&nbsp;TRAP)</font>",
                styles["body"],
            ),
            Paragraph(
                "<font name=\"GeistMono-Bold\" color=\"#7C3AED\" size=\"8.5\">"
                "DECISION&nbsp;-&nbsp;FIRST&nbsp;&nbsp;(THE&nbsp;ALTERNATIVE)</font>",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "Open Claude. Paste a paragraph. Watch a file tree appear. Realise on day "
                "three you picked the wrong runtime, the wrong ORM, and the wrong auth "
                "story. Refactor. Re-paste. Repeat.",
                styles["body"],
            ),
            Paragraph(
                "Open Claude. Run <font name=\"GeistMono\">/project-architect</font>. Answer "
                "eight multiple-choice questions about scope and constraints, six about the "
                "stack, four about architecture. Read the research notes the skill brought "
                "back. Approve the ADRs. <i>Then</i> let the scaffold land.",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "AI has no shared memory across sessions. Every restart re-derives "
                "everything from the current state of the code — which means earlier "
                "tradeoffs are invisible.",
                styles["body"],
            ),
            Paragraph(
                "Every decision is written into <font name=\"GeistMono\">docs/decisions/</font> "
                "as an ADR. <font name=\"GeistMono\">CLAUDE.md</font> auto-loads at session "
                "start. Future-you and future-Claude both see <i>why</i>, not just <i>what</i>.",
                styles["body"],
            ),
        ],
        [
            Paragraph(
                "&ldquo;Vibe coding doesn't scale.&rdquo;",
                styles["body"],
            ),
            Paragraph(
                "Vibe coding scales <i>beautifully</i> once you front-load the architecture. "
                "The vibe becomes <i>iteration speed</i> on a foundation that holds up.",
                styles["body"],
            ),
        ],
    ]
    story.append(compare_table(rows))

    story.append(PageBreak())

    # ── §4  How it works ──────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;04 &nbsp; HOW IT WORKS", styles["kicker"]))
    story.append(
        Paragraph("Eleven phases,<br/>explained without jargon.", styles["h1"])
    )
    story.append(
        Paragraph(
            "Each phase has a focused job. None of them are negotiable, but most of them "
            "are fast — typical bootstrap, from elevator pitch to locked v1.0 design, "
            "runs in about 90 minutes. Here is what happens, in human language:",
            styles["body"],
        )
    )

    phases = [
        ("Preflight", "Checks the room: are you on Opus 4.7 with max effort? Are the recommended companion plugins installed? Is your project-architect copy current? Surfaces problems before they cost you an hour."),
        ("Repo Init (optional)", "If the directory has no git yet, offers <font name=\"GeistMono\">git init</font> and optionally <font name=\"GeistMono\">gh repo create</font>. Skip if you already have a repo."),
        ("Universal Kickoff", "Eight multi-choice questions. What type of thing is this? Who's the user? What's the time budget? Classifies your project into one of 19+ types so subsequent questions are relevant, not generic."),
        ("Vision &amp; Scope", "Type-specific drill-down. For a CLI tool: who runs it, on what OS, how do they discover commands? For a web app: auth model, multi-tenant or not, payments? A research-scout subagent fetches up-to-date context at the end of the phase."),
        ("Tech Stack", "Real options, not opinions-from-2023. Per language, the skill picks the right CLI-UX library, the right web framework, the right database. Every major choice becomes an ADR. The skill runs cost research before recommending paid services."),
        ("Cost Modeling", "If your stack touches a metered service — Vercel, Supabase, AWS Bedrock, anything per-token — the skill estimates monthly cost at your expected scale. Filed into <font name=\"GeistMono\">COST_MODEL.md</font>."),
        ("Architecture Deep Dive", "Per-area drilling: how do auth tokens flow, what's the cache invalidation story, what's the failure-injection surface? Inline consistency-check so the architecture doesn't contradict the tech-stack choices."),
        ("Document Generation", "The big moment. <i>document-author</i> subagents run in parallel and write every design doc the project type requires. <i>quality-gate-auditor</i> then runs 16 cross-cutting checks (link integrity, ADR coverage, no placeholder text, consistent numbers, etc.). Findings auto-seed the next phase."),
        ("Iteration", "You read what's been written. The skill presents a menu of auditor findings plus open questions. Want to revisit the database choice? <i>decision-revisor</i> re-opens it, supersedes the old ADR, and updates every doc that referenced it."),
        ("Post-Generation Setup (LOCK)", "Final commit. Snapshot the docs to <font name=\"GeistMono\">docs/versions/v1.0/</font>. Set <font name=\"GeistMono\">state.locked&nbsp;=&nbsp;true</font>. From here on, design changes go through Phase 5 explicitly — no drift."),
        ("Tooling Execution + Handoff", "Two specialised authors (<i>claude-md-author</i>, <i>claude-tooling-author</i>) consume the plan docs from Phase 4 and emit the final <font name=\"GeistMono\">CLAUDE.md</font> tree and <font name=\"GeistMono\">.claude/</font> tooling. Then prints a restart message — future sessions auto-load the new <font name=\"GeistMono\">CLAUDE.md</font> as a router with <font name=\"GeistMono\">/scaffold</font>, <font name=\"GeistMono\">/implement&nbsp;&lt;feature&gt;</font>, <font name=\"GeistMono\">/iterate-design</font> available."),
    ]
    for name, body_html in phases:
        story.append(Paragraph(name.upper(), styles["h3"]))
        story.append(Paragraph(body_html, styles["body"]))

    story.append(Spacer(1, 2 * mm))
    story.append(
        callout_panel(
            "<b>Why eleven phases and not five.</b> &nbsp; Every phase exists because skipping "
            "it produced a measurable, recurring failure during real bootstraps. The "
            "quality-gate auditor exists because docs drifted from decisions. The LOCK phase "
            "exists because designs kept regressing. Phase 7 exists because "
            "<font name=\"GeistMono\">CLAUDE.md</font> kept getting written without a plan. "
            "Each phase pays for its own existence in problems it prevents.",
            styles,
        )
    )

    story.append(PageBreak())

    # ── §5  For developers ────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;05 &nbsp; FOR DEVELOPERS", styles["kicker"]))
    story.append(
        Paragraph(
            "The fastest path<br/>from idea to defensible architecture.",
            styles["h1"],
        )
    )
    story.append(
        Paragraph(
            "If you've been doing this for a while, you already know the value of an ADR, "
            "the pain of a stale <font name=\"GeistMono\">CLAUDE.md</font>, and the cost of "
            "discovering at deploy time that your framework can't do what you assumed. "
            "project-architect's offer to you is straightforward:",
            styles["body"],
        )
    )

    bullets = [
        ("<b>One conversation</b> replaces what would otherwise be a week of solo RFC-writing. "
         "The skill remembers everything you decide and never asks twice."),
        ("<b>Every decision is an ADR.</b> Sequential, supersession-aware, with a full audit "
         "trail. If you change your mind about the database in Phase 5, every doc that "
         "mentioned the old choice gets rewritten — automatically, with a new ADR filed "
         "superseding the old one."),
        ("<b>The 16-check quality gate</b> runs after every doc-generation pass. It catches "
         "link rot, missing ADR references, broken JSON, drift in numbers across docs, "
         "ISO8601 timestamp violations, unresolved placeholders, and ten other things you'd "
         "otherwise discover three months in."),
        ("<b>Type-aware questioning.</b> 19+ project types, each with its own decision tree. "
         "A CLI tool doesn't get asked about CDN caching; a SaaS doesn't get asked about "
         "<font name=\"GeistMono\">termios</font>. v2.3 added programming-language design "
         "as a first-class type, with 7 dedicated templates and 4 decision axes."),
        ("<b>Phase 7 hands off cleanly</b> to <font name=\"GeistMono\">superpowers:writing-plans</font> "
         "for the actual implementation. The scaffold plan emitted by Phase 4 is exactly the "
         "input that <i>subagent-driven-development</i> wants. The boundary between "
         "<i>design</i> and <i>code</i> is sharp — and reversible."),
    ]
    for b in bullets:
        story.append(Paragraph("&nbsp;&nbsp;<font color=\"#7C3AED\">·</font>&nbsp;&nbsp; " + b, styles["body"]))

    story.append(Spacer(1, 2 * mm))
    story.append(
        Paragraph(
            "<b>The dirty secret:</b> the people who already write ADRs by hand love this "
            "skill the most. It is not lowering the floor for them — it is raising the "
            "ceiling. The skill makes it cheap to file four ADRs when you would have filed "
            "one, because each one takes ninety seconds of clicking instead of fifteen "
            "minutes of writing.",
            styles["body"],
        )
    )

    story.append(PageBreak())

    # ── §6  For non-developers ────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;06 &nbsp; FOR NON-DEVELOPERS", styles["kicker"]))
    story.append(
        Paragraph(
            "If you can describe your idea,<br/>you can ship a real architecture.",
            styles["h1"],
        )
    )
    story.append(
        Paragraph(
            "Here is the thing the AI hype cycle keeps half-saying and never quite finishing: "
            "the bottleneck for non-developers building software has never been the code. It "
            "has been the <b>decisions</b>. Which framework? Which database? Which auth "
            "provider? Which hosting? Which payment processor? Each one has eight options, "
            "every option has tradeoffs, and there is no way to evaluate them without "
            "experience you don't have yet.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "project-architect was designed so that someone who has never written production "
            "code can sit down, answer questions in plain language, and walk away with the "
            "same artifact a senior engineer would have produced — design docs, ADRs, a "
            "tech-stack rationale grounded in actual research, a cost estimate, and a "
            "scaffold plan ready to hand to Claude for implementation.",
            styles["body"],
        )
    )

    story.append(Paragraph("WHAT IT LOOKS LIKE FOR YOU, CONCRETELY", styles["h3"]))
    bullets2 = [
        ("<b>Questions are multiple-choice</b>, not free-form. You pick from real options the "
         "skill has researched. If you don't know what JWT means, the skill explains it inline "
         "before asking you to choose."),
        ("<b>Tradeoffs are surfaced, not hidden.</b> &ldquo;Option A is faster to ship and "
         "locks you into vendor X; Option B is slower to ship but portable.&rdquo; You make "
         "the call; the skill doesn't pretend there's a right answer."),
        ("<b>Cost is estimated in dollars per month</b>, at your expected scale, before you "
         "commit. No more discovering that the AI-powered features you assumed were "
         "&ldquo;included&rdquo; will cost $1,200/month at 10,000 users."),
        ("<b>The end product is something you can show a developer.</b> &ldquo;Here is my "
         "design doc, here are my ADRs, here is my architecture.&rdquo; You will be taken "
         "seriously, because the artifact is taken seriously. The format is the same one "
         "engineering teams use internally."),
        ("<b>If you decide to ship it yourself,</b> the <font name=\"GeistMono\">/scaffold</font> "
         "and <font name=\"GeistMono\">/implement</font> commands wired up at the end give "
         "Claude Code the context it needs to write the actual code — chunk by chunk, on the "
         "foundation you already designed."),
    ]
    for b in bullets2:
        story.append(Paragraph("&nbsp;&nbsp;<font color=\"#7C3AED\">·</font>&nbsp;&nbsp; " + b, styles["body"]))

    story.append(Spacer(1, 2 * mm))
    story.append(
        callout_panel(
            "<b>This is the real story of vibe coding.</b> &nbsp; It is not &ldquo;AI replaces "
            "engineers.&rdquo; It is &ldquo;the gap between <i>knowing what you want</i> and "
            "<i>shipping it</i> just collapsed&rdquo; — but only for people who let the AI "
            "see the architecture first. project-architect is the bridge.",
            styles,
        )
    )

    story.append(PageBreak())

    # ── §7  What you get ──────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;07 &nbsp; WHAT YOU GET", styles["kicker"]))
    story.append(Paragraph("Artifacts, not promises.", styles["h1"]))
    story.append(
        Paragraph(
            "At the end of a bootstrap, your repository contains the following — all "
            "committed, all readable, all consumable by future Claude sessions:",
            styles["body"],
        )
    )

    artifacts = [
        ("CLAUDE.md + per-folder", "A root router that loads into every Claude session, plus folder-level overlays where conventions differ. Future sessions wake up with full project context."),
        ("docs/PROJECT_OVERVIEW.md", "The master hub. Vision, scope, decisions, links to every other doc. The first thing anyone — human or AI — should read."),
        ("docs/decisions/ (ADRs)", "Every meaningful tradeoff. Sequentially numbered, supersession-tracked, dated. If a decision changes later, the chain shows the evolution."),
        ("docs/research/", "Every research-scout finding the skill ran, archived. You can re-read the comparison that justified your runtime choice three months later."),
        ("docs/*_PLAN.md", "Four design-first plan docs from Phase 4 (CLAUDE_MD, CLAUDE_TOOLING, SCAFFOLD, NEXT_STEP). Phase 7 consumes the first two; superpowers:writing-plans consumes the third; you consume the fourth."),
        ("docs/versions/v1.0/", "Snapshot of every design doc at the moment of LOCK. If you regret something in v1.1, you can diff against this."),
        (".claude/", "Stack-aware tooling — settings.json, hooks for lint-on-save and test-on-stop, custom agents, slash commands. Tightened permissions when fewer-permission-prompts is installed."),
        (".claude/commands/", "Three router slash commands wired up: /scaffold (kick off implementation), /implement &lt;feature&gt; (add a feature on the existing architecture), /iterate-design (re-open the design loop without losing locked state)."),
        ("docs/_architect_state.json", "The skill's own memory. Survives across sessions. Re-invocation enters wherever you left off."),
    ]
    rows = []
    for name, desc in artifacts:
        rows.append(
            [
                Paragraph(
                    f'<font name="GeistMono-Bold" color="#0A0A0A" size="9.5">{name}</font>',
                    styles["body"],
                ),
                Paragraph(desc, styles["body"]),
            ]
        )
    story.append(two_col_table(rows, header=("ARTIFACT", "WHAT IT IS"), key_w=56 * mm))

    story.append(PageBreak())

    # ── §8  Where it's going ──────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;08 &nbsp; WHERE IT'S GOING", styles["kicker"]))
    story.append(Paragraph("Future possibilities.", styles["h1"]))
    story.append(
        Paragraph(
            "v2.3 just added programming-language design as a first-class project sub-type — "
            "six PL flavours (general-purpose, DSL, query, configuration, educational, "
            "transpiler target) with seven dedicated design templates (grammar, semantics, "
            "type system, stdlib, toolchain, bootstrap plan, stability &amp; RFC) and four "
            "decision axes calibrated to the 2026 state-of-the-art (LLVM 22.x, Cranelift, "
            "QBE, GraalVM/Truffle 24/25 LTS, Wasm 3.0, BEAM, dependent types as in Lean 4).",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "The roadmap below is not a roadmap so much as a horizon. project-architect is "
            "iteratively shipped — each release responds to lessons from real bootstraps. "
            "Here is what looks reachable from where we are now:",
            styles["body"],
        )
    )

    future = [
        ("PL-specific auditor checks (v2.4)",
         "Grammar consistency, type-system soundness sketches, bootstrap-plan dependency cycles — quality-gate-auditor extended for the new programming-language type."),
        ("Polyglot stdlib design",
         "Cross-language standard library design for project types that span multiple runtimes — a single source of truth for naming and semantics across Rust, Go, and TypeScript."),
        ("Markup-language sub-type",
         "CommonMark variants, configuration markups, template languages — sibling to the programming-language sub-types, with its own template stack."),
        ("Live cost dashboards",
         "COST_MODEL.md auto-syncs with the actual bills from your hosting providers, so the design-time estimate becomes a runtime delta you can act on."),
        ("Multi-project workspaces",
         "Bootstrap a monorepo with three apps and shared packages — each gets its own design pass, all share a top-level architecture doc, consistency is auditor-enforced across packages."),
        ("Continuous architecture review",
         "After lock, ongoing PRs are checked against the locked design — drift surfaces as a PR comment, with a one-click /iterate-design path to make the change deliberately."),
        ("The teaching mode",
         "An optional &ldquo;explain why this matters&rdquo; toggle that, at every decision point, expands a sidebar with the engineering principles behind the question. project-architect as a learning instrument, not just a builder."),
    ]
    rows = []
    for name, desc in future:
        rows.append(
            [
                Paragraph(
                    f'<font name="GeistMono-Bold" color="#0A0A0A" size="9.5">{name}</font>',
                    styles["body"],
                ),
                Paragraph(desc, styles["body"]),
            ]
        )
    story.append(two_col_table(rows, header=("DIRECTION", "WHY IT WOULD MATTER"), key_w=58 * mm))

    story.append(PageBreak())

    # ── §9  Try it ────────────────────────────────────────────────────
    story.append(Paragraph("§&nbsp;&nbsp;09 &nbsp; TRY IT", styles["kicker"]))
    story.append(Paragraph("Three commands to start.", styles["h1"]))
    story.append(
        Paragraph(
            "Open a terminal in a fresh directory. The whole bootstrap fits on a postcard:",
            styles["body"],
        )
    )
    story.append(
        code_block(
            "claude plugin marketplace add alexfordlabs/skills\n"
            "claude plugin install project-architect@alexfordlabs\n"
            "claude",
            styles,
        )
    )
    story.append(Paragraph("Then, inside Claude:", styles["body"]))
    story.append(
        code_block(
            "/effort max\n"
            "/model       → Opus 4.7 (1M context)\n"
            "/project-architect",
            styles,
        )
    )
    story.append(
        Paragraph(
            "Answer the questions. Read the research the skill brings back. Approve the "
            "ADRs. Read the docs that get generated. Iterate. Lock. Hand off to the "
            "scaffolder.",
            styles["body"],
        )
    )
    story.append(
        Paragraph(
            "Ninety minutes from now, your repository has a foundation that takes most "
            "teams a week of meetings to produce. You will not have written a single line "
            "of production code — and that is the point. The code is the easy part now. "
            "The decisions that <i>shape</i> the code were always the hard part. "
            "project-architect makes them <b>visible</b>, <b>portable</b>, and <b>cheap</b>.",
            styles["body"],
        )
    )

    story.append(Spacer(1, 3 * mm))
    story.append(
        callout_panel(
            "<b>The deeper aspiration.</b> &nbsp; If project-architect succeeds long-term, it "
            "is because it normalises something the industry already knows is true but "
            "rarely practises: <i>designing before coding pays for itself many times over.</i> "
            "AI didn't change that. AI made it cheaper. The window for &ldquo;just start "
            "vibe-coding and figure it out&rdquo; is real, but it ends at &mdash; "
            "conservatively &mdash; a thousand lines. Past that line, structure wins. "
            "Always has, always will.",
            styles,
        )
    )

    story.append(Spacer(1, 6 * mm))
    story.append(hairline_rule())
    story.append(Spacer(1, 4 * mm))
    story.append(
        Paragraph(
            '<font name="GeistMono-Bold" color="#0A0A0A">GITHUB.COM/ALEXFORDLABS/PROJECT-ARCHITECT</font> &nbsp;&nbsp;·&nbsp;&nbsp; '
            '<font name="GeistMono-Medium" color="#555E78">MIT LICENSED &nbsp;·&nbsp; v2.3.0 &nbsp;·&nbsp; MAY 2026</font>',
            styles["small"],
        )
    )
    story.append(
        Paragraph(
            '<font name="GeistMono-Medium" color="#7C3AED">★ SKILLFULLY MADE WITH PROJECT-ARCHITECT.</font>',
            styles["small"],
        )
    )

    doc.build(story)


if __name__ == "__main__":
    build()
    print(f"Wrote {OUTFILE}")
