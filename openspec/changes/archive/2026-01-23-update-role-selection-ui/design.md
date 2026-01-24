## Context

The role selection page needs a visual redesign with a "hightech vibe" featuring:
- Light mode color scheme
- Three rounded card sections for form fields
- Animated background with floating tech icons in orbital motion

This is a frontend-only change affecting `RoleSelectionView.vue`.

## Goals / Non-Goals

**Goals:**
- Create visually engaging hightech aesthetic with light mode
- Present Company Name, Role, and Role Description in distinct rounded cards
- Implement floating tech icons with orbital animation
- Maintain all existing form functionality

**Non-Goals:**
- No JavaScript animation libraries (keep it pure CSS)
- No external icon libraries or CDN dependencies
- No changes to form validation or API integration

## User Input Sections Design

### Layout Structure
```
┌─────────────────────────────────────────┐
│         [Animated Background]           │
│  ┌───────────────────────────────────┐  │
│  │  Section 1: Company Name          │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ [Text Input]                │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Section 2: Role                  │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ [Dropdown Select]     ▼     │  │  │
│  │  └─────────────────────────────┘  │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │  Section 3: Role Description      │  │
│  │  ┌─────────────────────────────┐  │  │
│  │  │ [Textarea                   │  │  │
│  │  │  Multi-line input]          │  │  │
│  │  └─────────────────────────────┘  │  │
│  │                     0 / 8000      │  │
│  └───────────────────────────────────┘  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │         Start Practice            │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### Section 1: Company Name Card
- **Card**: White background, 16px border-radius, subtle shadow
- **Label**: "Company Name" - bold, dark text
- **Input**: Full-width text input
  - Placeholder: "Enter company name"
  - Border: 1px solid light gray, rounds to 8px
  - Focus: Blue border highlight
- **Error**: Red text below input when validation fails

### Section 2: Role Card
- **Card**: Same styling as Section 1
- **Label**: "Role" - bold, dark text
- **Select**: Full-width dropdown
  - Default: "Select a role" (disabled option)
  - Options: Fetched from `/api/roles`
  - Styled to match text inputs
- **Error**: Red text below select when validation fails

### Section 3: Role Description Card
- **Card**: Same styling as Section 1
- **Label**: "Role Description (Optional)" - bold, dark text
- **Textarea**: Full-width, 4 rows minimum
  - Placeholder: "Describe your target role..."
  - Resizable vertically
- **Character count**: Right-aligned, gray text "0 / 8000"
- **Error**: Red text when over limit or under minimum

### Submit Button
- Full-width, below cards
- Primary accent color (tech blue)
- Rounded corners (12px)
- Hover: Slightly darker
- Disabled: Gray, no cursor

## Animated Background Design

### Decision: Use pure CSS @keyframes for orbital animation
- **Why**: No external dependencies, performant, easy to maintain

### Decision: Inline SVG icons for floating elements
- **Why**: No additional HTTP requests, full CSS styling control

### Decision: 5-7 floating icons with staggered animation delays
- **Why**: Enough visual interest without overwhelming

### Background Structure
```
.background-animation (fixed, full viewport, z-index: -1)
├── .floating-icon.icon-1 (keyboard SVG)
├── .floating-icon.icon-2 (monitor SVG)
├── .floating-icon.icon-3 (code brackets SVG)
├── .floating-icon.icon-4 (mouse SVG)
├── .floating-icon.icon-5 (terminal SVG)
└── ... varied delays and orbit radii
```

### CSS Animation Pattern
```css
@keyframes orbit {
  0% { transform: rotate(0deg) translateX(150px) rotate(0deg); }
  100% { transform: rotate(360deg) translateX(150px) rotate(-360deg); }
}

.floating-icon {
  position: absolute;
  animation: orbit 20s linear infinite;
  opacity: 0.12;
}
```

## Color Palette (Light Mode Hightech)

| Element | Color | Usage |
|---------|-------|-------|
| Page background | `#f0f2f5` | Light gray base |
| Card background | `#ffffff` | White cards |
| Primary accent | `#0066ff` | Button, focus states |
| Text primary | `#1a1a2e` | Labels, content |
| Text secondary | `#6c757d` | Placeholders, hints |
| Border | `#e0e0e0` | Input borders |
| Error | `#dc3545` | Validation errors |
| Icon fill | `#0066ff` | At 12% opacity |

## Risks / Trade-offs

- **Risk**: Animation performance on low-end devices
  - **Mitigation**: Use `transform` only (GPU-accelerated), limit icons, add `prefers-reduced-motion`

- **Trade-off**: Inline SVGs increase component size (~2-3KB)
  - **Acceptable**: Keeps component self-contained

## Open Questions

None - design is straightforward frontend styling work.
