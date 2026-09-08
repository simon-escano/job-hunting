# Design System Guidelines & Philosophy (`design.md`)

A comprehensive, opinionated guide to crafting high-craft, human-centric web applications. This document outlines core design principles, token systems, animation standards, copywriting rules, and anti-patterns to ensure software looks deliberate, bespoke, and distinctly non-generic.

---

## 1. Core Philosophy & Guiding Manifesto

1. **Substance Over Spectacle**: A tool should feel sharp, reliable, and respectful of the user's focus. Visual flair should reward intent, not mask a lack of utility.
2. **Ruthless Simplification**: Eliminate every visual element that does not convey meaning, establish hierarchy, or aid orientation.
3. **No "Vibecoding" Artifacts**: Avoid generic AI-generated aesthetic tropes. Custom craftsmanship always trumps boilerplates and untouched component kits.
4. **Human-First Language**: The interface is an earnest conversation with a person trying to get work done—not a marketing deck or an engineering thesis.
5. **Tactile Micro-Interactions**: Small, physics-based feedback loops (springs, gestures, deliberate states) ground digital software into something tangible.

---

## 2. Anti-Vibecoding Manifesto: 20 Prohibitions & Fixes

Modern interfaces often fall into predictable AI/template design traps ("vibecoded"). Every project must explicitly avoid these 20 pitfalls:

| # | Vibecoding Anti-Pattern | Why It Fails | Bespoke Alternative / Fix |
|---|---|---|---|
| **01** | **Purple-to-Blue Gradients** | Overused cliché; looks like a generic SaaS template from 2023. | Use a restrained, distinctive palette with deliberate solid accents and tonal neutrals. |
| **02** | **Gradient Hero Text** | Degrades contrast and legibility; screams low-effort marketing hype. | Crisp, solid-color typography with impeccable kerning, optical weights, and high contrast. |
| **03** | **Emojis in Headings** | Cheapens the product aesthetic; looks childish and disorganized. | Use clear, semantic typography or purposeful custom SVG iconography. |
| **04** | **Inter Everywhere** | Default aesthetic apathy. Inter is capable, but default usage feels sterile. | Curate typographic pairings with character (e.g., Geist, Satoshi, Basier, General Sans, Archivo). |
| **05** | **Colored Border Cards** | Heavy-handed and distracting; competes with actual data content. | Subtle 1px neutral borders (`rgba(0,0,0,0.08)` or `rgba(255,255,255,0.08)`) or soft tonal separation. |
| **06** | **Glassmorphism Everywhere** | Muddy readability, high GPU overhead, and inconsistent contrast across backgrounds. | Crisp, opaque surfaces with deliberate border separation and subtle, diffuse drop shadows. |
| **07** | **Low-Contrast Dark Mode** | Charcoal text on pitch-black or grey-on-dark-grey is hostile to accessibility. | High-contrast WCAG AAA compliance. Dark text at ≥70% lightness against elevated dark surfaces. |
| **08** | **3 Icon Boxes in a Row** | The ultimate generic feature grid; users mentally tune it out as marketing fluff. | Asymmetric layouts, interactive live previews, or real contextual UI states showing the workflow. |
| **09** | **Badge Above the Headline** | Pill-shaped badges like `🚀 Announcement: v2.0` create visual clutter before the main value. | Lead immediately with your primary statement or integrate meta-context into a cleaner header. |
| **10** | **Lucide Icons Everywhere** | Over-reliance on generic icon kits makes distinct apps look identical. | Use icons sparingly; prioritize text labels over cryptic icons. Custom-tune stroke widths. |
| **11** | **Untouched shadcn/ui** | Dropping default shadcn without theming or radius tweaks produces cookie-cutter clones. | Customize CSS tokens, border radii, padding density, typography, and interactive hover states. |
| **12** | **Fade-In on Scroll Everywhere** | Annoying scroll-jacking and visual latency; delays information retrieval. | Static or instant rendering for content. Restrict subtle entrance animations strictly to first mount. |
| **13** | **Cursor-Following Glow/Beam** | Gimmicky novelty that drains CPU/GPU and distracts the eye from actionable targets. | Eliminate gimmicky canvas followers. Use crisp, CSS-driven native cursor and focus indicators. |
| **14** | **Buttons Fade on Hover** | Sloppy opacity transitions feel sluggish and cheap. | Use subtle background color shifts, subtle scale (`0.98` on click), or micro-shadow elevations. |
| **15** | **Inconsistent Spacing** | Arbitrary margin and padding numbers create visual disharmony. | Strict 4px/8px modular grid scale. Lock all spacing to defined design tokens (`space-1` to `space-16`). |
| **16** | **Em Dashes Everywhere** | Pervasive `—` is a hallmark of unedited LLM generated copy. | Clean, concise, punchy sentences. Structure points with bullets or clear syntactic phrasing. |
| **17** | **Generic Buzzword Copy** | Phrases like *"supercharge your workflow"* or *"unleash seamless potential"* say nothing. | Concrete, direct, truthful language describing what the user actually gets and can do. |
| **18** | **Serif Italic Accents** | Staged, pseudo-intellectual italic words in serif headlines are overdone. | Confident, clean typography without decorative italic crutches. |
| **19** | **Space Grotesk + Instrument Serif** | The default hipster aesthetic pair that has saturated recent agency templates. | Choose typography tailored to the exact tone of your domain rather than trending font pairings. |
| **20** | **Grain Over a Gradient** | Adding noisy texture overlays to compensate for weak layout structure. | Strong spatial layout, clean geometry, whitespace discipline, and solid visual hierarchy. |

---

## 3. Color Architecture & Token System

### 3.1 Primary Color Foundations
A high-energy, contemporary palette built on stark monochrome structure, accented with electric chartreuse and solar yellow.

- **Base Canvas**: `#FCFCFC` (Pristine light off-white)
- **Primary Accent (Lime / Chartreuse)**: `#D2F898` (Fresh, organic, electric highlight)
- **Secondary Accent (Solar Lemon)**: `#F6F930` (High-energy focal trigger / badge / state indicator)
- **Deep Neutral (Charcoal / Ink)**: `#2F2F2F` (Softened black for readable typography)
- **True Pitch**: `#000000` (Stark structural contrast, primary buttons, deep borders)

---

### 3.2 Dual-Mode Token System (Light, Dark, System)

Support system preference automatically via `prefers-color-scheme`, while offering manual override.

```css
:root {
  /* Canvas & Surfaces */
  --bg-canvas: #FCFCFC;
  --bg-surface: #FFFFFF;
  --bg-surface-elevated: #F5F5F3;
  --bg-surface-subtle: #EFEFEA;
  
  /* Text & Content */
  --text-primary: #121212;
  --text-secondary: #2F2F2F;
  --text-muted: #6B7280;
  --text-faint: #9CA3AF;
  --text-inverse: #FCFCFC;
  
  /* Borders & Dividers */
  --border-subtle: rgba(0, 0, 0, 0.06);
  --border-default: rgba(0, 0, 0, 0.12);
  --border-strong: #2F2F2F;
  
  /* Accents & Brand */
  --accent-lime: #D2F898;
  --accent-lime-fg: #142403;
  --accent-lemon: #F6F930;
  --accent-lemon-fg: #2E2F00;
  
  /* Interactive Controls */
  --btn-primary-bg: #000000;
  --btn-primary-fg: #FFFFFF;
  --btn-primary-hover: #2F2F2F;
  
  --btn-accent-bg: #D2F898;
  --btn-accent-fg: #142403;
  --btn-accent-hover: #C3EE80;
}

[data-theme="dark"] {
  /* Canvas & Surfaces */
  --bg-canvas: #0E100D;            /* Deep black with subtle organic undertone */
  --bg-surface: #151813;           /* Base card container */
  --bg-surface-elevated: #1D211A;  /* Floating panels & modals */
  --bg-surface-subtle: #252A21;    /* Hover states & tags */
  
  /* Text & Content */
  --text-primary: #F7F9F5;          /* High-contrast readable white */
  --text-secondary: #D4D9CE;        /* Balanced body contrast */
  --text-muted: #8E9684;            /* Secondary labels */
  --text-faint: #5C6353;            /* Placeholders & disabled */
  --text-inverse: #0E100D;
  
  /* Borders & Dividers */
  --border-subtle: rgba(255, 255, 255, 0.08);
  --border-default: rgba(255, 255, 255, 0.14);
  --border-strong: #3F4738;
  
  /* Accents (Tuned for Dark Luminosity) */
  --accent-lime: #D2F898;
  --accent-lime-fg: #0E100D;
  --accent-lemon: #F6F930;
  --accent-lemon-fg: #0E100D;
  
  /* Interactive Controls */
  --btn-primary-bg: #F7F9F5;
  --btn-primary-fg: #0E100D;
  --btn-primary-hover: #DDE2D8;
  
  --btn-accent-bg: #D2F898;
  --btn-accent-fg: #0E100D;
  --btn-accent-hover: #E1FBAC;
}
```

### 3.3 Color Usage Rules
1. **60-30-10 Rule**: 60% neutral canvas/backgrounds, 30% structural ink/surfaces, and 10% high-energy lime/lemon highlights.
2. **Never Tint Body Text With Pure Accents**: Lime and lemon are strictly for high-visibility badges, focus indicators, primary interaction triggers, or active tab indicators.
3. **Contrast Discipline**: Test every combination against WCAG AA standards minimum (4.5:1 for normal text, 3:1 for large UI components).

---

## 4. Typography & Spacing System

### 4.1 Typographic Hierarchy
- **Font Stack**: Modern geometric sans with character (e.g., Geist Sans, General Sans, Satoshi, or System UI fallback).
- **Scale**:
  - `Display / H1`: 32px – 40px | Semi-bold (600) | Line-height: 1.1 | Letter-spacing: -0.02em
  - `Section / H2`: 22px – 26px | Semi-bold (600) | Line-height: 1.2 | Letter-spacing: -0.015em
  - `Subsection / H3`: 16px – 18px | Medium (500) | Line-height: 1.3 | Letter-spacing: -0.01em
  - `Body`: 14px – 15px | Regular (400) | Line-height: 1.5 | Letter-spacing: 0
  - `Small / Metadata`: 12px – 13px | Medium (500) | Line-height: 1.4 | Letter-spacing: +0.01em
  - `Code / Monospace`: 12px – 13px | JetBrains Mono / Geist Mono | Line-height: 1.4

### 4.2 Spatial Grid & Density
- Base unit: **4px**. Standard rhythm: `4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`.
- Avoid random margin/padding values (`margin-top: 17px` is forbidden).
- **Component Padding**:
  - Buttons: Compact `8px 14px`, Standard `10px 18px`, Large `12px 24px`.
  - Cards: `16px` to `24px` internal padding with `12px` or `16px` border-radius.
  - Form Inputs: `10px 14px` with clear 1.5px focus rings.

---

## 5. UI Copywriting & Voice Standards

A clean interface must sound like an honest, capable tool—never like an AI chatbot or a breathless hype deck.

### 5.1 The Anti-AI Voice Guidelines
- **Zero Hallucination / Zero AI Jargon**: Never use terms like "zero-hallucinations", "powered by next-gen neural models", or "autonomous intelligence". State what the software physically accomplishes.
- **Banned Buzzwords**:
  - ❌ *Delve, Unleash, Elevate, Supercharge, Seamless, Game-changer, Revolutionary, Magic.*
  - ✅ *Organize, Track, Review, Generate, Edit, Filter, Connect, Save.*
- **No Em-Dash Overkill**: LLMs default to dramatic em-dash constructions (`—`). Write direct, declarative sentences instead.
- **Conversational Tone, Serious Utility**: Clear, modest, and straightforward. Provide helpful context without patronizing.

### 5.2 Microcopy Best Practices
- **Buttons**: Use imperative verbs (`Export PDF`, `Save Draft`, `Copy Link`) rather than vague labels (`Submit`, `Proceed`, `Go`).
- **Empty States**: Explain what belongs here, why it matters, and provide a single one-click action to create or discover it.
- **Error Messages**: Always explain: (1) what happened, (2) why it happened, and (3) exactly how to fix it immediately. Never just output `An unexpected error occurred`.

---

## 6. Animation, Motion & Micro-Interactions

Inspired by the Emil Kowalski design philosophy and modern motion craft:

### 6.1 Principles of Motion
1. **Functional, Not Theatrical**: Animations should explain layout changes, hierarchy transitions, or state changes. Never animate solely for the sake of movement.
2. **Spring Physics Over Easing Curves**: Use physics-based springs (`stiffness`, `damping`, `mass`) rather than linear or abrupt `ease-in-out` transitions. Springs feel organic and responsive.
3. **Interruptible Transitions**: Users should be able to click, gesture, or cancel midway through any transition without the UI locking or glitching.
4. **Snappy Timings**:
   - Micro-interactions (hover, focus, toggles): `120ms` – `180ms`.
   - Modals, drawers, expandable cards: `200ms` – `300ms`.
   - Page-level or layout shifts: `250ms` – `350ms`.
   - Never exceed `400ms` for core UI responses.

### 6.2 Implementation Recipes (`motion.dev` / Framer Motion)
```tsx
// Snappy spring configuration for buttons and switches
export const springQuick = {
  type: "spring",
  stiffness: 400,
  damping: 30,
  mass: 0.8,
};

// Fluid spring for expanding panels, drawers, and modal transitions
export const springSmooth = {
  type: "spring",
  stiffness: 280,
  damping: 26,
  mass: 1,
};

// Subtle interactive tap feedback
export const tapScale = {
  whileHover: { scale: 1.015 },
  whileTap: { scale: 0.985 },
  transition: springQuick,
};
```

---

## 7. Curated UI Library Stack & Component Strategy

Do not blindly install every component library. Curate and customize to preserve a cohesive, distinct aesthetic:

| Library | Core Strength | Where to Use | Customization Rule |
|---|---|---|---|
| **Motion.dev (Framer Motion)** | Physics-based animation engine | Layout transitions, gestures, drag/drop, animated accordions, modals. | Default to springs. Avoid continuous looping animations. |
| **Motion Primitives** | Reusable atomic interactive primitives | Tooltips, morphing dialogues, animated popovers, expandable tabs. | Strip default styling; bind all colors to design tokens. |
| **React Bits** | Specialized micro-components & text motion | Counter tickers, dynamic tabs, magnetic buttons, spotlight cards. | Use sparingly for key delight moments; never crowd a single view. |
| **Aceternity UI** | High-concept visual elements | Key hero interactions, spotlight containers, dynamic borders. | Remove generic gradient text and low-contrast borders before using. |
| **Kokonut UI** | Functional SaaS components | Clean action inputs, minimal cards, modern form controls. | Perfect for structured utility interfaces; inherit app color tokens. |
| **Bklit UI / Skiper UI / Watermelon UI** | Fast building blocks & presets | Specialized badges, minimal status pills, clean card layouts. | Audit for accessibility and contrast before deployment. |

---

## 8. Skills, Standards & Reference Benchmarks

### 8.1 Active Design Skills
- **Emil Kowalski Skill (`npx skills add emilkowalski/skill`)**:
  - Focus on interaction craft, micro-delights, gestural interfaces, smooth layout animations, and spring physics.
- **Impeccable Design Skill (`https://impeccable.style`)**:
  - Uncompromising typography standards, pixel-level polish, whitespace balance, and clean visual rhythm.
- **Taste-Skill (`npx skills add Leonxlnx/taste-skill`)**:
  - Curation over accumulation; eliminating generic tropes, choosing distinctive direction, avoiding template mediocrity.
- **Vercel Web Design Guidelines (`https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines`)**:
  - Accessibility (`aria-*`, keyboard traps, focus rings, contrast), responsive design, layout shifts (CLS), semantic HTML.
- **Awesome Design.md (`https://github.com/voltagent/awesome-design-md`)**:
  - Structured, maintainable design token architectures and living documentation patterns.

### 8.2 Design Inspiration Benchmarks
- **Recent Design (`https://recent.design`)**: Modern, high-craft software aesthetics prioritizing clarity, utility, and understated elegance.
- **Godly (`https://godly.design`)**: Benchmark for premier typography, layout experimentation, fluid interactions, and high-impact digital products.

---

## 9. Frontend Readiness & Execution Gates

Before writing a single line of visual frontend code, apply this readiness gate:

### Phase 0: The "Is It Ready for Frontend?" Checklist
- [ ] **Core Logic Verified**: Are backend endpoints, data schemas, calculations, and data stores fully functional and tested?
- [ ] **Contract Integrity**: Are API responses, typing definitions, and potential edge-case states (empty, loading, error, partial) documented and mockable?
- [ ] **Workflow Clarity**: Is the step-by-step user journey completely mapped without unresolved architectural assumptions?
- [ ] **State Machine Defined**: Are asynchronous transitions, optimistic updates, and failure recoveries explicitly planned?

### Phase 1: Progressive Implementation Plan
1. **Design Tokens & Theme Providers**: Set up CSS variables for Light, Dark, and System modes with the lime/lemon/charcoal palette.
2. **Atomic Primitives**: Implement buttons, inputs, badges, and cards with high-contrast borders and spring feedback.
3. **Motion Primitives**: Configure `motion.dev` springs and shared layout animation wrappers.
4. **View Compositions**: Assemble screens with strict spacing grids, avoiding 3-icon boxes and gradient hero tropes.
5. **Human Copy Polish**: Review every label, button, toast, and tooltip against anti-AI voice rules.
6. **Accessibility & Contrast Pass**: Audit WCAG AAA contrast, keyboard navigation (`:focus-visible`), and screen reader tags.
