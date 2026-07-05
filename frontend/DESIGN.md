---
name: NeuroSense AI
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#44474e'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#74777f'
  outline-variant: '#c4c6cf'
  surface-tint: '#4c5f81'
  primary: '#000513'
  on-primary: '#ffffff'
  primary-container: '#071e3d'
  on-primary-container: '#7387ab'
  inverse-primary: '#b3c7ef'
  secondary: '#0051d5'
  on-secondary: '#ffffff'
  secondary-container: '#316bf3'
  on-secondary-container: '#fefcff'
  tertiary: '#000608'
  on-tertiary: '#ffffff'
  tertiary-container: '#002229'
  on-tertiary-container: '#0093ab'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d6e3ff'
  primary-fixed-dim: '#b3c7ef'
  on-primary-fixed: '#041b3a'
  on-primary-fixed-variant: '#344768'
  secondary-fixed: '#dbe1ff'
  secondary-fixed-dim: '#b4c5ff'
  on-secondary-fixed: '#00174b'
  on-secondary-fixed-variant: '#003ea8'
  tertiary-fixed: '#acedff'
  tertiary-fixed-dim: '#4cd7f6'
  on-tertiary-fixed: '#001f26'
  on-tertiary-fixed-variant: '#004e5c'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-xl:
    fontFamily: Inter
    fontSize: 64px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.04em
  headline-lg:
    fontFamily: Inter
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.2'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 24px
  lg: 40px
  xl: 64px
  container-max: 1440px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style
The design system for this healthcare AI application is built upon a foundation of **precision, clarity, and trust**. It synthesizes the iterative speed of developer-centric tools with the polished, human-centric accessibility of high-end consumer hardware. 

The aesthetic is **Modern Minimalist with Glassmorphic accents**, characterized by:
- **Atmospheric Depth:** Using translucency and blurred background layers to maintain context during complex medical data analysis.
- **Scientific Precision:** High-contrast typography and a structured grid that evokes a sense of medical reliability.
- **Human-Centric Softness:** Large corner radii and generous whitespace to reduce cognitive load for clinicians and researchers.

## Colors
The palette is anchored in **Deep Navy**, providing a sense of institutional authority and depth. **Medical Blue** and **Cyan** serve as functional accents for interactivity and data visualization, representing the "intelligence" layer of the AI.

- **Primary (Deep Navy):** Used for sidebars, primary text, and deep-state containers.
- **Secondary (Medical Blue):** Reserved for primary actions and focused states.
- **Tertiary (Cyan):** Used for AI-generated insights, active scanning indicators, and highlights.
- **Surface (Slate/Gray):** A range of cool grays (from #F8FAFC to #E2E8F0) creates soft layering without the harshness of pure white.

## Typography
The system utilizes **Inter** for its exceptional legibility in data-dense environments. Large headings utilize **tight letter-spacing** to create a modern, "editorial" feel common in premium tech brands. 

For technical metadata and labels, **Geist** is employed to provide a slight monospaced, technical rhythm that distinguishes AI-generated values from human-readable body text.

## Layout & Spacing
The layout follows a **Fluid Grid** model with a maximum container width to ensure readability on ultra-wide monitors. 

- **Grid:** A 12-column system for desktop, 8-column for tablet, and 4-column for mobile.
- **Rhythm:** An 8px base unit governs all dimensions.
- **Whitespace:** Generous padding (40px+) is used between major sections to prevent the UI from feeling "crowded," which is critical in high-stress medical environments.

## Elevation & Depth
This design system avoids heavy drop shadows in favor of **Tonal Layering and Glassmorphism**.

1.  **Level 0 (Background):** Solid Slate #F8FAFC.
2.  **Level 1 (Cards):** Pure White surface with a 1px border (#E2E8F0) and a very soft, diffused shadow (0px 4px 20px rgba(0,0,0,0.03)).
3.  **Level 2 (Glass Overlays):** Translucent White (80% opacity) with a 20px backdrop-blur. Used for navigation bars and floating action panels.
4.  **Level 3 (Modals):** High-contrast White surface with a deep, wide-spread shadow to pull focus.

## Shapes
The shape language is defined by **significant roundness**. Standard components use 0.5rem (8px), while primary containers and cards use **2xl** (1.5rem / 24px) to create the signature "soft-tech" appearance. 

Interactive elements like buttons should maintain a consistent corner radius of 12px (rounded-lg) to bridge the gap between the soft containers and sharp text.

## Components
- **Buttons:** Primary buttons feature a subtle linear gradient from **Medical Blue** to a slightly darker shade. Secondary buttons are "ghost" style with a 1px border and high-blur hover states.
- **Glass Cards:** Used for dashboard widgets. They feature a `backdrop-filter: blur(12px)` and a thin, semi-transparent white border to catch light.
- **Sleek Timelines:** Vertical lines should be 2px thick in light gray, with active nodes glowing in **Cyan**.
- **Data Visualizations:** Use a limited color palette of Cyan, Blue, and Navy. Chart lines should be anti-aliased and slightly thick (3px) with soft-area fills.
- **Inputs:** Fields are minimal, using a light gray fill and transitioning to a Cyan border glow on focus. 
- **Chips:** Small, pill-shaped labels with low-opacity background tints (e.g., Success green at 10% opacity) for categorizing patient data or AI confidence levels.