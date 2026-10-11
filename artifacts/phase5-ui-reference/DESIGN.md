---
name: Indigo Intelligence
colors:
  surface: '#fcf8ff'
  surface-dim: '#dbd8e5'
  surface-bright: '#fcf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f2fe'
  surface-container: '#efecf9'
  surface-container-high: '#e9e6f3'
  surface-container-highest: '#e4e1ed'
  on-surface: '#1b1b23'
  on-surface-variant: '#464555'
  inverse-surface: '#302f39'
  inverse-on-surface: '#f2effb'
  outline: '#767586'
  outline-variant: '#c7c4d7'
  surface-tint: '#4849da'
  primary: '#4343d5'
  on-primary: '#ffffff'
  primary-container: '#5d5fef'
  on-primary-container: '#faf7ff'
  inverse-primary: '#c1c1ff'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e5e2e1'
  on-secondary-container: '#656464'
  tertiary: '#555a5f'
  on-tertiary: '#ffffff'
  tertiary-container: '#6e7278'
  on-tertiary-container: '#f5f8ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e1e0ff'
  primary-fixed-dim: '#c1c1ff'
  on-primary-fixed: '#07006c'
  on-primary-fixed-variant: '#2e2bc2'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474646'
  tertiary-fixed: '#dfe2e9'
  tertiary-fixed-dim: '#c3c7cd'
  on-tertiary-fixed: '#181c21'
  on-tertiary-fixed-variant: '#43474d'
  background: '#fcf8ff'
  on-background: '#1b1b23'
  surface-variant: '#e4e1ed'
typography:
  display-lg:
    fontFamily: Geist
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-sm:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  mono-sm:
    fontFamily: jetbrainsMono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  grid_columns: '12'
  grid_gutter: 24px
  container_padding: 32px
---

## Brand & Style

This design system is engineered for high-fidelity professional SaaS environments, specifically tailored for AI management and monitoring. The brand personality is **precise, intelligent, and reliable**, striking a balance between cutting-edge technology and enterprise-grade stability.

The design style follows a **Modern Corporate** aesthetic with a strong emphasis on **Information Density and Clarity**. It utilizes a systematic approach to layering and whitespace to ensure that complex data—such as call logs, state machine traces, and real-time analytics—remains legible and non-overwhelming. The interface prioritizes high-contrast typography and a restrained but functional color palette to guide user attention toward critical system statuses and agent performance metrics.

## Colors

The palette is anchored by a deep **Indigo (#5D5FEF)**, used strategically for primary actions and brand presence. The interface relies on a "Cool Gray" neutral scale to maintain a clean, clinical feel that doesn't fatigue the eyes during long periods of monitoring.

### Functional Color Usage:
- **Primary:** Used for main buttons, active navigation states, and key data points.
- **Success/Pending/Error:** Reserved strictly for status indicators (e.g., call outcomes, test results). These should be used with a 10% opacity background of the same hue when used in chips or tags to ensure high legibility.
- **Surface Tones:** Pure white (#FFFFFF) is used for cards and workspace areas, while the background uses a subtle off-white (#F9FAFB) to create a clear container hierarchy.

## Typography

This system uses a dual-font approach. **Geist** is utilized for headlines and labels to provide a sharp, technical, and modern feel. **Inter** is used for all body text and data-heavy tables due to its exceptional legibility and neutral character.

For technical data—such as API traces or phone numbers—**JetBrains Mono** is recommended to ensure character distinction. Large headlines (Display-LG and Headline-LG) should scale down by 20% on mobile devices to prevent layout breaking. Use `label-lg` specifically for section headers and sidebar category titles to create a strong vertical rhythm.

## Layout & Spacing

The layout follows a **Fixed-Fluid Hybrid** model. The sidebar remains at a fixed width (260px) while the main content area utilizes a 12-column fluid grid. 

### Spacing Philosophy:
- **Generous Padding:** All container cards must have at least `lg` (24px) internal padding to maintain a premium, airy feel.
- **Rhythm:** Use a 4px base unit. Component heights should always be multiples of 8.
- **Breakpoints:**
  - **Desktop (1280px+):** Full 12-column grid, persistent sidebar.
  - **Tablet (768px - 1279px):** 8-column grid, collapsible sidebar.
  - **Mobile (< 767px):** 4-column grid, bottom-sheet navigation or hamburger menu, vertical stack for all cards.

## Elevation & Depth

Visual hierarchy is established using **Tonal Layers** combined with **Ambient Shadows**.

1.  **Level 0 (Background):** The base canvas (`#F9FAFB`).
2.  **Level 1 (Cards/Surface):** Pure white elements. These use a very soft, diffused shadow: `0px 4px 20px rgba(0, 0, 0, 0.03)`.
3.  **Level 2 (Overlays/Popovers):** Active menus and dropdowns. These use a slightly more defined shadow: `0px 10px 32px rgba(0, 0, 0, 0.08)` and a 1px border (`#E5E7EB`).
4.  **Active State:** Use a 2px Indigo border to indicate focus or active selection, rather than increasing shadow depth.

Avoid heavy black shadows; instead, use shadows tinted with the primary color at extremely low opacity (2-3%) to maintain a clean "Dashboard" look.

## Shapes

The design uses a **Rounded** shape language to soften the technical nature of the AI system and make it feel more approachable.

- **Standard Elements:** Buttons, Input fields, and small UI elements use `0.5rem` (8px).
- **Large Containers:** Dashboard cards, modals, and sidebar containers use `rounded-lg` (16px).
- **Interactive Feedback:** Focus states should follow the container's radius exactly.
- **Status Chips:** Use `pill-shaped` (full radius) to distinguish them from interactive buttons.

## Components

### Buttons
- **Primary:** Solid Indigo (#5D5FEF) with white text. High emphasis.
- **Secondary:** White background with Indigo border and text. 
- **Ghost:** No border, Indigo text. Used for less frequent actions.

### Status Indicators (Chips)
- **Structure:** 12px font size, 500 weight, 4px vertical / 12px horizontal padding.
- **Styles:** 
  - *Success:* Emerald green text on 10% green background.
  - *Pending:* Amber orange text on 10% orange background.
  - *Error:* Rose red text on 10% red background.

### Input Fields
- Heights should be standardized at 44px for desktop.
- 1px border (#E5E7EB) that transitions to 2px Indigo on focus.
- Placeholder text in `neutral.text_secondary`.

### Cards
- Always use the `rounded-lg` (16px) radius.
- Must include a subtle title section with `label-lg` typography.
- Background is always white (#FFFFFF) to pop against the light gray layout background.

### Data Tables
- Use `body-sm` for row content.
- Headers should be `label-md` with a light gray background (#F4F7FE) and a subtle bottom border.
- Row hover states should use a very faint gray (#F9FAFB) to assist tracking.