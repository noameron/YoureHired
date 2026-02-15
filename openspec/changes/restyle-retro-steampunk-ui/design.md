## Context

YoureHired currently uses a modern dark-first design system with emerald accents, DM Sans font, and CSS custom property tokens. The user wants a complete visual overhaul to a retro steampunk aesthetic inspired by Cuphead (1930s cartoon style). This is a cross-cutting visual change affecting every frontend component.

## Goals / Non-Goals

**Goals:**
- Replace the entire visual identity with a cohesive retro steampunk theme
- Use CSS-only effects (no image assets or SVG illustrations needed)
- Maintain all existing functionality — this is purely a cosmetic change
- Keep the CSS custom property architecture (just replace token values)
- Maintain WCAG AA accessibility standards with new palette

**Non-Goals:**
- No character illustrations or SVG art (CSS effects only)
- No structural layout changes to components
- No new components (removing ThemeToggle is the only component change)
- No backend changes

## Decisions

### Font Selection
- **Decision**: Use Google Fonts that evoke 1930s Art Deco / vintage style
- **Display font**: `Abril Fatface` — bold Art Deco display face for headings, inspired by Cuphead title cards
- **Body font**: `Libre Baskerville` — elegant vintage serif for readable body text, evoking old newspaper/book printing
- **Mono font**: `Cutive Mono` — typewriter-style mono for code, fitting the vintage industrial aesthetic
- **Rationale**: All freely available on Google Fonts, no licensing issues, period-appropriate feel

### Color Palette
- **Decision**: Warm sepia/brass palette replacing cool dark/emerald
- **Primary background**: Aged parchment tones (`#1a1410` dark, `#2a2218` medium, `#3a3028` light)
- **Text**: Warm cream/ivory (`#e8dcc8`, `#c4b69c`, `#9a8b74`)
- **Accent**: Brass/copper (`#c4883c` primary, `#d4a04c` hover, `#a06828` pressed)
- **Borders**: Oxidized brass (`#5a4a32`, `#6a5a42`, `#4a3a22`)
- **Semantic colors**: Kept but warmed (success: patina green, warning: amber, error: rust red, info: steel blue)
- **Rationale**: Evokes Victorian-era industrial materials while maintaining sufficient contrast

### CSS Effects Strategy
- **Film grain**: CSS `background-image` using repeating noise pattern via pseudo-elements with low opacity
- **Paper texture**: Subtle CSS gradient patterns simulating aged paper fiber
- **Gear borders**: CSS `border-image` or `background` with repeating cog-tooth patterns on section dividers
- **Art Deco dividers**: CSS-drawn geometric ornaments using borders, clip-path, or pseudo-elements
- **Brass rivets**: Small circular pseudo-elements at card corners
- **Vignette**: Radial gradient overlay darkening edges (replacing current emerald ambient gradient)
- **Rationale**: Pure CSS keeps bundle small, no asset loading, easy to maintain via tokens

### Theme Toggle Removal
- **Decision**: Remove ThemeToggle component and useTheme composable entirely
- **Alternative considered**: Keep toggle as "sepia intensity" control — rejected as over-engineering
- **Migration**: Delete component files, remove from App.vue, remove localStorage theme key, remove inline theme script from index.html

## Risks / Trade-offs

- **Readability risk** → Warm sepia palette must still meet 4.5:1 contrast. Will verify all text/background combinations.
- **Font loading** → Three new Google Fonts adds ~80KB. Mitigated with `font-display: swap` and preconnect.
- **Subjective taste** → Strong aesthetic may not appeal to all users. Accepted trade-off for memorable identity.
- **Code blocks** → Cutive Mono is less information-dense than JetBrains Mono. May need slightly larger font size for code areas.

## Open Questions

- None — scope is well-defined. Purely visual, no structural changes.
