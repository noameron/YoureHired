# Change: Update role selection page with minimal hightech UI and animated background

## Why

The current RoleSelectionView has basic styling. Users need a modern, clean, "hightech vibe" interface with distinct rounded sections for each form field, plus an animated background with floating tech icons to create an engaging visual experience.

## What Changes

- Redesign RoleSelectionView.vue with minimal hightech light mode aesthetic
- Implement 3 distinct rounded card sections (top to bottom)
- Add animated background with floating tech SVG icons in orbital/circular motion
- Apply subtle visual effects (shadows, borders, transitions) for depth
- Maintain all existing functionality and validation logic

## User Input Sections

Each section is a rounded card with its own label, input field, and validation feedback.

### Section 1: Company Name (Top)
- **Label**: "Company Name"
- **Input**: Text input field
- **Placeholder**: "Enter company name"
- **Validation**: Required, 2-100 characters
- **Style**: Rounded card container, text input with subtle border

### Section 2: Role (Middle)
- **Label**: "Role"
- **Input**: Dropdown/select with fixed options from backend
- **Placeholder**: "Select a role"
- **Options**: Frontend Developer, Backend Developer, etc. (fetched from API)
- **Validation**: Required selection
- **Style**: Rounded card container, styled select dropdown

### Section 3: Role Description (Bottom)
- **Label**: "Role Description (Optional)"
- **Input**: Textarea for custom description
- **Placeholder**: "Describe your target role or specific areas you want to practice..."
- **Validation**: Optional, 30-8000 characters if provided
- **Style**: Rounded card container, multi-line textarea with character count

### Submit Button
- Full-width button below the cards
- Label: "Start Practice"
- Disabled state while submitting

## Animated Background

- Floating tech SVG icons (keyboard, monitor, code brackets, mouse, terminal)
- Icons move in orbital/circular paths
- Low opacity (10-15%) so form content remains focus
- Respects prefers-reduced-motion

## Impact

- Affected specs: role-selection (UI portion only - no API changes)
- Affected code: `frontend/src/views/RoleSelectionView.vue` (styling, template, animated background)
- No backend changes required
- No breaking changes to existing functionality
