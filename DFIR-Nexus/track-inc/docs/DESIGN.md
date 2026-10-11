---
name: Evidence Narrative
colors:
  surface: '#0c1511'
  surface-dim: '#0c1511'
  surface-bright: '#313b36'
  surface-container-lowest: '#07100c'
  surface-container-low: '#141e19'
  surface-container: '#18221d'
  surface-container-high: '#222c27'
  surface-container-highest: '#2d3732'
  on-surface: '#dae5dd'
  on-surface-variant: '#c0c9bd'
  inverse-surface: '#dae5dd'
  inverse-on-surface: '#28332d'
  outline: '#8a9389'
  outline-variant: '#404940'
  surface-tint: '#94d69d'
  primary: '#94d69d'
  on-primary: '#003917'
  primary-container: '#6faf7a'
  on-primary-container: '#00411b'
  inverse-primary: '#2c6a3c'
  secondary: '#90d6a1'
  on-secondary: '#00391a'
  secondary-container: '#08552c'
  on-secondary-container: '#82c894'
  tertiary: '#9fcede'
  on-tertiary: '#003642'
  tertiary-container: '#7aa8b8'
  on-tertiary-container: '#033d4b'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#aff2b8'
  primary-fixed-dim: '#94d69d'
  on-primary-fixed: '#00210a'
  on-primary-fixed-variant: '#0f5227'
  secondary-fixed: '#abf3bb'
  secondary-fixed-dim: '#90d6a1'
  on-secondary-fixed: '#00210d'
  on-secondary-fixed-variant: '#03522a'
  tertiary-fixed: '#baeafb'
  tertiary-fixed-dim: '#9fcede'
  on-tertiary-fixed: '#001f27'
  on-tertiary-fixed-variant: '#1b4d5b'
  background: '#0c1511'
  on-background: '#dae5dd'
  surface-variant: '#2d3732'
typography:
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 42px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '500'
    lineHeight: '1.3'
  body-lg:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1'
    letterSpacing: 0.1em
  mono-data:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: '1.4'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-safe: 32px
  container-max: 1440px
  panel-gap: 16px
---

## Brand & Style
The design system is built on a "forensic documentary" aesthetic, balancing technical precision with a moody, cinematic atmosphere inspired by investigation and mystery. The target audience includes forensic analysts, investigators, and researchers who require high legibility over long periods in low-light environments.

The visual style merges **Corporate Modern** structure with **Glassmorphism** and **Tactile** overlays.
- **Atmosphere:** Deep, contemplative, and serious. It avoids high-energy neon in favor of muted, phosphorescent glows reminiscent of old CRT monitors or darkroom equipment.
- **Visual Motif:** Subtle node networks and connection lines represent the "linking of evidence." 
- **Texture:** A very fine grain (1-2% opacity noise) should be applied to primary background surfaces to prevent digital banding and add a tactile, photographic quality.
- **Effects:** Use soft "mist" gradients (linear-gradients with high transparency) in Petrol Blue and Expediente Green to suggest depth and focus without sharp directional lighting.

## Colors
The palette is deeply rooted in desaturated greens and blues to reduce eye strain and establish a professional, analytical tone.

- **Primary (Expediente Green):** Reserved for primary actions, active navigation states, and confirmed evidence.
- **Secondary (Soft Neon):** Used sparingly for hover states, success indicators, and highlights within data visualizations.
- **Tertiary (Petrol Blue):** Dedicated to contextual information, secondary data points, and "cold" case files.
- **Alert/Critical:** Both use "aged" or "dusty" variants (Amber and Documentary Red) to ensure they feel part of the environment rather than a digital overlay.
- **Surfaces:** Utilize the "Deep Greenish Black" for the base canvas, layered with "Dark Greyish Green" panels to create a hierarchy of information containers.

## Typography
Typography reflects a balance between futuristic data processing and typewriter-era documentation.

- **Headlines:** Use **Space Grotesk** for a technical, geometric feel. Keep tracking tight for a confidential, "classified" look.
- **Body & Data:** Use **JetBrains Mono** for all analytical content, logs, and evidence descriptions. The monospaced nature emphasizes the forensic, data-heavy focus of the system.
- **UI Labels:** Use **Geist** for functional elements (menus, buttons) to ensure maximum clarity and a modern developer-tool aesthetic.
- **Styling:** Use uppercase labels for metadata headers to mimic document stamps.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy on desktop to maintain the rigorous structure of a laboratory report, transitioning to a fluid model on mobile.

- **The 8px Grid:** All components and internal padding should align to an 8px base unit (referenced via the 4px micro-unit).
- **Desktop:** 12-column grid with wide margins (32px) to allow the "noise" and "mist" background effects to breathe.
- **Tablet:** 8-column grid with 24px margins.
- **Mobile:** 4-column grid with 16px margins. 
- **Investigation Map Pattern:** For background areas, use a faint 32px square grid made of 1px dotted lines in `#1B2520`. Connect specific data nodes with 1px solid lines in Petrol Blue at 30% opacity.

## Elevation & Depth
Elevation is achieved through **Tonal Layering** and **Glassmorphism** rather than traditional drop shadows.

1.  **Level 0 (Base):** Deep Greenish Black (#0B0F0D) with subtle noise.
2.  **Level 1 (Panels):** Dark Green-tinted Grey (#131A17) with a 1px "inner-glow" border (Top/Left: 10% white, Bottom/Right: 5% black).
3.  **Level 2 (Modals/Popovers):** Dark Greyish Green (#1B2520) with a `backdrop-filter: blur(12px)`. These surfaces should feel like glass slides placed over the data.
4.  **Lines:** Use "Connection Lines" (1px thickness) to bridge elements together, creating a visual map of related information.

## Shapes
The shape language is "Soft" yet disciplined. While accessibility requires some rounding, it is kept minimal to maintain a professional, high-tech instrument feel.

- **Standard Elements:** Use `rounded` (0.25rem) for input fields, buttons, and small cards.
- **Large Panels:** Use `rounded-lg` (0.5rem) for main content areas and map containers.
- **Interactive Triggers:** Use sharp 90-degree corners for "Tabs" to mimic folder dividers in a physical file.
- **Icons:** Use thin-stroke (1.5px) icons with square terminals to match the technical aesthetic.

## Components
Consistent application of the forensic aesthetic across interactive elements:

- **Buttons:** 
  - *Primary:* Solid Expediente Green with black text for maximum contrast.
  - *Ghost:* Petrol Blue border (1px) with Petrol Blue text. On hover, apply a soft outer glow (`box-shadow: 0 0 10px rgba(76, 122, 137, 0.3)`).
- **Input Fields:** Dark background (#0B0F0D) with a 1px border of #1B2520. Focus state uses a 1px primary green border and a faint "glow" pulse.
- **Chips / Tags:** Small, monospaced text in all-caps. Use Petrol Blue backgrounds for "Neutral" evidence and Aged Amber for "Flagged" items.
- **Cards:** No shadows. Use 1px borders in #1B2520 and a header section with a slightly lighter background color to distinguish the title area.
- **Node Networks:** Interactive data points should use the Secondary Color (Soft Neon Green) as small circular pulses to indicate "Live" data or active signals.
- **Lists:** Data rows should have a subtle hover state using a #1B2520 background and a 2px vertical "marker" on the left in the primary color.