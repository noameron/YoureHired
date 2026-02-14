# Change: Restyle UI to Retro Steampunk Aesthetic

## Why

The current modern dark-mode UI is functional but generic. A distinctive retro steampunk visual identity — inspired by Cuphead's 1930s cartoon art direction — will make YoureHired immediately recognizable and memorable, reinforcing the "challenge accepted" spirit of coding practice with bold, playful vintage flair.

## What Changes

- **BREAKING**: Remove dark/light theme toggle — replaced by a single unified retro steampunk theme
- Replace entire color palette with warm vintage tones (sepia, brass, copper, aged parchment)
- Replace DM Sans / JetBrains Mono fonts with 1930s Art Deco display font + vintage serif body text + period-appropriate monospace
- Add CSS-only decorative effects: film grain overlay, paper texture, gear/cog borders, Art Deco dividers, brass rivet accents
- Restyle all UI components (buttons, cards, inputs, badges) to match steampunk aesthetic
- Replace ambient emerald gradient background with aged parchment texture and vintage vignette

## Impact

- Affected specs: `design-system`, `theme-toggle`
- Affected code:
  - `frontend/src/assets/design-tokens.css` — full token replacement
  - `frontend/src/assets/base.css` — global styles, animations, textures
  - `frontend/index.html` — font imports, remove theme init script
  - `frontend/src/App.vue` — remove theme-related imports
  - `frontend/src/components/ThemeToggle.vue` + `.styles.css` — remove entirely
  - `frontend/src/composables/useTheme.ts` — remove entirely
  - All component `.styles.css` files — adapt to new tokens
  - All view `.styles.css` files — adapt to new tokens
