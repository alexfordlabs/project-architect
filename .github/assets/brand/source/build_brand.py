#!/usr/bin/env python3
# Author: Alexander Ford <alex@alexfordlabs.com>
# Repository: https://github.com/alexfordlabs/project-architect
# License: MIT
"""Build the complete Alex Ford Labs brand-asset kit.

Outputs:
    lockup/   AF / LABS stack — primary lockup, 1:1 square
    mark/     AF only — favicon / avatar / app-icon
    wordmark/ AF · LABS inline — horizontal banner / README header
    social/   1280×640 social-preview composition

Each layout ships:
    · One SVG per variant (light + dark), text outline-converted via fontTools
    · PNGs at standard resolutions, rendered from the SVG via cairosvg

Font: Geist Mono ExtraBold (display) + Geist Mono Medium (subtext)
Palette: V5 (pure black ink + paper, no colour)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont


HERE = Path(__file__).resolve().parent
BRAND_DIR = HERE.parent
REPO_ROOT = BRAND_DIR.parent.parent.parent

FONT_DISPLAY = REPO_ROOT / "docs" / "explainer" / "fonts" / "GeistMono-ExtraBold.ttf"
FONT_SUB = REPO_ROOT / "docs" / "explainer" / "fonts" / "GeistMono-Medium.ttf"


# ── Palette V5 ─────────────────────────────────────────────────────────────
INK_HEX_LIGHT = "#0A0A0A"
PAPER_HEX_LIGHT = "#FFFFFF"
INK_HEX_DARK = "#FFFFFF"
PAPER_HEX_DARK = "#0A0A0A"


@dataclass
class Variant:
    name: str
    ink: str
    paper: str


VARIANTS = [
    Variant("light", INK_HEX_LIGHT, PAPER_HEX_LIGHT),
    Variant("dark", INK_HEX_DARK, PAPER_HEX_DARK),
]


# ── Font helpers ───────────────────────────────────────────────────────────


class FontProbe:
    def __init__(self, font_path):
        self.font = TTFont(str(font_path))
        self.cmap = self.font.getBestCmap()
        self.gs = self.font.getGlyphSet()
        self.upm = self.font["head"].unitsPerEm
        os2 = self.font["OS/2"]
        self.cap_height = getattr(os2, "sCapHeight", None) or 700
        self.ascender = self.font["hhea"].ascent
        self.descender = self.font["hhea"].descent

    def glyph_path(self, char):
        """Returns (path_d, advance_width)."""
        gname = self.cmap[ord(char)]
        glyph = self.gs[gname]
        pen = SVGPathPen(self.gs)
        glyph.draw(pen)
        return pen.getCommands(), glyph.width

    def measure_text(self, text):
        """Total advance width in font units (no letter-spacing)."""
        return sum(self.gs[self.cmap[ord(c)]].width for c in text)


# ── SVG composition primitives ─────────────────────────────────────────────


def svg_header(width, height, paper):
    return (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n'
        f'  <rect width="{width}" height="{height}" fill="{paper}"/>\n'
    )


def svg_footer():
    return "</svg>\n"


def text_as_paths(probe, text, x, baseline_y, font_size_svg, ink,
                  letter_spacing_svg=0.0):
    """Render text as <path> elements in SVG.

    `font_size_svg` is the desired em-square size in SVG units. The cap-height
    will appear smaller (cap_height / units_per_em × font_size_svg).

    `letter_spacing_svg` adds this many SVG units between consecutive glyphs
    (in addition to the glyph's natural advance width).
    """
    scale = font_size_svg / probe.upm
    out = []
    pen_x_units = 0
    for i, ch in enumerate(text):
        d, adv = probe.glyph_path(ch)
        pen_x_svg = x + pen_x_units * scale + i * letter_spacing_svg
        # The transform: translate to position, scale, flip Y so the glyph
        # ascends upward from baseline_y rather than downward.
        out.append(
            f'  <g transform="translate({pen_x_svg:.3f},{baseline_y:.3f}) '
            f'scale({scale:.6f},{-scale:.6f})">\n'
            f'    <path d="{d}" fill="{ink}"/>\n'
            f'  </g>\n'
        )
        pen_x_units += adv
    total_width_svg = pen_x_units * scale + (len(text) - 1) * letter_spacing_svg
    return "".join(out), total_width_svg


def text_width(probe, text, font_size_svg, letter_spacing_svg=0.0):
    scale = font_size_svg / probe.upm
    return probe.measure_text(text) * scale + (len(text) - 1) * letter_spacing_svg


def find_letter_spacing_for_width(probe, text, font_size_svg, target_width):
    """Solve for the letter_spacing_svg that makes `text` measure `target_width`."""
    natural = text_width(probe, text, font_size_svg, 0)
    if len(text) < 2 or target_width <= natural:
        return 0.0
    return (target_width - natural) / (len(text) - 1)


# ── Layout composers ───────────────────────────────────────────────────────


def compose_lockup_svg(variant, probe_disp, probe_sub, canvas=1024):
    """AF / LABS stack — primary lockup."""
    af_font_size = 520
    sub_font_size = 88

    # AF total width
    af_w = text_width(probe_disp, "AF", af_font_size)
    af_x = (canvas - af_w) / 2.0
    # Position AF so the cap top sits around y = 0.34 * canvas.
    cap_h_svg = probe_disp.cap_height * af_font_size / probe_disp.upm
    af_baseline_y = canvas * 0.34 + cap_h_svg / 2.0

    # Matched-width LABS spacing
    labs_spacing = find_letter_spacing_for_width(probe_sub, "LABS",
                                                 sub_font_size, af_w)
    labs_w = text_width(probe_sub, "LABS", sub_font_size, labs_spacing)
    labs_x = (canvas - labs_w) / 2.0
    rule_y = canvas * 0.66
    sub_cap_h_svg = probe_sub.cap_height * sub_font_size / probe_sub.upm
    labs_baseline_y = rule_y + 52 + sub_cap_h_svg

    body = svg_header(canvas, canvas, variant.paper)
    # AF
    af_paths, _ = text_as_paths(probe_disp, "AF", af_x, af_baseline_y,
                                af_font_size, variant.ink)
    body += af_paths
    # Hairline rule — matches AF width exactly
    body += (
        f'  <rect x="{af_x:.3f}" y="{rule_y:.3f}" '
        f'width="{af_w:.3f}" height="3" fill="{variant.ink}"/>\n'
    )
    # LABS (matched-width)
    labs_paths, _ = text_as_paths(probe_sub, "LABS", labs_x, labs_baseline_y,
                                  sub_font_size, variant.ink,
                                  letter_spacing_svg=labs_spacing)
    body += labs_paths
    body += svg_footer()
    return body


def compose_mark_svg(variant, probe_disp, canvas=1024):
    """Just AF, centered with comfortable square padding."""
    af_font_size = 720
    af_w = text_width(probe_disp, "AF", af_font_size)
    cap_h_svg = probe_disp.cap_height * af_font_size / probe_disp.upm
    af_x = (canvas - af_w) / 2.0
    af_baseline_y = (canvas + cap_h_svg) / 2.0

    body = svg_header(canvas, canvas, variant.paper)
    af_paths, _ = text_as_paths(probe_disp, "AF", af_x, af_baseline_y,
                                af_font_size, variant.ink)
    body += af_paths
    body += svg_footer()
    return body


def compose_wordmark_svg(variant, probe_disp, probe_sub, width=1600, height=400):
    """Inline wordmark — AF · LABS on a single horizontal line."""
    af_font_size = 220
    labs_font_size = 200
    sep_font_size = 220

    af_w = text_width(probe_disp, "AF", af_font_size)
    labs_w = text_width(probe_disp, "LABS", labs_font_size)
    sep_w = text_width(probe_disp, "·", sep_font_size)
    gap = 32.0
    total_w = af_w + gap + sep_w + gap + labs_w
    cap_h_svg = probe_disp.cap_height * af_font_size / probe_disp.upm

    x = (width - total_w) / 2.0
    baseline_y = (height + cap_h_svg) / 2.0

    body = svg_header(width, height, variant.paper)
    p, _ = text_as_paths(probe_disp, "AF", x, baseline_y,
                         af_font_size, variant.ink)
    body += p
    x_sep = x + af_w + gap
    p, _ = text_as_paths(probe_disp, "·", x_sep, baseline_y,
                         sep_font_size, variant.ink)
    body += p
    x_labs = x_sep + sep_w + gap
    # Slightly drop LABS so its visual centre aligns with AF's
    labs_cap_h_svg = probe_disp.cap_height * labs_font_size / probe_disp.upm
    labs_baseline_y = (height + labs_cap_h_svg) / 2.0
    p, _ = text_as_paths(probe_disp, "LABS", x_labs, labs_baseline_y,
                         labs_font_size, variant.ink)
    body += p
    body += svg_footer()
    return body


def compose_social_svg(variant, probe_disp, probe_sub, width=1280, height=640):
    """Social-preview composition.

    Layout:
        Top-left:   "alexfordlabs.com" small mono mark
        Top-right:  "v3.0.0 · 2026" version stamp
        Centre:     AF / LABS stack lockup
        Bottom:     short tagline
    """
    body = svg_header(width, height, variant.paper)

    # ── Top-left: domain mark ──
    domain = "alexfordlabs.com"
    dom_font_size = 28
    dom_baseline = 60
    p, _ = text_as_paths(probe_sub, domain, 60, dom_baseline,
                         dom_font_size, variant.ink)
    body += p

    # ── Top-right: version ──
    version = "v3.0.0  ·  2026"
    ver_w = text_width(probe_sub, version, dom_font_size)
    p, _ = text_as_paths(probe_sub, version, width - 60 - ver_w, dom_baseline,
                         dom_font_size, variant.ink)
    body += p

    # ── Centre: AF / LABS lockup ──
    af_font_size = 260
    sub_font_size = 60
    af_w = text_width(probe_disp, "AF", af_font_size)
    af_x = (width - af_w) / 2.0
    cap_h_svg = probe_disp.cap_height * af_font_size / probe_disp.upm
    af_baseline_y = height * 0.50 + cap_h_svg / 2.0

    labs_spacing = find_letter_spacing_for_width(probe_sub, "LABS",
                                                 sub_font_size, af_w)
    labs_w = text_width(probe_sub, "LABS", sub_font_size, labs_spacing)
    labs_x = (width - labs_w) / 2.0
    rule_y = af_baseline_y + 26
    sub_cap_h_svg = probe_sub.cap_height * sub_font_size / probe_sub.upm
    labs_baseline_y = rule_y + 40 + sub_cap_h_svg

    p, _ = text_as_paths(probe_disp, "AF", af_x, af_baseline_y,
                         af_font_size, variant.ink)
    body += p
    body += (
        f'  <rect x="{af_x:.3f}" y="{rule_y:.3f}" '
        f'width="{af_w:.3f}" height="3" fill="{variant.ink}"/>\n'
    )
    p, _ = text_as_paths(probe_sub, "LABS", labs_x, labs_baseline_y,
                         sub_font_size, variant.ink,
                         letter_spacing_svg=labs_spacing)
    body += p

    # ── Bottom: tagline ──
    tagline = "STUDIO  ·  TOOLS  ·  RESEARCH"
    tag_font_size = 26
    tag_spacing = 4.0
    tag_w = text_width(probe_sub, tagline, tag_font_size, tag_spacing)
    tag_x = (width - tag_w) / 2.0
    tag_baseline = height - 60
    p, _ = text_as_paths(probe_sub, tagline, tag_x, tag_baseline,
                         tag_font_size, variant.ink,
                         letter_spacing_svg=tag_spacing)
    body += p

    body += svg_footer()
    return body


# ── Driver ─────────────────────────────────────────────────────────────────


def svg_to_png(svg_text, out_path, width=None, height=None):
    cairosvg.svg2png(
        bytestring=svg_text.encode("utf-8"),
        write_to=str(out_path),
        output_width=width,
        output_height=height,
    )


def emit_layout(name, compose_fn, sizes, variants, probe_disp, probe_sub,
                svg_kwargs=None, png_kwargs_fn=None):
    """Generic emitter: writes the SVG once + PNGs at each requested size.

    Args:
        name: folder name (e.g. 'lockup')
        compose_fn: function that returns the SVG string for a given variant
        sizes: list of (label, width, height) tuples for PNG outputs;
               if height is None, scale proportionally from width
        variants: list of Variant
        svg_kwargs: extra kwargs for compose_fn
        png_kwargs_fn: optional function (size_label) -> dict (rarely used)
    """
    out_dir = BRAND_DIR / name
    out_dir.mkdir(exist_ok=True)
    svg_kwargs = svg_kwargs or {}

    for variant in variants:
        svg = compose_fn(variant, probe_disp, probe_sub, **svg_kwargs)
        svg_path = out_dir / f"{variant.name}.svg"
        svg_path.write_text(svg, encoding="utf-8")

        for label, w, h in sizes:
            png_path = out_dir / f"{variant.name}-{label}.png"
            svg_to_png(svg, png_path, width=w, height=h)


def main():
    probe_disp = FontProbe(FONT_DISPLAY)
    probe_sub = FontProbe(FONT_SUB)

    # ── 1. Lockup (square, AF / LABS) ──
    emit_layout(
        "lockup",
        compose_lockup_svg,
        sizes=[
            ("256", 256, 256),
            ("512", 512, 512),
            ("1024", 1024, 1024),
            ("2048", 2048, 2048),
        ],
        variants=VARIANTS,
        probe_disp=probe_disp,
        probe_sub=probe_sub,
        svg_kwargs={"canvas": 1024},
    )

    # ── 2. Mark (square, just AF) — for favicons, avatars, app icons ──
    emit_layout(
        "mark",
        lambda variant, pd, ps, **kw: compose_mark_svg(variant, pd, **kw),
        sizes=[
            ("16", 16, 16),
            ("32", 32, 32),
            ("48", 48, 48),
            ("64", 64, 64),
            ("128", 128, 128),
            ("180", 180, 180),   # Apple touch icon
            ("192", 192, 192),   # Android / PWA
            ("256", 256, 256),
            ("460", 460, 460),   # GitHub avatar
            ("512", 512, 512),
            ("1024", 1024, 1024),
        ],
        variants=VARIANTS,
        probe_disp=probe_disp,
        probe_sub=probe_sub,
        svg_kwargs={"canvas": 1024},
    )

    # ── 3. Wordmark (horizontal, AF · LABS inline) ──
    emit_layout(
        "wordmark",
        compose_wordmark_svg,
        sizes=[
            ("400", 400, 100),
            ("800", 800, 200),
            ("1600", 1600, 400),
            ("3200", 3200, 800),
        ],
        variants=VARIANTS,
        probe_disp=probe_disp,
        probe_sub=probe_sub,
        svg_kwargs={"width": 1600, "height": 400},
    )

    # ── 4. Social preview (1280×640, full composition) ──
    emit_layout(
        "social",
        compose_social_svg,
        sizes=[("1280x640", 1280, 640)],
        variants=VARIANTS,
        probe_disp=probe_disp,
        probe_sub=probe_sub,
        svg_kwargs={"width": 1280, "height": 640},
    )

    # Count outputs
    counts = {
        "lockup": len(list((BRAND_DIR / "lockup").glob("*"))),
        "mark": len(list((BRAND_DIR / "mark").glob("*"))),
        "wordmark": len(list((BRAND_DIR / "wordmark").glob("*"))),
        "social": len(list((BRAND_DIR / "social").glob("*"))),
    }
    for k, v in counts.items():
        print(f"  {k:10s}  {v} files")
    print(f"Total: {sum(counts.values())} brand-asset files in {BRAND_DIR}")


if __name__ == "__main__":
    main()
