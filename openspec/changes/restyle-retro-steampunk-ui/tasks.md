## 1. Remove Theme Toggle Infrastructure
- [ ] 1.1 Delete `frontend/src/components/ThemeToggle.vue` and `ThemeToggle.styles.css`
- [ ] 1.2 Delete `frontend/src/composables/useTheme.ts`
- [ ] 1.3 Remove ThemeToggle import and usage from `frontend/src/App.vue`
- [ ] 1.4 Remove inline theme initialization `<script>` from `frontend/index.html`
- [ ] 1.5 Remove `data-theme` attribute logic from `<html>` element
- [ ] 1.6 Run frontend tests — verify no regressions from removal

## 2. Replace Font Imports
- [ ] 2.1 Replace Google Fonts link in `frontend/index.html` — swap DM Sans for Abril Fatface + Libre Baskerville + Cutive Mono
- [ ] 2.2 Add proper `font-display: swap` and preconnect hints for new fonts

## 3. Replace Design Tokens
- [ ] 3.1 Replace color tokens in `frontend/src/assets/design-tokens.css` — remove `[data-theme]` selectors, define single steampunk palette on `:root`
- [ ] 3.2 Replace typography tokens — update font family, size, weight, and line-height variables for vintage style
- [ ] 3.3 Replace shadow tokens — warm-toned shadows replacing cool/emerald glows
- [ ] 3.4 Replace border tokens — oxidized brass border colors and radius values
- [ ] 3.5 Replace gradient tokens — brass/copper button gradients replacing emerald
- [ ] 3.6 Add new decorative effect tokens (grain opacity, vignette strength, rivet size)
- [ ] 3.7 Verify all color combinations meet WCAG AA 4.5:1 contrast ratio

## 4. Update Global Styles
- [ ] 4.1 Update `frontend/src/assets/base.css` — replace ambient gradient with vignette + paper texture
- [ ] 4.2 Add film grain overlay pseudo-element with animated noise pattern
- [ ] 4.3 Add Art Deco divider styles for `<hr>` and section separators
- [ ] 4.4 Add gear/cog decorative background patterns via CSS
- [ ] 4.5 Update button base styles — brass gradients, embossed edges, warm glow on hover
- [ ] 4.6 Update input/form styles — recessed/engraved effect with brass focus ring
- [ ] 4.7 Update focus ring styles — brass-colored outline with warm glow
- [ ] 4.8 Add `@media (prefers-reduced-motion)` rules for new animations (grain, decorative effects)

## 5. Update Component Styles
- [ ] 5.1 Update `DrillCard.styles.css` — aged parchment card with brass rivets and warm badges
- [ ] 5.2 Update `FeedbackCard.styles.css` — vintage score display with brass accents
- [ ] 5.3 Update `AgentFlowchart.styles.css` — steampunk pipeline visualization
- [ ] 5.4 Update `AgentOutputCard.styles.css` — vintage terminal/ticker-tape feel

## 6. Update View Styles
- [ ] 6.1 Update `RoleSelectionView.styles.css` — steampunk role selection with ornamental layout
- [ ] 6.2 Update `PracticeView.styles.css` — vintage practice workspace

## 7. Validation
- [ ] 7.1 Visual review — all pages render with cohesive steampunk aesthetic
- [ ] 7.2 Accessibility audit — contrast ratios verified, focus states visible, reduced motion works
- [ ] 7.3 Run full frontend test suite
- [ ] 7.4 Run frontend build — no CSS errors or warnings
