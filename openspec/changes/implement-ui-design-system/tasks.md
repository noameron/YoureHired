# Tasks: Implement UI Design System

## Task List

- [x] ### 1. Add Google Fonts and theme initialization to index.html
  - Add Google Fonts link (Inter, JetBrains Mono)
  - Add inline script to initialize theme from localStorage before render
  - **Validation**: Page loads without flash of unstyled content

- [x] ### 2. Create design tokens CSS file
  - Create `frontend/src/assets/design-tokens.css`
  - Define all color tokens for light and dark modes
  - Define spacing, radius, shadow, and typography tokens
  - **Validation**: File imports without errors

- [x] ### 3. Create base styles CSS file
  - Create `frontend/src/assets/base.css`
  - Add CSS reset and base element styles
  - Add ambient gradient background effect
  - Add utility classes for common patterns
  - **Validation**: Base styles apply correctly when imported

- [x] ### 4. Create useTheme composable
  - Create `frontend/src/composables/useTheme.ts`
  - Implement theme state with localStorage persistence
  - Implement toggleTheme function
  - Implement initTheme function
  - **Validation**: Theme toggles correctly and persists across refreshes

- [x] ### 5. Create ThemeToggle component
  - Create `frontend/src/components/ThemeToggle.vue`
  - Implement sun/moon icon toggle button
  - Style with design tokens (48px circle, emerald hover glow)
  - Add accessibility attributes (aria-label)
  - **Validation**: Toggle switches theme and shows correct icon

- [x] ### 6. Update App.vue
  - Import design-tokens.css and base.css
  - Import and mount ThemeToggle component (fixed position)
  - Initialize theme on app mount
  - **Validation**: Theme toggle visible on all pages

- [x] ### 7. Update RoleSelectionView.vue styles
  - Replace hardcoded colors with CSS variables
  - Update component styling to match design spec
  - Apply pill buttons, card styles, input styles
  - Update floating icons to use emerald accent
  - **Validation**: View matches design spec in both themes

- [x] ### 8. Update PracticeView.vue styles
  - Replace hardcoded colors with CSS variables
  - Update drill card, badges, hints accordion, code blocks
  - Apply design spec styling
  - **Validation**: View matches design spec in both themes

- [x] ### 9. Update FeedbackCard.vue styles
  - Replace hardcoded colors with CSS variables
  - Update score badges, feedback items, buttons
  - Apply design spec styling
  - **Validation**: Component matches design spec in both themes

- [x] ### 10. Final testing and polish
  - Test theme toggle on all pages
  - Verify localStorage persistence
  - Check accessibility (focus states, contrast)
  - Test reduced motion preference
  - **Validation**: All acceptance criteria met

## Dependencies

```
Task 1 ─┐
Task 2 ─┼─► Task 6 ─► Task 7 ─┐
Task 3 ─┤            Task 8 ─┼─► Task 10
Task 4 ─┤            Task 9 ─┘
Task 5 ─┘
```

Tasks 1-5 can be done in parallel. Task 6 depends on all of them. Tasks 7-9 can be done in parallel after Task 6. Task 10 is final integration testing.
