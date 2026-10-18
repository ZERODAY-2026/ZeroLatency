# Redline Design Tokens: The Ink Room & Paper Room

Extracted directly from `ui design idea/` reference implementations (`the_ink_room/DESIGN.md`, HTML/Tailwind configs, and reference screens).

---

## 1. Color Palette

### Ink Room (Dark Theme — Default)
| Token Name | Hex Code | Semantic Role |
|---|---|---|
| `--bg-app` | `#0D0C0A` | Canvas background (warm charcoal/black) |
| `--bg-rail` | `#12110E` | Persistent left navigation rail |
| `--bg-surface` | `#181612` | Surface cards, containers, panels |
| `--bg-raised` | `#211E19` | Raised cards, inputs, hover states, popovers |
| `--bg-inset` | `#0A0908` | Inset blocks, quote background, terminal/mono boxes |
| `--line` | `#2C2923` | Hairline dividers, card borders |
| `--line-strong` | `#433E34` | Input outlines, active dividers |
| `--paper-primary` | `#F3EDE0` | Primary headings, prominent body text |
| `--paper-secondary` | `#CFC7B6` | Standard body copy, secondary metadata |
| `--paper-muted` | `#968D7B` | Captions, timestamps, disabled/muted labels |
| `--marker` | `#F7D748` | Brand accent, primary CTAs, highlighter yellow, active indicators |
| `--marker-dark` | `#1A1608` | Ink text rendered on top of `--marker` surfaces |
| `--found` | `#7CC4FF` | Verbatim quote verified in document |
| `--found-bg` | `rgba(124, 196, 255, 0.12)` | Background tint for verified badges |
| `--found-border` | `rgba(124, 196, 255, 0.35)` | Border tint for verified badges |
| `--ember` | `#FF9566` | Unverified quotes, sparse text warnings, low confidence |
| `--ember-bg` | `rgba(255, 149, 102, 0.12)` | Background tint for unverified/warning items |
| `--ember-border` | `rgba(255, 149, 102, 0.35)` | Border tint for unverified/warning items |
| `--review` | `#C3A6FF` | Needs professional review flag |
| `--review-bg` | `rgba(195, 166, 255, 0.12)` | Background tint for review badge |
| `--review-border` | `rgba(195, 166, 255, 0.35)` | Border tint for review badge |
| `--jurisdiction` | `#A9B7C2` | Depends on local law |
| `--jurisdiction-bg` | `rgba(169, 183, 194, 0.12)` | Background tint for jurisdiction badge |
| `--local-teal` | `#4FE3C8` | Local model ready, offline air-gap status (system only) |
| `--local-teal-bg` | `rgba(79, 227, 200, 0.10)` | System local status capsule background |
| `--local-teal-border`| `rgba(79, 227, 200, 0.30)` | System local status capsule border |
| `--error-red` | `#FF7A8A` | Runtime errors, network blocked alert |
| `--error-red-bg` | `rgba(255, 122, 138, 0.10)`| Error card background |
| `--error-red-border`| `rgba(255, 122, 138, 0.35)`| Error card border |

### Paper Room (Light Theme)
| Token Name | Hex Code | Semantic Role |
|---|---|---|
| `--bg-app` | `#F5EFE3` | Warm parchment canvas background |
| `--bg-rail` | `#EDE5D4` | Light navigation rail |
| `--bg-surface` | `#FFFBF2` | Crisp off-white card surface |
| `--bg-raised` | `#FFFFFF` | Inputs, raised cards, dropdown popovers |
| `--bg-inset` | `#F0E8D8` | Inset quote containers, code snippets |
| `--line` | `#E2D8C3` | Light hairline dividers and borders |
| `--line-strong` | `#C9BDA3` | Stronger borders, active inputs |
| `--paper-primary` | `#1C1A16` | Ink black primary text |
| `--paper-secondary` | `#403B31` | Deep warm grey secondary text |
| `--paper-muted` | `#6B6354` | Muted annotations and captions |
| `--marker` | `#F2C500` | Deep golden highlighter accent |
| `--marker-dark` | `#1C1A16` | Text on golden highlighter |
| `--found` | `#0F5FA8` | Verified quote blue (high contrast) |
| `--found-bg` | `rgba(15, 95, 168, 0.10)` | Background tint for verified badge |
| `--found-border` | `rgba(15, 95, 168, 0.30)` | Border tint for verified badge |
| `--ember` | `#B8431A` | Unverified/warning terracotta |
| `--ember-bg` | `rgba(184, 67, 26, 0.10)` | Background tint for warning badge |
| `--ember-border` | `rgba(184, 67, 26, 0.30)` | Border tint for warning badge |
| `--review` | `#6B3FC9` | Review with professional violet |
| `--review-bg` | `rgba(107, 63, 201, 0.10)` | Background tint for review badge |
| `--review-border` | `rgba(107, 63, 201, 0.30)` | Border tint for review badge |
| `--jurisdiction` | `#4B5B68` | Jurisdiction slate grey |
| `--local-teal` | `#0B7A6B` | Deep local-only teal |
| `--local-teal-bg` | `rgba(11, 122, 107, 0.10)` | Local status capsule background |
| `--local-teal-border`| `rgba(11, 122, 107, 0.30)` | Local status capsule border |
| `--error-red` | `#B3203A` | Error crimson red |
| `--error-red-bg` | `rgba(179, 32, 58, 0.08)` | Error card background |
| `--error-red-border`| `rgba(179, 32, 58, 0.30)` | Error card border |

---

## 2. Typography

| Role | Family | Fallbacks | Size | Line Height | Weight | Letter Spacing |
|---|---|---|---|---|---|---|
| `display-hero` | `Fraunces` | Georgia, serif | 56px | 60px | 600 | -0.02em |
| `display-hero-mobile` | `Fraunces` | Georgia, serif | 32px | 38px | 600 | -0.01em |
| `headline-h1` | `Fraunces` | Georgia, serif | 36px | 42px | 600 | -0.02em |
| `headline-h1-mobile`| `Fraunces` | Georgia, serif | 26px | 32px | 600 | -0.01em |
| `headline-h2` | `Fraunces` | Georgia, serif | 24px | 32px | 600 | -0.01em |
| `headline-h3` | `Inter Tight` | Inter, sans-serif | 17px | 24px | 600 | -0.01em |
| `stat-numeral` | `Fraunces` | Georgia, serif | 40px | 44px | 600 | tabular-nums |
| `body-default` | `Inter` | system-ui, sans-serif | 15px | 25px | 400 | normal |
| `caption-default` | `Inter` | system-ui, sans-serif | 13px | 20px | 400 | normal |
| `badge-label` | `Inter` | system-ui, sans-serif | 12px | 16px | 550 | 0.01em |
| `code-quote` | `JetBrains Mono` | monospace | 13px | 22px | 400 | normal |

---

## 3. Spacing & Dimensions

- **Base scale**: `4px`, `8px`, `12px`, `16px`, `20px`, `24px`, `32px`, `48px`, `64px`, `72px`
- **Rail Width**: Collapsed `72px`, Expanded `264px`
- **Top Bar Height**: `56px`
- **Stat Tile Height**: `110px` – `120px`
- **Vault Card Max Width**: `440px`

---

## 4. Border Radii

- **Cards & Containers**: `14px` (`border-radius: 14px`)
- **Buttons & Inputs**: `10px` (`border-radius: 10px`)
- **Quote Blocks**: `6px` (`border-radius: 6px` with square left edge)
- **Badges & Pills**: `9999px` (`border-radius: 9999px`)
- **Tags & Small Chips**: `4px` (`border-radius: 4px`)

---

## 5. Shadows & Depth

- **Card Elevation**:
  - Ink Room: `0 2px 8px rgba(0, 0, 0, 0.25)`
  - Paper Room: `0 2px 8px rgba(28, 26, 22, 0.04)`
- **Physical Sheet on Desk**:
  - Ink Room: `0 12px 32px rgba(0, 0, 0, 0.55)`
  - Paper Room: `0 12px 32px rgba(28, 26, 22, 0.12)`
- **Rail Flyout Shadow**:
  - Ink Room: `4px 0 24px rgba(0, 0, 0, 0.50)`
  - Paper Room: `4px 0 20px rgba(30, 24, 12, 0.08)`
- **Tactile Paper Grain Texture**:
  - `radial-gradient(rgba(243, 237, 224, 0.03) 1px, transparent 0)` at `24px 24px` grid

---

## 6. Iconography

- **Style**: Inline SVG (Lucide/Material Symbols Outlined geometric stroke)
- **Stroke Width**: `1.75px` to `2px`
- **Default Sizes**:
  - Small / Badge: `14px` - `16px`
  - Standard / Nav: `18px` - `20px`
  - Large / Feature: `24px` - `32px`

---

## 7. Motion & Animations (A1 to A15)

- **Timing functions**:
  - `ease-out`: `cubic-bezier(0.16, 1, 0.3, 1)`
  - `ease-in-out`: `cubic-bezier(0.65, 0, 0.35, 1)`
- **Durations**:
  - `fast`: `120ms`
  - `base`: `220ms`
  - `slow`: `420ms`
  - `scene`: `700ms`
- **Signature Animations**:
  - **A1 Page Turn**: Fade + 8px slide left out (120ms); 12px rise + fade in (220ms)
  - **A2 Highlighter Sweep**: Marker yellow bar wipes left-to-right (420ms); viewer clip-path wipe
  - **A3 Stamp**: Scale 1.35 -> 1.0, rotate -4deg -> 0deg, opacity 0 -> 1 (220ms overshoot)
  - **A4 Redaction Reveal**: Scan line top-to-bottom; black bars retract horizontally (320ms)
  - **A5 Vault Unlock**: Ring segment latching (3x120ms) + iris opening (420ms)
  - **A6 Orbit of Trust**: 12s ambient rotating orbit loop with laptop glyph and cut external line
  - **A7 Staggered Rise**: 16px slide up + fade in, 40ms stagger between elements
  - **A8 Count-up**: Numerals ease from 0 to target (600ms)
  - **A9 Rail Expand**: 72px to 264px width transition (220ms ease-out)
  - **A10 Underline Draw**: Left-to-right border draw (200ms)
  - **A11 Page Fan**: Parallaxing fanned paper sheets
  - **A12 Segment Ticks**: Section progress tick bumps (120ms)
  - **A13 Shred**: Vertical shred strips drop and fade (500ms)
  - **A14 Breathing Dot**: 4s opacity pulse (0.6 -> 1.0) on local privacy badge
  - **A15 Typewriter Answer**: Line-by-line reveal (60ms/line)
