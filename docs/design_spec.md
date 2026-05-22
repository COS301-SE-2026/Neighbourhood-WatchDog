# Neighbourhood WatchDog Design Specification

---

## 1. Introduction

Neighbourhood WatchDog is an AI powered surveillance platform designed to enhance the safety of South African neighbourhoods. The platform integrates surveillance systems with computer vision to detect suspicious behavior and alert security personnel and residents.

### Our Vision

To enhance community safety through the use of intelligent surveillance systems that residents and security professionals can fully trust.

### Our Mission

To provide South African communities with a platform that detects threats and communicates them reliably, allowing security teams and law enforcement to act before incidents escalate.

### Mascot

The German Shepherd was chosen as the Neighbourhood WatchDog mascot because it embodies the qualities of our platform. Dogs are universally regarded as protectors and as man's best friend. We want every user to trust the platform the way they would trust a guard dog. The mascot reinforces our role in the community, always alert and always on watch.

---

## 2. Brand Foundation

The brand foundation defines the personality, voice, and values of Neighbourhood WatchDog. Every design decision, from colour choice to copy tone, should trace back to these principles.

### Core Values

| Value | What It Means |
|-------|---------------|
| Vigilance | The platform is always watching. UI states, alerts, and indicators must communicate aliveness and attentiveness at all times. |
| Trust | Users depend on us with their safety. The design must feel authoritative, reliable, and calm, never alarmist or confusing. |
| Clarity | Alerts are time-critical. Information hierarchy must be ruthless. The most important information must be immediately obvious. |
| Community | WatchDog exists to protect people. The tone is human, approachable, and empathetic, not cold or institutional. |
| Precision | Detections, timestamps, and locations must be communicated with exactness. No ambiguity in safety-critical contexts. |

### Brand Voice

WatchDog's voice is that of a calm, expert protector. It is direct and confident, never anxious or vague. In normal operational states the tone is composed and professional. When a threat is detected the tone becomes urgent but not panicked, decisive but not alarming. Error messages explain what happened and what the user should do next. Success confirmations are brief and reassuring.

| Always | Sometimes | Never |
|--------|-----------|-------|
| Direct and specific. Action-oriented. | Calm under pressure. Empathetic to users. | Vague or ambiguous. Alarmed or panicked. |
| | Firm when escalating. Concise summaries. | Overly technical jargon. Passive voice in alerts. |

---

## 3. Colour Palette

The WatchDog colour system is built around deep navy, electric blue, and neutral greys. These colours communicate authority, intelligence, and trust. Semantic colours follow standard conventions and must not be repurposed for other meanings.

### Primary Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Command Navy | `#1D2A5E` | rgb(29, 42, 94) | Primary brand colour. Used for headings, the primary nav bar, and high-authority surfaces. |
| Alert Blue | `#3B5EDE` | rgb(59, 94, 222) | Primary interactive colour. Buttons, links, active states, focus rings, and chart accents. |
| Sky Blue | `#5B8DEF` | rgb(91, 141, 239) | Secondary interactive. Hover states, secondary buttons, and informational badges. |
| Steel | `#2C3E6B` | rgb(44, 62, 107) | Subheadings, sidebar backgrounds, table headers, card chrome. |

### Neutral Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| White | `#FFFFFF` | rgb(255, 255, 255) | All page and card backgrounds on light theme. |
| Fog | `#F4F6FA` | rgb(244, 246, 250) | Alternate row backgrounds, input backgrounds, subtle surface distinction. |
| Mist | `#D0D7E8` | rgb(208, 215, 232) | Borders, dividers, and table lines. |
| Ink | `#1A1A2E` | rgb(26, 26, 46) | Primary body text on light backgrounds. |

### Semantic Colours

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Threat Red | `#DC2626` | rgb(220, 38, 38) | Critical alerts. High-severity detections. Destructive action confirmation states. |
| Caution Amber | `#D97706` | rgb(217, 119, 6) | Medium-severity alerts. Warning states. Items requiring attention but not immediate action. |
| Safe Green | `#16A34A` | rgb(22, 163, 74) | System online. Camera active. Resolved incident. Positive confirmation states. |
| Info Blue | `#0284C7` | rgb(2, 132, 199) | Informational notices. Non-urgent system messages. Tooltip accents. |

### Colour Usage Rule: 60/30/10

- **Dominant (60%):** Navy and White for surfaces and backgrounds.
- **Supporting (30%):** Steel and Fog for structural elements like sidebars, tables, and cards.
- **Accent (10%):** Alert Blue and semantic colours exclusively for interactive elements, key data, and status indicators. Never apply accent colours to large background areas.

### Accessibility Requirements

All colour combinations used for text must meet WCAG 2.2 AA contrast ratios: 4.5:1 for body text, 3:1 for large text (18pt+) and UI components. Do not rely on colour alone to convey alert severity — always pair with an icon and/or a text label.

| Combination | Foreground | Background | Contrast Ratio |
|-------------|------------|------------|----------------|
| Body text | `#1A1A2E` | White | >= 15:1 |
| Primary button label | White | `#3B5EDE` | >= 4.5:1 |
| Nav bar text | White | `#1D2A5E` | >= 8:1 |
| Alert badge text | White | `#DC2626` | >= 4.5:1 |
| Caption / meta text | `#2C3E6B` | White | >= 7:1 |

---

## 4. Typography

Typography is the primary carrier of information in WatchDog. The type system uses two typefaces that work together to create a hierarchy that is clear, scannable, and purposeful. All sizing uses a consistent scale derived from a 1.25 (Major Third) modular ratio.

### Typefaces

| | Inter | JetBrains Mono |
|--|-------|----------------|
| **Role** | Display, headings, labels, and all UI text | Code snippets, timestamps, IDs, and technical data strings |
| **Why chosen** | Highly legible at small sizes. Optimised for screen rendering. Neutral but confident personality. Wide weight range. | Monospaced clarity for camera IDs, alert codes, and timestamps. Reduces reading errors in technical data. |
| **Weights used** | Regular (400), Medium (500), SemiBold (600), Bold (700) | Regular (400), Bold (700) |
| **Fallback** | system-ui, -apple-system, sans-serif | Consolas, Courier New, monospace |

### Type Scale

The scale uses a 1.25 ratio (Major Third) starting from a 14px base. Line height is always paired with the size and shipped as a single token. Reading width for body text must be constrained to 60–75 characters per line.

| Token | Size | Line Height | Weight | Usage |
|-------|------|-------------|--------|-------|
| `display` | 48px / 3rem | 56px | Bold 700 | Page titles, hero headings |
| `heading-1` | 32px / 2rem | 40px | Bold 700 | Section headings (H1) |
| `heading-2` | 24px / 1.5rem | 32px | SemiBold 600 | Subsection headings (H2) |
| `heading-3` | 20px / 1.25rem | 28px | SemiBold 600 | Card titles, panel headers (H3) |
| `body-lg` | 18px / 1.125rem | 28px | Regular 400 | Lead paragraphs, emphasis body |
| `body` | 16px / 1rem | 24px | Regular 400 | Default body text, descriptions |
| `body-sm` | 14px / 0.875rem | 20px | Regular 400 | Secondary body, helper text |
| `label` | 14px / 0.875rem | 20px | Medium 500 | Form labels, table headers |
| `caption` | 12px / 0.75rem | 16px | Regular 400 | Timestamps, metadata, captions |
| `code` | 14px / 0.875rem | 20px | Regular 400 | Camera IDs, alert codes, timestamps |

### Typography Rules

- Never set font size outside the defined scale. If a new size is needed, extend the scale and document it here.
- Use weight to create hierarchy within the same size; do not mix sizes when weight alone suffices.
- Body text line width must not exceed 75 characters (roughly 680px at 16px). Use `max-width` constraints on prose containers.
- Alert titles must always use `heading-3` or above. Never use `caption` or `body-sm` for primary alert information.
- Timestamps and camera IDs must always use the `code` token (JetBrains Mono). This prevents misreading similar characters.
- Do not use italic for anything other than inline code emphasis or quotations. Italics reduce legibility at small sizes on screens.

---

## 5. Spacing System

WatchDog uses an 8px base grid. Every spacing value is a multiple of 8px (or 4px for fine-grained adjustments within components). Consistent spacing creates rhythm and makes the interface feel intentional and structured.

### Spacing Scale

| Token | Value (px) | Value (rem) | Usage |
|-------|------------|-------------|-------|
| `space-1` | 4px | 0.25rem | Icon-to-label gap, tight inline padding, fine adjustments only |
| `space-2` | 8px | 0.5rem | Internal component padding (badge, chip). Gaps between icon and text in buttons. |
| `space-3` | 12px | 0.75rem | Input field internal padding. Compact list item padding. |
| `space-4` | 16px | 1rem | Default internal padding for cards, panels, and form fields. |
| `space-5` | 24px | 1.5rem | Gap between related components. Section padding within a card. |
| `space-6` | 32px | 2rem | Space between distinct card/panel groups. Column gutters in layouts. |
| `space-8` | 48px | 3rem | Major section separators within a page. |
| `space-10` | 64px | 4rem | Page-level section breaks. Top-of-page breathing room. |
| `space-12` | 96px | 6rem | Hero sections, empty states, large display spacing. |

### Layout Grid

The dashboard uses a 12-column grid with 24px gutters and 32px page margins. Content areas are constrained to a maximum width of 1440px and centred. The sidebar occupies 2 columns (fixed at 240px) on desktop. The main content area spans the remaining 10 columns.

| Breakpoint | Viewport | Columns | Gutter |
|------------|----------|---------|--------|
| mobile | < 640px | 4 | 16px |
| tablet | 640px – 1024px | 8 | 20px |
| desktop | 1024px – 1440px | 12 | 24px |
| wide | > 1440px | 12 (max-width capped) | 24px |

---

## 6. Design Tokens

Design tokens are the contract between design and code. Every colour, spacing value, radius, shadow, and motion timing is named and referenced by token. Update a token once and the change reflects across the web dashboard.

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `radius-sm` | 4px | Badges, chips, small inline tags |
| `radius-md` | 8px | Buttons, input fields, small cards |
| `radius-lg` | 12px | Main content cards, alert panels, camera feed tiles |
| `radius-xl` | 16px | Modal dialogs, drawer panels |
| `radius-full` | 9999px | Pills, avatar containers, toggle switches |

### Elevation and Shadows

| Token | CSS Value | Usage |
|-------|-----------|-------|
| `shadow-sm` | `0 1px 3px rgba(29,42,94,0.08)` | Subtle card lift. Default card state. |
| `shadow-md` | `0 4px 12px rgba(29,42,94,0.12)` | Hovered card. Dropdown menus. |
| `shadow-lg` | `0 8px 24px rgba(29,42,94,0.16)` | Active modal. Slide-over panels. |
| `shadow-alert` | `0 0 0 3px rgba(220,38,38,0.30)` | Critical alert focus ring. Camera feed in alarm state. |

### Motion

Motion communicates state change. It must feel purposeful, quick enough not to impede workflow, deliberate enough to signal that something has changed. All duration and easing values are tokens.

| Token | Duration | Easing | Usage |
|-------|----------|--------|-------|
| `motion-instant` | 0ms | none | State switches where animation would feel sluggish (tab selection) |
| `motion-fast` | 100ms | ease-out | Hover states, focus rings, small micro-interactions |
| `motion-normal` | 200ms | ease-in-out | Button presses, card expand/collapse, dropdown open |
| `motion-slow` | 350ms | ease-in-out | Modal enter/exit, panel slide, page transitions |
| `motion-alert-pulse` | 1200ms | ease-in-out, infinite | Pulsing ring on critical alert camera feed tiles |

---

## 7. Component Patterns

Components are the reusable building blocks of the WatchDog interface. Each component has a defined set of states, variants, and accessibility requirements. Building from these composable units ensures consistency across all views.

### Alert Badge (Severity Indicator)

Alert badges communicate the severity level of a detection event. They always appear paired with a label, never as colour-only indicators.

| Variant | Background | Text | When to use |
|---------|------------|------|-------------|
| CRITICAL | `#DC2626` | White | Weapon detected, perimeter breach, fall detected. Requires immediate response. |
| HIGH | `#D97706` | White | Loitering beyond threshold, unrecognised person in restricted zone. |
| MEDIUM | `#0284C7` | White | Perimeter scanning behaviour, person detection in monitored area. |
| LOW | `#16A34A` | White | Informational event. Camera motion in unrestricted zone. |
| RESOLVED | `#D0D7E8` | `#2C3E6B` | Historical record. Incident acknowledged and closed. |

### Button

Buttons must have a visible label and a logical action. Never disable a button without explaining why — use a tooltip or helper text instead. All buttons must have a visible focus state (3px Alert Blue outline, 2px offset) for keyboard navigation.

| Variant | Background | Usage | When to use |
|---------|------------|-------|-------------|
| Primary | `#3B5EDE` filled, white label | One per view. The single most important action (Acknowledge Alert, Confirm). | Primary call to action |
| Secondary | Transparent, outlined `#3B5EDE` border and label | Supporting actions that are important but not the primary call to action. | Secondary actions |
| Ghost | Transparent, blue text only, no border | Low-emphasis actions within dense UI (table rows, card footers). | Tertiary/inline actions |
| Danger | `#DC2626` filled, white label | Destructive actions only (Delete Camera, Remove User). Always requires confirmation. | Destructive actions |
| Icon-only | Transparent, icon, no label | Tight spaces like toolbars. Must include `aria-label`. Tooltip on hover required. | Space-constrained toolbars |

### Camera Feed Tile

Camera tiles are the primary information unit on the monitoring dashboard. They communicate both live stream status and threat state simultaneously.

- **Active / Clear:** Standard border (Mist). Camera name in `heading-3`. Stream preview fills the tile.
- **Active / Alert:** Animated red ring using `shadow-alert` token. Corner badge shows severity. Name text colour switches to Threat Red.
- **Offline:** Greyed-out tile with offline icon centred. Name displayed in `body-sm` italic. No stream preview.
- **Reconnecting:** Tile shows spinner in centre. Amber border (Caution Amber). Tooltip shows last seen timestamp.

### Navigation

The primary navigation is a fixed left sidebar on desktop and a bottom tab bar on mobile. Navigation items include icon and label pairs. The active item is indicated by a filled Alert Blue left border and a Fog background. Unread alert count is shown as a badge on the Alerts nav item using the CRITICAL badge style.

---

## 8. Accessibility

WatchDog is a safety-critical application. Accessibility is not optional — it ensures that users operating under stress, in low-light conditions, or with assistive technologies can use the platform reliably. All components must meet WCAG 2.2 AA as a minimum.

### POUR Principles

| Principle | Requirement | WatchDog Implementation |
|-----------|-------------|------------------------|
| Perceivable | Content must be presentable to users in ways they can perceive. | Colour is never the sole indicator of state. All severity levels pair colour with icon and text label. Images of camera feeds include descriptive alt attributes. |
| Operable | Interface components must be operable by keyboard and assistive tech. | All interactive elements reachable via Tab. Focus rings are visible (3px blue outline). Alert acknowledgement possible without a mouse. |
| Understandable | Information and UI operation must be understandable. | Error messages state what happened and what to do. Form fields have persistent labels. Confirmation dialogs clearly state the consequence of the action. |
| Robust | Content must be interpretable by assistive technologies. | Semantic HTML throughout. ARIA roles and labels on all custom components. Live regions (`aria-live=assertive`) on the alert feed for screen reader users. |

---

## 9. Logo and Identity

The Neighbourhood WatchDog logo consists of the mascot mark (German Shepherd within a circular badge containing a home icon, network nodes, and gear elements). The logo has been designed in two tones: the deep Navy/Blue gradient primary version and a white monochrome version for use on dark backgrounds.

### Clear Space

A minimum clear space equal to the height of the home icon within the mascot badge must be maintained on all sides of the logo. No other visual elements, text, images, or borders should enter this exclusion zone.

### Approved Usage

- **Primary:** Full colour logo (navy + blue) on white or light backgrounds.
- **Reversed:** White monochrome on Navy or dark photographic backgrounds.
- **Icon only:** Mascot badge alone, without wordmark, for favicon, app icon, or avatar contexts.

### Prohibited Usage

- Do not recolour the logo outside of the approved two variants.
- Do not apply drop shadows, strokes, or glows to the logo.
- Do not place the logo on busy photographic backgrounds without a sufficient contrast overlay.
- Do not stretch, skew, rotate, or otherwise distort the logo mark.
- Do not use the wordmark without the mascot mark in external-facing contexts.

---

## 10. Writing Style

Writing is part of the interface. Every label, error message, confirmation, and tooltip is a design decision. WatchDog copy should feel like a trusted security professional communicating clearly under pressure.

### UI Copy Guidelines

- Use active voice. "Camera offline" not "The camera has been reported as offline."
- Be specific. "Camera 04, Entrance Gate" not "A camera has gone offline."
- Lead with what the user needs to know, follow with context.
- Alert titles are sentence case, max 8 words. Details go in the description.
- Avoid abbreviations unless they are universally understood (CCTV, AI, ID).
- Use South African English spelling conventions (colour, licence, analyse).

### Alert Copy Patterns

| Context | Do ✓ | Don't ✗ |
|---------|------|---------|
| Alert title | Person detected, Restricted Zone 3 | Alert notification from camera subsystem 3 |
| Alert description | YOLOv8 detected a person in Zone 3 (Rear gate) at 14:23. Confidence: 94%. No authorised persons scheduled. | Suspicious activity was detected by the AI model at the rear of the premises. |
| Camera offline | Camera 07, Offline. Last seen 2 min ago. | Camera connection error. |
| Success state | Alert acknowledged. Assigned to Officer Dlamini. | The operation was completed successfully. |
| Error state | Could not load camera feed. Check network connection. | Error 503. |

---

## 11. Token Quick Reference

The following CSS custom property declarations represent the complete token set for the WatchDog web dashboard. These should be defined on `:root` and consumed throughout all component styles. Never use raw values — always reference a token.

```css
:root {
  /* Colour - Brand */
  --color-navy: #1D2A5E;
  --color-blue: #3B5EDE;
  --color-sky: #5B8DEF;
  --color-steel: #2C3E6B;

  /* Colour - Neutral */
  --color-white: #FFFFFF;
  --color-fog: #F4F6FA;
  --color-mist: #D0D7E8;
  --color-ink: #1A1A2E;
  --color-body: #2E3A5C;

  /* Colour - Semantic */
  --color-threat: #DC2626;
  --color-caution: #D97706;
  --color-safe: #16A34A;
  --color-info: #0284C7;

  /* Typography */
  --font-sans: 'Inter', system-ui, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;
  --text-display: 3rem/3.5rem var(--font-sans);
  --text-h1: 2rem/2.5rem var(--font-sans);
  --text-h2: 1.5rem/2rem var(--font-sans);
  --text-h3: 1.25rem/1.75rem var(--font-sans);
  --text-body: 1rem/1.5rem var(--font-sans);
  --text-sm: 0.875rem/1.25rem var(--font-sans);
  --text-caption: 0.75rem/1rem var(--font-sans);
  --text-code: 0.875rem/1.25rem var(--font-mono);

  /* Spacing */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
  --space-4: 16px;  --space-5: 24px;  --space-6: 32px;
  --space-8: 48px;  --space-10: 64px; --space-12: 96px;

  /* Border Radius */
  --radius-sm: 4px;   --radius-md: 8px;
  --radius-lg: 12px;  --radius-xl: 16px;
  --radius-full: 9999px;

  /* Motion */
  --motion-fast: 100ms ease-out;
  --motion-normal: 200ms ease-in-out;
  --motion-slow: 350ms ease-in-out;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(29,42,94,.08);
  --shadow-md: 0 4px 12px rgba(29,42,94,.12);
  --shadow-lg: 0 8px 24px rgba(29,42,94,.16);
  --shadow-alert: 0 0 0 3px rgba(220,38,38,.30);
}
```
