---
name: The Ink Room
colors:
  surface: '#15130f'
  surface-dim: '#15130f'
  surface-bright: '#3c3934'
  surface-container-lowest: '#100e0a'
  surface-container-low: '#1d1b17'
  surface-container: '#221f1b'
  surface-container-high: '#2c2a25'
  surface-container-highest: '#373430'
  on-surface: '#e8e1da'
  on-surface-variant: '#cfc6ae'
  inverse-surface: '#e8e1da'
  inverse-on-surface: '#33302b'
  outline: '#98907a'
  outline-variant: '#4c4734'
  surface-tint: '#e4c537'
  primary: '#fff4d6'
  on-primary: '#3a3000'
  primary-container: '#f7d748'
  on-primary-container: '#6e5d00'
  inverse-primary: '#6f5d00'
  secondary: '#92ccff'
  on-secondary: '#003351'
  secondary-container: '#00699e'
  on-secondary-container: '#c8e3ff'
  tertiary: '#faf2ff'
  on-tertiary: '#3a1e6f'
  tertiary-container: '#e2d1ff'
  on-tertiary-container: '#6a4fa1'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffe165'
  primary-fixed-dim: '#e4c537'
  on-primary-fixed: '#221b00'
  on-primary-fixed-variant: '#544600'
  secondary-fixed: '#cce5ff'
  secondary-fixed-dim: '#92ccff'
  on-secondary-fixed: '#001d31'
  on-secondary-fixed-variant: '#004b73'
  tertiary-fixed: '#eaddff'
  tertiary-fixed-dim: '#d2bbff'
  on-tertiary-fixed: '#25005a'
  on-tertiary-fixed-variant: '#513787'
  background: '#15130f'
  on-background: '#e8e1da'
  surface-variant: '#373430'
  bg-app: '#0D0C0A'
  bg-rail: '#12110E'
  bg-surface: '#181612'
  bg-raised: '#211E19'
  bg-inset: '#0A0908'
  line: '#2C2923'
  line-strong: '#433E34'
  paper-primary: '#F3EDE0'
  paper-secondary: '#CFC7B6'
  paper-muted: '#968D7B'
  marker-dark: '#1A1608'
  ember: '#FF9566'
  jurisdiction: '#A9B7C2'
  local-teal: '#4FE3C8'
  error-red: '#FF7A8A'
typography:
  display-hero:
    fontFamily: Fraunces
    fontSize: 56px
    fontWeight: '600'
    lineHeight: 60px
  display-hero-mobile:
    fontFamily: Fraunces
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 38px
  headline-h1:
    fontFamily: Fraunces
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 42px
  headline-h1-mobile:
    fontFamily: Fraunces
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 32px
  headline-h2:
    fontFamily: Fraunces
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-h3:
    fontFamily: Inter Tight
    fontSize: 17px
    fontWeight: '600'
    lineHeight: 24px
  stat-numeral:
    fontFamily: Fraunces
    fontSize: 40px
    fontWeight: '600'
    lineHeight: 44px
  body-default:
    fontFamily: Inter
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 25px
  caption-default:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
  badge-label:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '550'
    lineHeight: 16px
  code-quote:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 22px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

This design system embodies the mood of an editor's desk, an archival study, and a litigator's private library under lamplight. Crafted for private legal document triage, the aesthetic translates tactile editorial workflows into digital precision: warm paper stocks, deep carbon inks, wax pencil margin notes, chisel-tip highlighter strokes, physical redaction bars, and brass lock mechanisms.

The style represents **Tactile Flat Realism**: physical editorial metaphors translated through disciplined, clean surfaces. It completely avoids the ethereal neon purples, glowing cyan grids, and translucent frosted glass typical of conventional tech and AI platforms. Instead, it relies on strict 1px hairline rules, tactile warmth, local typography, and paper-like substance.

The interface must evoke:
- **Discretion & Privacy**: Absolute operational confidentiality conveyed through air-gapped styling, monospaced verification telemetry, and quiet surfaces.
- **Skeptical Rigor**: No green "safe" confirmations anywhere in the system. The platform never gives false legal certainty; it guides, highlights, and alerts.
- **Warm Editorial Substance**: Tactile, readable, unhurried, grounded in historical legal print traditions yet razor-sharp in utility.

## Colors

The color palette centers on **Ink Room** (dark mode as primary operational default) with support for **Paper Room** (light mode). All base tones derive from warm carbon black and aged manuscript paper rather than synthetic slate or cold blue-grays.

### Core Signals & Accents
- **Marker Yellow (`#F7D748`)**: Primary action driver, focal point highlighter, active state indicator pip, and document highlight marker. Text placed on marker fills must always use `#1A1608`.
- **Found Quote Blue (`#7CC4FF`)**: Semantic indicator for verified textual citations grounded directly in the document.
- **Ember Warning (`#FF9566`)**: High-priority alert for unverified quotations, hallucinations, or low-confidence extractions.
- **Review Violet (`#C3A6FF`)**: Contextual alert signifying terms, ambiguities, or clauses requiring licensed human counsel.
- **Jurisdiction Gray (`#A9B7C2`)**: Contextual indicator for clauses dictated by governing local law.
- **Local Teal (`#4FE3C8`)**: Strict system-only status (local execution, model readiness, air-gap integrity). **Strict rule:** Never apply teal to document claims, legal findings, or quote veracity.
- **Error Red (`#FF7A8A`)**: Critical failure alerts, destructive actions, and connection block events.

### The No-Green Mandate
Green is strictly prohibited across the entire design system. Software must never convey that a contract or legal document is "safe" or "approved." Legal findings communicate degrees of textual verification, never legal absolution.

### Semantic Alpha Rules
- **Badge & Chip Fills**: 12% opacity of the respective signal color over `bg-surface`.
- **Signal Hairline Outlines**: 35% opacity of the respective signal color.
- **Active Document Highlight Fills**: Marker yellow at 35% opacity.
- **Hero Spotlight Glow**: Radial gradient of `#F7D748` at 6% opacity (600px spread).
- **Disabled State**: Applied uniformly across elements at `opacity: 0.45`.

## Typography

Typography establishes an editorial atmosphere balanced with forensic legibility. All fonts must be served locally to maintain complete offline privacy.

### Hierarchy & Family Roles
- **Fraunces**: Optical-size variable serif with warm, human curves. Used for high-level display text, page titles (`headline-h1`, `headline-h2`), and quantitative counter figures (`stat-numeral`). It communicates tradition, institutional authority, and editorial deliberation.
- **Inter Tight**: High-density geometric sans-serif assigned exclusively to card headlines and inquiry headings (`headline-h3`). Offers clean visual grouping in constrained containers.
- **Inter**: Functional, unembellished grotesque for standard interface copy (`body-default`), metadata tooltips, legal disclaimers (`caption-default`), and status chips (`badge-label`).
- **JetBrains Mono**: Clean, tabular monospace assigned to direct quoted excerpts, extracted clauses, file nomenclature, hash values, and system terminal feeds (`code-quote`).

Stat numerals and tabular figures must always render with font-variant-numeric: `tabular-nums` to prevent horizontal jitter during automated analysis and count-up sequences.

## Layout & Spacing

The layout operates on a strict **8-point base grid** with a 4px sub-grid step. The layout philosophy relies on an asymmetric split workspace simulating a physical desk: a primary triage list paired with a persistent, sticky document review pane.

### Layout Rhythm
- **Top Shell Bar**: Fixed 56px height across all desktop views.
- **Navigation Rail**: Dual-state architectural sidebar. 72px width when collapsed (icon-only); smooth expand to 264px on hover or pin.
- **Findings Triage Screen**: Asymmetric split on desktop (55% triage and answer stream, 45% sticky document viewport offset by 72px from top).
- **Vault Dialog**: Fixed 440px centered card modal.
- **Component Heights**: Buttons at 44px; stat tiles at 120px; table rows at 40px; status chips at 26px.

### Responsive Breakpoints
- **Desktop (>= 1200px)**: Default 12-column layout. Split view visible simultaneously. Rail dynamic (72px -> 264px). Outer margin at 32px (`space-xl`), gutters at 24px (`space-lg`).
- **Tablet / Compact Desktop (900px – 1199px)**: Rail locked strictly to 72px collapsed mode. Document pane reduces to 40% width. Filters collapse into popovers.
- **Mobile (< 900px)**: Navigation transforms to a docked bottom icon bar. Layout collapses to a single 100% column. The document viewer moves to an on-demand bottom sheet drawer. Tables reformat into stacked cards.

## Elevation & Depth

This design system avoids blurry floating shadows and artificial ambient lighting. Depth is tactile, structural, and planar, mirroring stacked paper, desk surfaces, and physical folios.

### Depth Grammar
- **Base Desk Surface (`bg-app`, `#0D0C0A`)**: Ground canvas finished with an ambient 3% tactile paper noise texture overlay to break synthetic digital smoothness.
- **Workstations & Shell (`bg-rail`, `#12110E`)**: Receded structural navigation zones.
- **Surface Tier (`bg-surface`, `#181612`)**: Standard cards, triage containers, and utility boxes.
- **Raised Tier (`bg-raised`, `#211E19`)**: Input fields, active popovers, stat tiles, selected cards, and hover elevation states.
- **Inset Tier (`bg-inset`, `#0A0908`)**: Recessed areas simulating cut paper grooves, used for monospaced quote boxes, extracted text, and redaction wells.

### Border Hairlines & Tactile Shadows
- **Standard Outlines**: 1px solid hairline `line` (`#2C2923`). Shadows are withheld from normal cards.
- **Physical Sheet Shadow**: The document preview simulates a physical sheet resting on dark wood using: `box-shadow: 0 12px 32px rgba(0, 0, 0, 0.45)`.
- **Physical Sheet Rotation**: Unprocessed source documents and exported markdown sheets apply a deliberate physical tilt of `transform: rotate(0.4deg)` to evoke physical stationery on a desk.

## Shapes

The shape system balances modern structural utility with soft editorial tangibility. Elements do not share uniform rounding; radii vary according to the physical metaphor of the container.

### Radius Assignments
- **Cards, Panels & Containers**: `14px` border radius (`rounded-lg`), softening rectangular boundaries into handled paper folders.
- **Interactive Controls (Buttons, Text Inputs, Dropzones)**: `10px` border radius (`rounded`), providing crisp fingertip affordances.
- **Extracted Quotes & Inset Wells**: `6px` radius on top-right and bottom-right edges (`0 6px 6px 0`), keeping the left bound flush against the vertical provenance indicator bar.
- **Status Pills & Chips**: Fully circular pill shape (`rounded-full`, 9999px).
- **Redaction Bars**: 2px micro-rounded edges, simulating physical marker blackout tapes.

## Components

### Buttons
- **Primary Marker Action**: Height 44px, border-radius 10px, background `#F7D748`, text `#1A1608` (Inter, weight 600). Hover triggers a subtle brightness lift without drop shadows. On focus: 2px solid `#F7D748` outline with 2px offset.
- **Secondary Document Action**: Height 44px, border-radius 10px, background transparent, border 1px solid `#433E34`, text `#F3EDE0`. On hover: background `#211E19`.
- **Destructive Action**: Height 44px, border-radius 10px, background 8% tint of `#FF7A8A`, border 1px solid `#FF7A8A`, text `#FF7A8A`.

### Status Badges & Chips
- **Geometry**: Height 26px, pill-shaped (`9999px`), padding `0 10px`, typography 12px / 16px weight 550.
- **Composition**: All badges pair an SVG icon with sentence-case text. Badges are never icon-only.
- **Variant Tints**:
  - *Verified Quote*: `#7CC4FF` foreground, 12% `#7CC4FF` background, 1px solid 35% `#7CC4FF` border.
  - *Unverified Warning*: `#FF9566` foreground, 12% `#FF9566` background, 1px dashed 35% `#FF9566` border.
  - *Requires Review*: `#C3A6FF` foreground, 12% `#C3A6FF` background, 1px solid 35% `#C3A6FF` border.
  - *Air-Gap / Local Only*: `#4FE3C8` foreground, 12% `#4FE3C8` background, 1px solid 35% `#4FE3C8` border.
  - *Jurisdiction Note*: `#A9B7C2` foreground, 12% `#A9B7C2` background, 1px solid 35% `#A9B7C2` border.

### Finding & Triage Cards
- **Container**: Background `#181612`, border 1px solid `#2C2923`, border-radius 14px, padding 20px.
- **Selected State**: Background shifts to `#211E19`, and the left border gains an immediate 2px solid `#F7D748` marker accent.
- **Unverified State**: Card border converts to 1px solid `#FF9566`.
- **Title**: Inter Tight 17px/24px weight 600 in `#F3EDE0`.

### Document Quotes & Extracted Text
- **Container**: Background `#0A0908` (`bg-inset`), padding 12px 16px, border-radius `0 6px 6px 0`.
- **Verified Accent**: 3px solid `#7CC4FF` left border.
- **Unverified Accent**: 3px dashed `#FF9566` left border.
- **Typography**: JetBrains Mono 13px/22px in `#CFC7B6`.
- **Highlighter Sweep**: Text highlights render in `#F7D748` at 35% opacity with a clip-path left-to-right fill animation.

### Text Inputs & Form Fields
- **Container**: Height 44px, background `#211E19`, border 1px solid `#433E34`, border-radius 10px, padding `0 14px`.
- **Text Style**: Inter 15px `#F3EDE0`, placeholder text in `#968D7B`.
- **Focus State**: Border color `#F7D748`, outline 2px solid `#F7D748` with a 2px offset. Caret color is set to `#F7D748`.

### Checkboxes & Radios
- **Checkbox**: 18px × 18px, border-radius 4px, border 1px solid `#433E34`, background `#0A0908`. Selected state fills with `#F7D748` and displays an `#1A1608` check mark.
- **Radio**: 18px × 18px, circular, border 1px solid `#433E34`, background `#0A0908`. Selected state displays an inner 8px circle of `#F7D748`.

### Dropzone Target
- **Container**: Min-height 200px, border-radius 14px, background `#12110E`, border 2px dashed `#433E34`.
- **Drag-Over State**: Border turns 2px solid `#F7D748`, background shifts to `#181612`.