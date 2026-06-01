<!--
Author: Alexander Ford <alex@alexfordlabs.com>
Repository: https://github.com/alexfordlabs/project-architect
License: MIT
-->

# Alex Ford Labs — Brand Assets

Canonical visual identity for **Alex Ford Labs** — the umbrella entity for
`alexfordlabs.com`, `github.com/alexfordlabs`, and downstream projects
(including `alexfordlabs/project-architect`).

## Identity at a glance

| Aspect | Value |
|---|---|
| **Wordmark** | `AF` over `LABS` (matched-width stack) |
| **Display font** | Geist Mono ExtraBold (SIL OFL) |
| **Subtext font** | Geist Mono Medium |
| **Palette** | V5 — pure black + pure white. **No colour at the umbrella level.** Per-project sub-brands may introduce an accent colour. |
| **Ink (light variant)** | `#0A0A0A` (near-black) |
| **Paper (light variant)** | `#FFFFFF` |
| **Ink (dark variant)** | `#FFFFFF` |
| **Paper (dark variant)** | `#0A0A0A` |

## Asset directory

```
.github/assets/brand/
├── README.md                 ← this file
├── source/
│   └── build_brand.py        ← rerun to regenerate every asset
├── lockup/                   ← AF / LABS stack — primary lockup
│   ├── light.svg
│   ├── dark.svg
│   ├── light-256.png
│   ├── light-512.png
│   ├── light-1024.png
│   ├── light-2048.png
│   ├── dark-256.png
│   ├── dark-512.png
│   ├── dark-1024.png
│   └── dark-2048.png
├── mark/                     ← Just AF — favicon / avatar / app-icon
│   ├── light.svg
│   ├── dark.svg
│   ├── light-{16,32,48,64,128,180,192,256,460,512,1024}.png
│   └── dark-{16,32,48,64,128,180,192,256,460,512,1024}.png
├── wordmark/                 ← AF · LABS inline — horizontal banner
│   ├── light.svg
│   ├── dark.svg
│   ├── light-{400,800,1600,3200}.png
│   └── dark-{400,800,1600,3200}.png
└── social/                   ← Pre-composed 1280×640 social preview
    ├── light.svg
    ├── dark.svg
    ├── light-1280x640.png
    └── dark-1280x640.png
```

Every SVG is **outline-converted** via `fontTools` — no font file is required
at render time. Open the SVG in any browser, Figma, Illustrator, or PDF
renderer and the glyphs render identically without Geist Mono installed.

## Which asset goes where

| Use case | Asset | Recommended size |
|---|---|---|
| **GitHub avatar** (`@alexfordlabs`) | `mark/light-460.png` (or `dark-460.png` if your profile theme is dark) | 460×460 |
| **GitHub social-preview** (per-repo, including `alexfordlabs/project-architect`) | `social/light-1280x640.png` | 1280×640 (GitHub's required size) |
| **Open Graph / Twitter Card** (`alexfordlabs.com`) | `social/light-1280x640.png` | 1200×630 acceptable — GitHub's 1280×640 reuses without complaint |
| **Browser favicon** | `mark/light-32.png`, plus 16×16, 48×48 | Multi-size .ico equivalent |
| **Apple touch icon** | `mark/light-180.png` | 180×180 |
| **Android home-screen icon / PWA** | `mark/light-192.png`, `mark/dark-512.png` | 192 + 512 maskable |
| **iOS app icon** | `mark/light-1024.png` (master — system derives smaller sizes) | 1024×1024 |
| **README hero image** | `social/light-1280x640.png` or `wordmark/light-1600.png` | 1280×640 or 1600×400 |
| **Inline header / nav bar** | `wordmark/light.svg` | SVG — scales to any width |
| **Letterhead / business card** | `lockup/light.svg` | SVG — scales without quality loss |
| **Presentation title slide** | `social/light-1280x640.png` | 1280×640 |
| **Sticker / merchandise** | `lockup/light.svg` (sheet print at any size) | SVG |
| **Slack / Discord workspace icon** | `mark/light-512.png` | 512×512 |

Rule of thumb: **SVG first, PNG when a binary is required**.

## Light vs dark variant

Pick by surface theme, not by user-OS theme:

- **Use `light` variant** when the surface (page, slide, card) is paper-white
  or any light tone. The mark renders in near-black ink.
- **Use `dark` variant** when the surface is solid black or near-black. The
  mark renders in white ink on the dark paper.

For surfaces that themselves switch theme (e.g., a website respecting
`prefers-color-scheme`), embed both variants and toggle via `media` attribute:

```html
<picture>
  <source srcset="brand/mark/dark.svg"
          media="(prefers-color-scheme: dark)">
  <img src="brand/mark/light.svg" alt="Alex Ford Labs" width="64" height="64">
</picture>
```

## Future colour variants

The umbrella `alexfordlabs` brand is **locked to V5** — black, white, no colour.
This is deliberate. The restraint signals "we are the parent entity" and lets
each downstream project (e.g. `alexfordlabs/pseudo`, `alexfordlabs/project-architect`)
add **one** accent colour that becomes the project's identity.

When that time comes, the script will grow per-project variants:

```
brand/
├── ...                       (B&W umbrella, current)
├── _project-pseudo/          (violet accent — `#7C3AED`)
└── _project-architect/       (accent TBD)
```

Each project variant inherits the AF/LABS geometry and adds the colour. The
umbrella stays untouched.

## Regenerate

```bash
/tmp/pdfbuild-venv/bin/python .github/assets/brand/source/build_brand.py
```

Dependencies: `fontTools`, `cairosvg`. Already in the local venv from the
earlier explainer PDF + logo-concepts builds.

## Attribution

When Alex Ford Labs is mentioned in documentation, prefer:

> `Alex Ford Labs` (with the wordmark or lockup adjacent).

Never:
- ❌ `Alex Ford Labs LLC` (no legal form on the brand)
- ❌ `Alexander Ford Labs` (the founder is Alexander, the brand is Alex)
- ❌ `AlexFordLabs` (one-word concatenation — used only in URLs/handles)

---

*★ Skillfully made with [project-architect](https://github.com/alexfordlabs/project-architect).*
