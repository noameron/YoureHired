# Design: UI Design System Implementation

## Architecture Overview

```
frontend/
├── index.html                    # Google Fonts link + theme init script
├── src/
│   ├── assets/
│   │   ├── design-tokens.css     # CSS variables for both themes
│   │   └── base.css              # Global styles, resets, ambient effects
│   ├── components/
│   │   └── ThemeToggle.vue       # Theme toggle button component
│   ├── composables/
│   │   └── useTheme.ts           # Theme state management composable
│   ├── App.vue                   # Mounts ThemeToggle, imports global CSS
│   └── views/
│       ├── RoleSelectionView.vue # Updated with design tokens
│       └── PracticeView.vue      # Updated with design tokens
```

## Theme System Design

### CSS Custom Properties Structure

```css
:root {
  /* Light mode values (fallback) */
  --bg-primary: #F3F4F6;
  --text-primary: #111827;
  /* ... */
}

[data-theme="dark"] {
  /* Dark mode values (default) */
  --bg-primary: #09090B;
  --text-primary: #FAFAFA;
  /* ... */
}
```

### Theme Toggle Flow

```
1. Page Load
   ├─ Check localStorage for 'theme' key
   ├─ If exists → apply that theme
   └─ If not → default to 'dark'

2. User Clicks Toggle
   ├─ Toggle theme value
   ├─ Update document.documentElement.dataset.theme
   └─ Save to localStorage

3. Component renders sun/moon icon based on current theme
```

### Theme Composable API

```typescript
// useTheme.ts
export function useTheme() {
  const theme = ref<'light' | 'dark'>('dark')

  function initTheme(): void { /* ... */ }
  function toggleTheme(): void { /* ... */ }

  return { theme, toggleTheme, initTheme }
}
```

## Component Design

### ThemeToggle.vue

- **Position**: Fixed, top-right corner (16px from edges)
- **Size**: 48px circle
- **Behavior**: Click to toggle, hover effects with emerald glow
- **Icons**: Sun (light mode) / Moon (dark mode)
- **Z-index**: High enough to overlay all content

### Design Token Categories

| Category | Examples |
|----------|----------|
| Colors - Background | `--bg-primary`, `--bg-secondary`, `--bg-tertiary`, `--bg-hover` |
| Colors - Text | `--text-primary`, `--text-secondary`, `--text-tertiary` |
| Colors - Border | `--border-primary`, `--border-secondary`, `--border-subtle` |
| Colors - Accent | `--accent-primary`, `--accent-hover`, `--accent-light` |
| Colors - Semantic | `--color-success`, `--color-warning`, `--color-error` |
| Spacing | `--space-1` through `--space-16` |
| Radius | `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-2xl`, `--radius-full` |
| Shadows | `--shadow-sm`, `--shadow-md`, `--shadow-lg`, `--shadow-glow`, `--shadow-card` |
| Typography | `--font-sans`, `--font-mono`, font-size scale |

## Flash Prevention

To prevent flash of wrong theme on page load, add inline script in `<head>`:

```html
<script>
  (function() {
    const theme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
```

## Accessibility Considerations

1. **Focus States**: All interactive elements get `--accent-light` ring on focus
2. **Reduced Motion**: Respect `prefers-reduced-motion` for animations
3. **Contrast**: All color combinations meet WCAG AA (4.5:1 for text)
4. **Touch Targets**: Minimum 44px for all interactive elements
5. **Theme Toggle**: Has aria-label describing current state and action
