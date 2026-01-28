# Proposal: Implement UI Design System

## Summary

Implement a comprehensive UI design system for YoureHired with a dark-first, developer-focused aesthetic featuring emerald green accents, rounded corners, and subtle glow effects. Includes a **light/dark theme toggle on every page** allowing users to switch themes.

## Motivation

The current UI uses a basic light theme with blue accents and minimal design tokens. This proposal establishes:

1. **Brand Identity**: Dark, sophisticated aesthetic that appeals to developers
2. **Theme Toggle**: Persistent light/dark toggle accessible on every page
3. **Design Consistency**: Centralized CSS variables for colors, spacing, typography, and shadows
4. **Component Standards**: Consistent styling for buttons, inputs, cards, badges, and interactive elements
5. **Improved UX**: Subtle animations, glow effects, and hover states

## Scope

### In Scope

- CSS design tokens (variables) for colors, spacing, typography, shadows, and radii
- **Theme toggle component visible on top of every page** (positioned top-right corner)
- Dark mode as default with light mode support via `data-theme` attribute
- Theme preference persisted in localStorage
- Global stylesheet with base styles and component classes
- Updated styling for all existing views (RoleSelectionView, PracticeView)
- Updated styling for FeedbackCard component
- Google Fonts integration (Inter, JetBrains Mono)
- Ambient gradient background effect
- Accessibility considerations (focus states, reduced motion, WCAG contrast)

### Out of Scope

- New functional features or views
- Backend changes
- Additional components beyond current needs

## Approach

1. **Global CSS Variables**: Define all design tokens in `frontend/src/assets/design-tokens.css`
2. **Base Styles**: Create `frontend/src/assets/base.css` for resets, typography, and ambient effects
3. **Theme Toggle**: Add `ThemeToggle.vue` component in App.vue (visible on all pages)
4. **Component Styles**: Update scoped styles in Vue components to use design tokens
5. **Font Loading**: Add Google Fonts link in `index.html`

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Toggle position | Fixed top-right on every page | Always accessible regardless of scroll position |
| Token approach | CSS custom properties | Native browser support, runtime theme switching |
| Theme storage | localStorage + `data-theme` attribute | Persists preference across sessions |
| Default theme | Dark | Matches design spec's "dark-first" direction |
| Font loading | Google Fonts CDN | Simplicity, caching benefits |

## Success Criteria

- Theme toggle visible and functional on all pages
- Theme preference persists across page refreshes and sessions
- All views render correctly in both dark and light modes
- Design matches specification colors, spacing, and component styles
