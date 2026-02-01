---
name: client-code-simplifier
description: "Client code simplification for Vue 3 + TypeScript + Vite + Pinia stack. Use when user asks to 'simplify frontend code', 'clean up Vue components', 'extract inline styles/SVGs/types', 'reduce component size', or 'prepare frontend for review'. Enforces lean components, proper extraction, and production-ready structure."
---

# Client Code Simplification

**Stack:** Vue 3 | TypeScript | Vite | Pinia | npm

**Goal:** Lean, focused components. Extract everything that doesn't belong inline.

## Size Limits

| Element | Max | Severity |
|---------|-----|----------|
| `<template>` | 100 | 🟠 High |
| `<script setup>` (excl. imports) | 80 | 🟠 High |
| `<style scoped>` | 50 | 🟡 Medium |
| **Total .vue file** | 250 | 🔴 Critical |
| Single function | 20 | 🟡 Medium |
| Single computed | 10 | 🟢 Low |

## Extraction Rules

### 1. Inline SVGs → Icon Components
**Detect:** `<svg>` in template | **Severity:** 🟠 High

Extract to `src/components/icons/IconName.vue` or use unplugin-icons.

### 2. Inline Assets → Asset Files
**Detect:** Base64 URLs, hardcoded paths | **Severity:** 🟡 Medium

Extract to `src/assets/images/`, import via Vite.

### 3. Large Styles → External CSS
**Detect:** `<style scoped>` > 50 lines | **Severity:** 🟡/🟠

Extract to `ComponentName.styles.css`, import via `<style scoped src="./ComponentName.styles.css">`.

Also extract: `@keyframes` → `src/assets/styles/animations.css`

### 4. Inline Types → Type Files
**Detect:** `ref<{...}>`, interfaces in script | **Severity:** 🟡 Medium

Extract to `ComponentName.types.ts` or `src/types/`.

### 5. Constants → Constant Files
**Detect:** `const UPPER_CASE`, magic numbers | **Severity:** 🟢/🟡

Extract to `src/constants/validation.ts`, `ui.ts`, `api.ts`.

### 6. Validation Logic → Utils
**Detect:** `validate()` > 15 lines | **Severity:** 🟡 Medium

Extract to `src/utils/formValidation.ts` or `ComponentName.utils.ts`.

### 7. Complex Logic → Composables
**Detect:** Async handlers > 20 lines, 3+ related refs | **Severity:** 🟠 High

Extract to `src/composables/useFeatureName.ts`.

### 8. API Calls → Services
**Detect:** `fetch()`/axios in component | **Severity:** 🟠 High

Extract to `src/services/api.ts` or domain-specific service.

### 9. Global State → Pinia Stores
**Detect:** State passed through many props | **Severity:** 🟡 Medium

Extract to `src/stores/`.

### 10. Large Templates → Child Components
**Detect:** Template > 100 lines, deep nesting (4+) | **Severity:** 🟠/🔴

Extract sections to `components/SectionName.vue`.

## Anti-Patterns

**Template:** Inline SVGs, inline `style=""`, complex ternaries, nested v-if (4+)

**Script:** API calls, business logic in handlers, console.log, unused imports

**Style:** `!important` overuse, deep nesting (3+), hardcoded colors

## Analysis Commands

```bash
# Line counts
awk '/<template>/,/<\/template>/' f.vue | wc -l
awk '/<script/,/<\/script>/' f.vue | wc -l
awk '/<style/,/<\/style>/' f.vue | wc -l

# Find violations
grep -rln "<svg" frontend/src/                # Inline SVGs
grep -rEn "ref<\{|reactive<\{" frontend/src/  # Inline types
grep -En "const [A-Z][A-Z_]+ =" frontend/src/ # Constants
```

## Output Format

```
### Client Analysis: `ComponentName.vue`

**Template:** XX | **Script:** XX | **Style:** XX | **Total:** XX

| # | Sev | Rule | Location | Issue |
|---|-----|------|----------|-------|
| 1 | 🔴 | Size | - | Total 320 lines |
| 2 | 🟠 | SVG | L45-90 | 4 inline SVGs |

**Extraction plan:**
1. Create `src/components/icons/` with 4 icons
2. Extract styles to `ComponentName.styles.css`
```

## File Organization

```
Simple:     Component.vue
Medium:     Component.vue + Component.types.ts + Component.styles.css
Complex:    Feature/
            ├── Feature.vue
            ├── Feature.types.ts
            ├── Feature.styles.css
            ├── Feature.utils.ts
            ├── components/
            └── index.ts
```
