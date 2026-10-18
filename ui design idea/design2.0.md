# DESIGN.md: Private Legal Triage ("Redline")

Creative direction, design system, motion language and full screen specification for the Private Legal Document Triage Agent (PS2). Behaviour and data come from `frontend.md`. This file defines how every page looks, moves and feels.

---

## 0. Creative direction

### The concept: "The Ink Room"
Most legal-AI and dashboard UIs look the same: navy background, purple-blue gradient, glass cards, a robot icon. We are deliberately not doing that.

Redline is a **private reading room**. Warm paper and ink instead of cold blue glass. The document is the hero. The interface behaves like an editor's desk: highlighter pens, margin notes, redaction bars, rubber stamps and a locked cabinet. Every one of those objects maps to a real function of the product:

| Object | Product meaning |
|---|---|
| Highlighter marker | The cited passage in the source page. Also our primary action colour. |
| Redaction bar | The loading state. Black bars retract to reveal content as analysis progresses. |
| Rubber stamp | "Quote found in document". Stamps down once, then rests. |
| Margin note | Findings sit beside the page like annotations in a margin. |
| Locked cabinet / vault ring | The local app lock and the "nothing leaves this computer" story. |
| Shredder | "Clear and start over". The document is visibly destroyed. |

### Personality
Calm, exacting, quietly confident, a little theatrical in the moments that matter (unlock, analyse, stamp, shred) and completely still the rest of the time. Never alarmist, never "AI magic", never celebratory about legal content.

### Design pillars
1. **Evidence beside every claim.** Finding left, highlighted source page right.
2. **Uncertainty is visible.** Words + icon + shape. Colour is never the only signal.
3. **No legal-certainty signals.** No green "safe / OK / valid" anywhere. "Quote found in document" means the quote exists in the text, nothing more.
4. **Privacy is visible and provable.** Local status is always on screen, with a page that shows how to verify it.
5. **Motion explains.** Each animation communicates a state change. If it does not explain something, it is not there.
6. **Plain language.** Non-lawyer reading level.
7. **Fail clearly.** Title, one sentence, next step, never document text.

### Platform
Desktop web, 1440x900 primary, responsive down to about 900px. Built in Streamlit with injected CSS. Everything here must be buildable from: native widgets, `st.container(border=True)`, `st.columns`, `st.tabs`/`st.navigation`, `st.fragment`, and CSS (keyframes, transitions, `clip-path`, `@property`, `view-timeline` where supported). No external network assets (see section 12).

---

## 1. Colour system

Two themes: **Ink Room** (dark, default) and **Paper Room** (light). Same semantics in both. No gradients on surfaces; depth comes from warm layering, a faint paper-grain texture (3% noise), and a soft warm spotlight behind hero areas.

### Ink Room (dark)
| Token | Hex | Use |
|---|---|---|
| `bg-app` | `#0D0C0A` | Page background (warm black, not blue-black) |
| `bg-rail` | `#12110E` | Navigation rail |
| `bg-surface` | `#181612` | Cards |
| `bg-raised` | `#211E19` | Hover, inputs, popovers |
| `bg-inset` | `#0A0908` | Quote blocks, extracted text |
| `line` | `#2C2923` | Hairline borders |
| `line-strong` | `#433E34` | Inputs, dividers that must be seen |
| `paper` (text-primary) | `#F3EDE0` | Headings, key text |
| `paper-2` (text-secondary) | `#CFC7B6` | Body |
| `paper-3` (text-muted) | `#968D7B` | Captions, helper text |

### Paper Room (light)
`bg-app #F5EFE3`, `bg-rail #EDE5D4`, `bg-surface #FFFBF2`, `bg-raised #FFFFFF`, `bg-inset #F0E8D8`, `line #E2D8C3`, `line-strong #C9BDA3`, `ink #1C1A16`, `ink-2 #403B31`, `ink-3 #6B6354`.

### Signal colours
Each has fg, a 12% tint for backgrounds and a 35% tint for borders. Always paired with an icon and a label.

| Role | Dark fg | Light fg | Meaning | Icon |
|---|---|---|---|---|
| `marker` (primary) | `#F7D748` (text on it `#1A1608`) | `#F2C500` (text `#1C1A16`) | Primary buttons, active nav, the highlight on source pages, focus ring | none |
| `found` | `#7CC4FF` | `#0F5FA8` | Quote found in document | quote-check |
| `ember` | `#FF9566` | `#B8431A` | Could not verify, sparse pages, low confidence | triangle-alert |
| `review` | `#C3A6FF` | `#6B3FC9` | Review with a professional | user-check |
| `jurisdiction` | `#A9B7C2` | `#4B5B68` | Depends on local law | globe |
| `local` | `#4FE3C8` | `#0B7A6B` | Local-only status, model ready (system status only) | shield-lock |
| `error` | `#FF7A8A` | `#B3203A` | Errors and blocked connections only | octagon-alert |
| `neutral` | `paper-3` | `ink-3` | Silent answers, empty states, notes | info |

### Rules
- **No green "safe" colour.** Teal appears only for system status (local, model ready), never for content about the document.
- **No red on findings.** Red is for errors only.
- Marker yellow is the single brand colour. It is used sparingly: one primary button per view, the highlight, the active nav pip, the focus ring.
- Contrast: body text 4.5:1 or better, large text and borders 3:1 or better, in both themes. Text on marker uses the dark ink colour.

---

## 2. Typography

All fonts are **bundled locally** and served from Streamlit static files. Never load Google Fonts (it would break the privacy claim).

| Role | Font | Size / line | Weight |
|---|---|---|---|
| Display (hero, page titles) | Fraunces (variable serif, soft optical size) | 56 / 60 hero, 36 / 42 page title | 600 |
| H2 | Fraunces | 24 / 32 | 600 |
| H3 (card titles) | Inter Tight | 17 / 24 | 600 |
| Body | Inter | 15 / 25 | 400 |
| Caption | Inter | 13 / 20 | 400 |
| Badge | Inter | 12 / 16, sentence case | 550 |
| Quote, extracted text, file names, hosts, commands | JetBrains Mono | 13 / 22 | 400 |
| Numerals in stat tiles | Fraunces, tabular figures | 40 / 44 | 600 |

The serif gives the product a printed-document feel and is the main reason it will not look like every other AI dashboard. Body and UI stay in a clean sans for legibility.

---

## 3. Shape, spacing, depth

- Spacing scale: 4 / 8 / 12 / 16 / 24 / 32 / 48 / 72.
- Radius: cards 14px, inputs and buttons 10px, badges pill, quote blocks 6px with a squared left edge.
- Borders over shadows. 1px `line` on cards. A card that is "selected" gets a 2px marker left edge.
- Paper-grain overlay at 3% opacity on `bg-app`. Page images in the viewer get a soft paper drop shadow (`0 12px 32px rgba(0,0,0,.45)`) so they look like sheets lying on the desk.
- Hero spotlight: one radial warm glow (`#F7D748` at 6% opacity, 600px) behind the hero headline. It is the only glow in the product.

---

## 4. Motion language

### Tokens
| Token | Value |
|---|---|
| `ease-out` | `cubic-bezier(.16, 1, .3, 1)` (all enters) |
| `ease-in-out` | `cubic-bezier(.65, 0, .35, 1)` (loops, wipes) |
| `fast` | 120ms (hover, press) |
| `base` | 220ms (tab change, expander) |
| `slow` | 420ms (highlighter wipe, card rise) |
| `scene` | 700ms (unlock, page transitions) |

### Signature animations
| ID | Name | Where | What happens |
|---|---|---|---|
| A1 | **Page turn** | Switching between destinations | Outgoing content fades and shifts 8px left (120ms); incoming content rises from 12px below with fade (220ms). A thin marker line sweeps across the top of the content area. |
| A2 | **Highlighter sweep** | Selecting "View in document" | The quote block gets a marker-yellow bar wiping left to right behind the text (420ms). In the source viewer the highlight rectangle draws in with `clip-path` from left to right. Final state: soft 35% marker fill plus a 2px outline (visible without colour). |
| A3 | **Stamp** | "Quote found in document" badge | Appears once per card when it enters view: scale 1.35 to 1, rotate -4deg to 0, opacity 0 to 1, 220ms with a tiny overshoot. Never repeats. |
| A4 | **Redaction reveal** | Processing and loading skeletons | Skeleton placeholders are solid dark bars. A scan line moves down the page preview. As each section completes, one bar retracts to the right (320ms) and reveals a placeholder line. |
| A5 | **Vault unlock** | Auth page success | Segmented ring rotates, segments latch one by one (3 x 120ms), ring opens like an iris (420ms) and the app fades in beneath. |
| A6 | **Orbit of trust** | Home hero | Document, local model and findings orbit a laptop glyph along a dashed ring. Outside the ring, a dashed "internet" line is cut by a small gap with a "no connection" mark. Loops every 12s. |
| A7 | **Staggered rise** | Result cards, stat tiles, table rows | Each item rises 16px and fades in, 40ms stagger, max 8 items animated. |
| A8 | **Count-up** | Stat tiles | Numbers count from 0 over 600ms with ease-out. |
| A9 | **Rail expand** | Navigation | Rail is 72px (icons only). On hover or focus-within it widens to 264px and labels slide in (220ms). Pinning is available. |
| A10 | **Underline draw** | Links and ghost buttons | Marker underline draws from left on hover (200ms). |
| A11 | **Page fan** | Home hero | Three document sheets fan out behind the headline on load (600ms stagger). They parallax a few pixels on pointer move (disabled under reduced motion). |
| A12 | **Segment ticks** | Processing progress | Progress shows one small page-shaped tick per section. Completed ticks fill with marker and give a 120ms bump. |
| A13 | **Shred** | Clear and start over | The document card slices into vertical strips that drop and fade (500ms), then the Home screen fades in. |
| A14 | **Breathing dot** | Privacy badge | The status dot has a very slow 4s opacity breathe (0.6 to 1). Off under reduced motion. |
| A15 | **Typewriter answer** | Ask tab | Answer text reveals line by line (60ms per line), not letter by letter. Quote blocks appear after the text. Skipped if reduced motion is on. |

### Rules
- Maximum one signature animation playing at a time on any screen, except ambient loops (A6, A14).
- No animation longer than 700ms except ambient loops and the processing scan line.
- **`prefers-reduced-motion`:** all signature animations become instant state changes or 120ms fades. Ambient loops stop. Information is never conveyed by motion alone.
- No bouncing, no confetti, no spinners that spin forever without progress text.

---

## 5. Components

### 5.1 Navigation rail
Left rail, 72px collapsed, 264px expanded (A9). Top: logo mark. Middle: destinations. Bottom: privacy badge, theme toggle, "Clear and start over".

Logo mark: a rounded square split by a horizontal red-less "redline" stroke through a document sheet, in marker yellow on ink. Wordmark "Redline" in Fraunces next to it when expanded, with the descriptor "Private legal triage" in caption.

Destinations (icon + label, active shown by marker pip on the left edge and raised background, plus bold label, so not colour alone):
1. Desk (upload)
2. Overview
3. Findings
4. Ask
5. Key facts
6. Checklist
7. Export
8. Privacy and model

Destinations 2 to 7 are disabled (muted, lock icon, tooltip "Analyse a document first") until a result exists.

### 5.2 Top bar (inside main area)
Breadcrumb ("Desk / Findings"), document chip (file icon, name in mono, page count), and a compact short disclaimer link. Height 56px, hairline bottom border.

### 5.3 Buttons
- **Primary:** marker fill, ink text, 44px tall, 10px radius. Hover: slight lift 1px and underline draw on label (A10). Press: scale .98. One per view.
- **Secondary:** transparent, `line-strong` border, paper text.
- **Ghost:** text only with underline draw.
- **Destructive:** secondary style, `error` text and trash icon, triggers A13.
- Disabled: 45% opacity plus visible helper text with the reason.

### 5.3b Badges
Pill, icon + text, 26px tall. Never icon-only.

| Field | Text | Style |
|---|---|---|
| explicit | "Stated in document" | Solid thin outline, doc icon |
| interpretation | "Possible reading" | **Dashed** outline, question icon |
| verified | "Quote found in document" | `found` tint, quote-check icon, stamp animation (A3) |
| unverified | "Could not verify quote" | `ember` tint, triangle icon |
| confidence | "Confidence: high / medium / low" | Neutral, 3-bar meter icon with 3, 2 or 1 bars filled. Tooltip: "Derived from checks, not from the model" |
| needs_human_review | "Review with a professional" | `review` tint, user-check icon |
| jurisdiction_dependent | "Depends on local law" | `jurisdiction` tint, globe icon |
| category | e.g. "Termination" | Plain text chip, tag icon |

### 5.4 Finding card ("margin note")
```text
+------------------------------------------------------------------+
| Auto-renewal of the lease                          [ p. 1 ]      |
| [Obligation] [Stated in document] [Quote found] [Confidence: high]|
| [Review with a professional] [Depends on local law]              |
|                                                                  |
| The lease renews for another eleven months unless you give       |
| notice at least 30 days before it ends.                          |
|                                                                  |
|  | "Unless either party gives written notice at least 30 days    |
|  |  before the end of the term ..."                              |
|                                                                  |
| [View in document]            [How this was checked  v]          |
+------------------------------------------------------------------+
```
- Surface card, 14px radius, 20px padding.
- Title in Inter Tight 17px, page chip right-aligned in mono.
- Quote block: inset background, 3px left border in `found`, mono text, label above "Quoted from the document".
- Selected card: 2px marker left edge, raised background, and A2 plays on its quote.
- Enter animation: A7. Verified badge: A3.
- **Unverified variant:** 1px `ember` border, triangle in header, quote label "Model's claimed quote", dashed left border on the quote block, no highlight action. Button reads "Open page without highlight".
- "How this was checked" expands the verification note, ungrounded figures ("These figures do not appear in the document: 40000") and any "Page corrected from X to Y".

### 5.5 Source viewer ("the sheet on the desk")
Sticky panel. Header: "Page N, highlighted passage", prev/next icon buttons, "N of M" counter. Body: page image on a slightly rotated (0.4deg) paper sheet with drop shadow, the highlight drawn by A2. For TXT: mono text with the quote in a `<mark>` with underline. Fallback note: "The passage was verified but could not be highlighted." Alt text: "Page N of the document with the cited passage highlighted". Empty state: a blank sheet outline with "Select a finding to see its page here."

### 5.6 Stat tile
Raised card, Fraunces numeral (A8), caption label under it, small icon top-right. 120px tall.

### 5.7 Quote block
Inset background, mono, 6px radius with a squared left edge, 3px left border (`found` for verified, dashed `ember` for unverified, `neutral` for silent evidence). Page chip bottom-right.

### 5.8 Answer card
Question as H3 with timestamp, answer area, evidence quotes, escalation note. States in section 6.8.

### 5.9 Error card
Rose 1px border and 8% tint, octagon icon, title, one plain sentence, "What to do" line, button. Mono commands have a copy icon. Never contains document text. Wording from `frontend.md` section 5.

### 5.10 Disclaimer
Neutral info container with a small scales icon, never amber and never dismissible.
- Short: "Informational only. Not legal advice." (rail, top bar, results header)
- Full: "This tool is for informational triage only and does not give legal advice. Take any clause that matters to a lawyer or legal aid service in your jurisdiction." (Overview, Export, Ask)

### 5.11 Tables
40px rows, hairline dividers, sticky header, mono values, "View page" ghost button per row, A7 stagger on first render. No zebra stripes.

### 5.12 Privacy badge
Teal-tinted capsule with shield-lock icon, text "Local only" and sub-line "Nothing leaves this computer", breathing dot (A14). If the network guard blocks a connection it becomes an `error` capsule "Connection blocked" linking to Privacy and model.

### 5.13 Tooltips for legal terms
First use of a legal term has a dotted underline. Hover or focus shows a one-line plain explanation in a small raised card.

---

## 6. Pages

### 6.0 Global shell
```text
+------+-------------------------------------------------------------+
| Rail | Top bar: breadcrumb | document chip | short disclaimer      |
| 72px +-------------------------------------------------------------+
|      |                                                             |
| logo |                    Page content                             |
| nav  |            (A1 page-turn between pages)                     |
|      |                                                             |
| lock |                                                             |
| theme|                                                             |
| clear|                                                             |
+------+-------------------------------------------------------------+
```
Home and Auth are full-bleed (no rail). Everything else uses the shell.

---

### 6.1 PAGE: Home (landing, full-bleed)
**Purpose:** Explain the promise, prove the privacy, and get the user to the vault or desk.

```text
+--------------------------------------------------------------------+
| (logo) Redline                  How it works  Privacy  [Open desk] |
|                                                                    |
|   Your contracts stay                    +-------------------+     |
|   on your computer.                      |  orbit animation  |     |
|   Understand them anyway.                |  (A6) laptop,     |     |
|                                          |  doc, model,      |     |
|   Upload a lease, job offer or terms     |  findings, cut    |     |
|   of service. Get a plain-language       |  internet line    |     |
|   overview with every claim tied to      +-------------------+     |
|   the exact page it came from.                                     |
|                                                                    |
|   [ Open my desk ]   [ See how privacy works ]                     |
|   Local only · No account · No cloud                               |
+--------------------------------------------------------------------+
| 1 Drop in a PDF  ->  2 Read locally  ->  3 Review with sources    |
+--------------------------------------------------------------------+
| What you get (3 cards)                                             |
|  Findings with sources | Ask the document | Key facts & checklist  |
+--------------------------------------------------------------------+
| Not a lawyer. Honest about limits. (two columns)                   |
|  What it does            |  What it will never do                  |
|  - Quotes the text       |  - Say a clause is legal or enforceable |
|  - Shows the page        |  - Replace a lawyer                     |
|  - Flags what to check   |  - Read scanned documents (yet)         |
+--------------------------------------------------------------------+
| Tested on: Rental agreements · Employment contracts · Terms        |
| Footer: model name, licence, disclaimer, "Verify offline" link     |
+--------------------------------------------------------------------+
```
**Details**
- Headline in Fraunces 56px. The words "stay on your computer" get a marker underline that draws in (A10) once on load.
- Background: warm spotlight behind the headline plus three paper sheets fanning out (A11). Orbit illustration (A6) on the right.
- Primary CTA "Open my desk" leads to Auth if the app lock is on, otherwise to the Desk.
- Secondary CTA scrolls to the privacy section, which previews the "How to verify" steps (turn Wi-Fi off, run the sample).
- How-it-works strip: three numbered steps, each icon draws itself on scroll into view (A7).
- "What it will never do" column uses neutral styling, not warning colours, and repeats the no-verdict rule.
- Honest scope note: "Text-based PDFs and TXT files. Scanned documents are not supported yet."
- Sections reveal with A7 on scroll. Sticky top bar gains a hairline border after 24px scroll.

**States:** none beyond theme. Readiness is not checked here.

---

### 6.2 PAGE: Auth, "Vault" (local app lock)
> **Important scope note.** The product has no accounts, servers or logins. This page is a **local app lock**: a passphrase that gates the screen on this computer, useful for shared machines. It is stored only as a salted hash on this device and nothing is sent anywhere. It is an optional extra on top of `frontend.md`. Without extra backend work it protects access to the UI, it does not encrypt documents, and the copy must not claim otherwise. If the team skips it, Home goes straight to the Desk.

**Layout:** full-bleed, centered vault card (440px) on a dark spotlight, with the segmented ring (A5) above it.

```text
              [ segmented vault ring ]
                 Unlock Redline
          Your passphrase never leaves this computer.

          Passphrase  [ ******************** ] (eye)
                      [ strength meter ]
          [ Unlock ]
          Forgot it?  Reset (clears this app's local session)
          ----------------------------------------------
          No account. No cloud. Nothing to sign in to.
```
**Variants (same card, content swaps with A1):**
1. **First run: "Set a passphrase."** Two fields (passphrase, confirm), strength meter with text label (Weak / Okay / Strong, plus icon), checklist of rules, buttons "Set passphrase" and ghost "Skip, I'm the only user".
2. **Returning: "Unlock Redline."** One field, "Unlock" button, caps-lock warning.
3. **Wrong passphrase:** card does a short horizontal shake (180ms), ring segments flash `error` and unlatch, inline message "That passphrase didn't match. Try again." Attempt counter after 3 tries adds a 5 second delay with a visible countdown.
4. **Reset confirmation:** neutral-info dialog, "Resetting removes the passphrase and clears any loaded document. Your files on disk are not touched." Buttons "Reset" (destructive) and "Cancel".
5. **Success:** ring latches and opens (A5), then the Desk page transitions in.

**Accessibility:** field is labelled, show/hide toggle has accessible name, Enter submits, errors announced via `aria-live`, strength and errors in text not only colour.

---

### 6.3 PAGE: Desk (upload and readiness) — F1, F2
**Purpose:** Get a valid document in, confirm the system is ready.

```text
Top bar: Desk
+--------------------------------------------------------------------+
| H1 (Fraunces) Put a document on the desk.                          |
| Understand a legal document without it leaving your computer.      |
|                                                                    |
| [ readiness banner: Local model ready ]                            |
|                                                                    |
| +----------------------------------+  +--------------------------+ |
| |  dashed paper dropzone           |  | Tested on                | |
| |  (sheet icon floats up on hover) |  |  Rental agreements       | |
| |  Drop a PDF or TXT here, or      |  |  Employment contracts    | |
| |  browse.   Max 50 MB             |  |  Terms of service        | |
| |  Text-based PDFs only. Scanned   |  |                          | |
| |  documents aren't supported yet. |  | [ Use sample document ]  | |
| +----------------------------------+  +--------------------------+ |
|                                                                    |
| (after parse) Document card:                                       |
| [file icon] rental_agreement.pdf                                   |
|  Pages 12 | Characters 38,204 | Little text 0 | PDF                |
|                                    [ Analyse document ]            |
+--------------------------------------------------------------------+
```
**Details**
- Dropzone: dashed 2px `line-strong` border. On drag-over, border becomes solid marker, a sheet icon lifts 6px and the label changes to "Release to put it on the desk" (220ms).
- On drop, the file "slides" onto the desk: a mini paper sheet animates from the dropzone into the document card (420ms, A1 variant).
- Readiness banner: `local` teal for ready, `ember` for not ready with copyable commands `ollama serve` and `ollama pull gemma3n:e2b`. Analyse is disabled until ready, helper text says why.
- Document card stat for "Pages with little text" uses an ember triangle when above 0 with caption "Some pages have little text. Results may be incomplete."
- Replacing the file triggers A13 on the old card, then the new card slides in.

**States:** idle, drag-over, parsing (redaction bar over the card, A4), ready, parse error (error card inline under the dropzone, see 6.13).

---

### 6.4 PAGE: Processing — F3
Full-width centered stage. No rail interaction except Cancel (rail links disabled).

```text
+--------------------------------------------------------------------+
| H2 Reading your document                                           |
| Everything is running on this computer.                            |
|                                                                    |
|        +----------------------+                                    |
|        |  page preview with   |   Reading section 3 of 12          |
|        |  scan line moving    |   [#][#][#][ ][ ][ ][ ] ... ticks  |
|        |  down (A4)           |   Elapsed 01:24 · About 3 min left |
|        +----------------------+                                    |
|                                                                    |
|  Findings will appear here once checking is finished:              |
|  [redaction bar skeleton] [redaction bar skeleton] [skeleton]      |
|                                                                    |
|                         [ Cancel ]                                 |
+--------------------------------------------------------------------+
```
- Segment ticks (A12), one per section, with text "Reading section 3 of 12" in addition to the visuals.
- Estimate appears only after the first section completes.
- Skeleton cards use the redaction look. Bars retract as sections finish (A4).
- **No partial findings** are shown before validation ends. A caption says so: "Findings appear after every quote has been checked."
- Cancel returns to the Desk with the document still loaded. A short toast: "Stopped. Your document is still loaded."
- On completion: scan line finishes, ticks flash once, then A1 transitions to Overview.

---

### 6.5 PAGE: Results header (shared by pages 6.6 to 6.11)
Strip under the top bar on every results page:

```text
rental_agreement.pdf     Findings 14 · Quote found 11 · Need review 4 · 02:41
Informational only. Not legal advice.
```
Four stat tiles with count-up (A8). Counts: findings, "Quote found in document", "Need review", elapsed time.

---

### 6.6 PAGE: Overview — F4, F13, X3, X5
```text
+--------------------------------------------------------------------+
| H1 Preliminary overview                                            |
| +----------------------------------------------+ +---------------+ |
| | Summary card (serif intro paragraph, then    | | Counts by     | |
| | plain-language bullets)                      | | category      | |
| | Note: A quote found in the document does not | | horizontal    | |
| | mean the reading is correct.                 | | bars (ink     | |
| +----------------------------------------------+ | blue, labels  | |
|                                                  | and numbers)  | |
| Needs professional review (top 5)                +---------------+ |
|  [violet icon] Early termination fee      p.7  ->  open finding    |
|  [violet icon] Indemnity clause           p.9  ->  open finding    |
|                                                                    |
| (if present) Notice: This document contains text that looks like   |
| instructions to an AI. It was treated as document content only.    |
|                                                                    |
| v Limitations (open by default)                                    |
| Full disclaimer with escalation advice                             |
+--------------------------------------------------------------------+
```
- Summary card is labelled "Preliminary overview" with a small dashed-outline badge "Possible reading" to signal interpretation.
- Category bars grow from the left (A7 style, 420ms). Bars have number labels so colour is not the only data carrier.
- Review shortlist rows open Findings with that finding selected and A2 playing.
- Prompt-injection notice (X5) uses neutral styling and an info icon.

---

### 6.7 PAGE: Findings — F5, F6, F7, F8
Hero screen. Two columns: list 55%, sticky source viewer 45%.

```text
+--------------------------------------------------------------------+
| H1 Candidate findings                                              |
| Filter bar: [Category v][Type v][Verification v][Confidence v]     |
|             [ ] Needs review only  [ search... ]  Sort: [Page v]   |
|--------------------------------------------------------------------|
| v Quote found in document (11)          |  Source viewer (sticky)  |
|   [finding card]                        |  Page 7, highlighted     |
|   [finding card] (selected)             |  passage        [<][>]   |
|   [finding card]                        |  +--------------------+  |
|                                         |  | paper sheet with   |  |
| > Could not be verified (3) (collapsed) |  | highlighted quote  |  |
|   These are shown so you can see what   |  +--------------------+  |
|   the model claimed. Treat with caution.|  7 of 12                 |
+--------------------------------------------------------------------+
```
- Filters collapse into a "Filters (2)" popover below 1100px.
- Active filters show as removable chips; "Clear filters" ghost button.
- List uses A7 on load, A3 for verified badges as they enter view.
- Selecting "View in document" updates the viewer only and plays A2. The viewer page flips with a small page-turn (A1 variant, 220ms).
- Unverified group collapsed by default with a neutral explanation and the `ember` triangle in its header.
- Empty state: sheet illustration plus "No findings were produced for this document. That does not mean it has no issues."
- "No results for these filters" state is separate and offers "Clear filters".

---

### 6.8 PAGE: Ask — F9, F10, X2
```text
+--------------------------------------------------------------------+
| H1 Ask the document                                                |
| [ What would you like to know?                       ] [ Ask ]     |
| Try: [When can the landlord end this?] [What fees are mentioned?]  |
|      [What happens if I leave early?]                              |
|--------------------------------------------------------------------|
| Answer cards, newest first                                         |
+--------------------------------------------------------------------+
```
Large single-line input with a marker caret and a rounded "Ask" primary. Example chips fill the input on click.

**Answer states**
| State | Presentation |
|---|---|
| Answered | Answer text (A15), badge "Stated in document" or "Possible reading", evidence quote blocks with page chip and "View in document" (opens Findings viewer in a side sheet), escalation note when jurisdiction-dependent |
| Silent | Neutral card with info icon, headline "The document doesn't seem to address this." Not an error. Escalation line below. |
| Verdict declined | Violet accent line, headline "I can't say whether this is legal or enforceable", then only what the text says, then escalation advice |
| Unverified evidence | Those quotes get the ember dashed treatment, excluded from "View in document" |
| Thinking | Redaction-bar skeleton (A4) with text "Reading the document locally..." and Cancel |
| Empty input | Inline "Please type a question." No error styling |

---

### 6.9 PAGE: Key facts — F11, X1
```text
| H1 Key facts                                                       |
| Amounts, dates, durations and percentages found in the text.       |
| [search facts...]   Type: [All v]                                  |
|--------------------------------------------------------------------|
| Label            | Value        | Page | Snippet            |      |
| Monthly rent     | 1,200        | 1    | "...rent of ..."   | View |
| Notice period    | 30 days      | 1    | "...at least 30..."| View |
```
- Table with A7 stagger. Values and snippets in mono.
- "View page" opens a side sheet containing the source viewer with the snippet highlighted (A2).
- Type filter chips use icons: currency, calendar, clock, percent.
- Empty state: "No amounts, dates or durations were found in the text."

---

### 6.10 PAGE: Checklist — F12
```text
| H1 Clause checklist                                                |
| Not found means the extracted text has no matching wording.        |
| It is not a legal conclusion.                                      |
|                                                                    |
| Wording found (7)               | No matching wording found (5)    |
|  (check-circle) Termination  p.7|  (dashed-circle) Subletting      |
|  (check-circle) Deposit      p.3|  (dashed-circle) Arbitration     |
```
- Two-column grouping. Icons: check-in-circle in neutral ink blue for found, dashed circle in muted for not found. Never green or red.
- Each found item has page chips and "View page" action (X1).
- Rows animate with A7. The caption sits above the lists, not hidden in a tooltip.

---

### 6.11 PAGE: Export — F15
```text
| H1 Export your report                                              |
| +------------------------------+  +------------------------------+ |
| | Report preview (paper sheet, |  | What's inside                | |
| | tilted 0.4deg, scrollable    |  |  - Findings with quotes      | |
| | mini render of the first     |  |  - Key facts                 | |
| | page of the Markdown)        |  |  - Clause checklist          | |
| +------------------------------+  |  - Questions you asked       | |
|                                   |  - Limitations & disclaimer  | |
|                                   | A quote found in the document| |
|                                   | does not mean the reading is | |
|                                   | correct. The report says so. | |
|                                   | [ Download Markdown report ] | |
|                                   +------------------------------+ |
```
- Primary download button. After click, the button shows a check and "Saved to your downloads" for 3s.
- Report is generated on demand, in memory only.

---

### 6.12 PAGE: Privacy and model — F14, X4
```text
| H1 Privacy and model                                               |
| +--------------------------------------------------------------+   |
| | What leaves this device during processing:  NOTHING.          |   |
| | (Fraunces 36px, marker underline)                             |   |
| +--------------------------------------------------------------+   |
| Live status card                                                   |
|   Processing endpoint   127.0.0.1:11434                            |
|   Network guard         Active                                     |
|   Blocked attempts      0 this session  (host names only)          |
|                                                                    |
| Network calls: Setup vs Processing (table)                         |
|                                                                    |
| How to verify (numbered, with the monitoring command in a mono     |
| block with copy icon):                                             |
|  1 Turn Wi-Fi off   2 Run the sample   3 Watch connections         |
|                                                                    |
| Threat model summary   |   Out of scope                            |
|                                                                    |
| Model: name, quantization, runtime, licence & attribution (link)   |
| Benchmark card: pages, chunks, model, elapsed s, memory (manual)   |
+--------------------------------------------------------------------+
```
- The top statement is the emotional centre of the page. Below it, proof.
- Live status values reflect real runtime state. If a blocked attempt exists, the card turns `error`-bordered with the host names listed in mono.
- "How to verify" steps are a vertical timeline with step numbers (not colour-coded).
- Benchmark memory field is a simple input with caption "Enter this manually".

---

### 6.13 PAGE: Errors — S5
Inline error card (5.9) replaces the current page content, rail stays usable. Includes a small illustration of a torn paper corner (neutral grey, not red). Messages:

| Backend error | Title | Next step |
|---|---|---|
| `UnsupportedFormat` | This file type isn't supported. | Upload a PDF or TXT. |
| `EncryptedDocument` | This PDF is password protected. | Remove the password and upload again. |
| `UnreadableDocument` | This file couldn't be read. | Try another copy or export it again. |
| `NoExtractableText` | No readable text was found. This may be a scanned document. | Use a text-based PDF. OCR isn't supported yet. |
| `OllamaUnavailable` | The local model isn't running. | Start it with `ollama serve`, then retry. |
| `ModelMissing` | The model isn't installed. | Run `ollama pull gemma3n:e2b`. |
| `ModelTimeout` | The model took too long. | Retry, or use a smaller document. |
| `InvalidModelOutput` | The model's reply couldn't be used. | Retry. Nothing was guessed or filled in. |
| `EmptyQuestion` | Please type a question. | None (inline, neutral). |
| `PrivacyViolation` | A network connection was blocked to protect your document. | Report this; it should not happen. |

Retry keeps the loaded document. Entering animation: card rises (A7) with no shake.

---

### 6.14 FLOW: Clear and start over — F16
Rail button, destructive style. Opens a small confirm popover: "This deletes the document and every result from this session. It cannot be undone." Buttons "Delete everything" and "Cancel". On confirm: A13 shred plays on the current content, then Home or Desk fades in with a toast "Session cleared. Temporary files were removed."

---

### 6.15 COMPONENT PAGE: Disclaimer and escalation — F17
Not a page, but it must appear in every context listed in section 5.10: rail footer, top bar link, results header, Overview, Ask, Export, and Home footer.

---

## 7. Navigation and flow map

```text
Home -> (Auth, optional) -> Desk -> Processing -> Overview
                                         |            |
                                         |            +-> Findings <-> Source viewer
                                         |            +-> Ask
                                         |            +-> Key facts -> Source viewer
                                         |            +-> Checklist -> Source viewer
                                         |            +-> Export
Privacy and model: reachable from the rail on every page
Errors: inline on any step
Clear and start over: from any state, returns to Home or Desk
```
Note on `frontend.md`: it defines five results tabs. This design splits Key facts and Checklist into separate destinations and surfaces all results pages in the rail for clarity. If you want to stay strictly with five tabs, merge 6.9 and 6.10 into one page with two sections.

---

## 8. Responsive behaviour
| Width | Behaviour |
|---|---|
| 1200+ | Full layout as above |
| 900-1199 | Rail stays collapsed (icons), filters become a popover, viewer stays beside list at 40% |
| under 900 | Rail becomes a bottom bar (icons), viewer opens as a full-height sheet from the bottom when "View in document" is pressed, tables become stacked cards |

---

## 9. Accessibility
- Status is always icon + text + shape (dashed vs solid outlines, bar counts), never colour alone.
- Contrast targets met in both themes, including text on marker yellow.
- Single `h1` per page, logical headings.
- Everything keyboard reachable, visible 2px marker focus ring with 2px offset.
- Page images have alt text and captions.
- `aria-live="polite"` for processing progress and toasts, `assertive` for errors.
- `prefers-reduced-motion` respected as defined in section 4.
- Reading level aimed at non-lawyers, with tooltips for legal terms.

---

## 10. Content and tone
- Use "candidate findings", "possible concern", "preliminary overview".
- Never say "illegal", "safe to sign", "enforceable", "valid" or "risk-free" as the tool's own judgement.
- "Quote found in document" never implies the reading is right. Overview and Export both say so.
- Errors say what happened in one sentence and what to do next. No document text in errors.
- Microcopy has a quiet voice with small editorial touches ("Put a document on the desk", "Session cleared"), never jokes about legal outcomes.

---

## 11. Do and don't
**Do**
- Make verified and unverified clearly different without colour.
- Keep the source page next to every finding.
- Keep the privacy status and disclaimer visible or one click away.
- Reserve motion for state changes and the few signature moments.

**Don't**
- No navy-and-purple gradient, glassmorphism, neon glow, robot or brain imagery, or stock photos.
- No green "safe" markers, no red severity on findings.
- No spinners without text, no endless looping decoration other than the two ambient loops.
- No partial findings before validation finishes.
- Don't style "document is silent" as an error.

---

## 12. Streamlit implementation notes
Streamlit limits what can be animated, so use these approaches:

- **Theme base** in `.streamlit/config.toml`: `[theme] base = "dark"`, `primaryColor = "#F7D748"`, `backgroundColor = "#0D0C0A"`, `secondaryBackgroundColor = "#181612"`, `textColor = "#F3EDE0"`. Everything else via injected CSS using CSS variables for both themes.
- **Fonts offline:** put Fraunces, Inter, Inter Tight and JetBrains Mono `.woff2` files in `static/fonts/`, set `enableStaticServing = true` under `[server]`, and reference them with `@font-face` pointing to `/app/static/fonts/...`. Do not use Google Fonts or any CDN.
- **Icons:** inline SVG (Lucide-style) in `ui/icons.py`, no icon-font CDN.
- **CSS animation:** keyframes injected with `st.markdown(..., unsafe_allow_html=True)`. A1, A2, A3, A7, A10, A12, A14 are pure CSS. A4 uses CSS gradients and `clip-path`. A5 and A13 are CSS animations on an HTML block, triggered by state change then followed by `st.rerun()` after the duration.
- **Home and Auth:** render as full-bleed pages with `st.set_page_config(initial_sidebar_state="collapsed")` plus CSS hiding the header, then show the rail only on shell pages. Use `st.navigation` or a state-driven router in `app.py`.
- **Rail:** style the native sidebar (`[data-testid="stSidebar"]`) to 72px and expand on hover with CSS `:hover` and `:focus-within`.
- **Count-up (A8):** CSS `@property --n` with `counter()` or a small inline script in a component. Fall back to static numbers.
- **Sticky viewer:** CSS class on the right column container with `position: sticky; top: 72px`.
- **Reduced motion:** wrap every animation in `@media (prefers-reduced-motion: no-preference)`.
- **Safety:** escape all document text before injecting into any HTML snippet.
- **Components:** badges, cards, quote blocks, stat tiles, answer cards and error cards are helper functions in `ui/components.py`. All strings in `ui/text.py`.
- **Suggested file additions:** `ui/home.py`, `ui/auth.py`, `ui/theme.py` (CSS and tokens), `ui/icons.py`, `static/fonts/`.

---

## 13. Build order for the design
1. Tokens and theme CSS, fonts, rail shell.
2. Desk page with dropzone and document card.
3. Findings page: finding card, badges, source viewer, A2 and A3.
4. Processing page with A4 and A12.
5. Overview, Ask, Key facts, Checklist, Export.
6. Privacy page and error cards.
7. Home page with orbit and page-fan.
8. Auth vault with A5.
9. Shred and polish animations, reduced-motion pass, light theme pass.

---

## 14. How to use this file with Stitch
Generate one page at a time and keep this file attached as the design system. Suggested order: **Findings** (hero), **Home**, **Desk**, **Processing**, **Auth**, **Overview**, **Ask** (show all four answer states), **Privacy and model**, **Error**. Ask for each in dark, then "same screen in the Paper Room light theme". Stitch produces static screens, so describe the animations in annotations and implement them in CSS afterwards.
