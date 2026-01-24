# Tasks: Update Role Selection UI

## 1. Card Section Layout

- [ ] 1.1 Create card container component/class with rounded styling (16px radius, shadow)
- [ ] 1.2 Wrap Company Name field (label + text input + error) in card container
- [ ] 1.3 Wrap Role field (label + dropdown + error) in card container
- [ ] 1.4 Wrap Role Description field (label + textarea + char count + error) in card container
- [ ] 1.5 Apply consistent vertical spacing between cards (16-24px gap)

## 2. Input Field Styling

- [ ] 2.1 Style Company Name text input (full-width, rounded border, focus state)
- [ ] 2.2 Style Role dropdown/select (match text input style, custom arrow)
- [ ] 2.3 Style Role Description textarea (multi-line, resizable, char count display)
- [ ] 2.4 Style labels (bold, dark color, proper spacing from inputs)
- [ ] 2.5 Style error messages (red text, positioned below inputs)

## 3. Animated Background

- [ ] 3.1 Create background container with fixed positioning (z-index: -1)
- [ ] 3.2 Add inline SVG icons (keyboard, monitor, code brackets, mouse, terminal)
- [ ] 3.3 Implement orbital @keyframes animation
- [ ] 3.4 Apply staggered animation-delay to each icon
- [ ] 3.5 Set subtle opacity (10-15%) for non-distracting effect
- [ ] 3.6 Add prefers-reduced-motion media query to pause animation

## 4. Hightech Light Mode Theme

- [ ] 4.1 Update page background color to light gray (#f0f2f5)
- [ ] 4.2 Apply white background to card sections
- [ ] 4.3 Style submit button with primary accent color (#0066ff)
- [ ] 4.4 Update success message styling to match new theme
- [ ] 4.5 Update loading state styling to match new theme

## 5. Interactive States

- [ ] 5.1 Add hover effect on cards (subtle shadow increase)
- [ ] 5.2 Add focus transitions for inputs (blue border, glow)
- [ ] 5.3 Add button hover/active states
- [ ] 5.4 Ensure disabled button state is visually distinct

## 6. Validation

- [ ] 6.1 Verify Company Name validation still works (required, 2-100 chars)
- [ ] 6.2 Verify Role selection validation still works (required)
- [ ] 6.3 Verify Role Description validation still works (optional, 30-8000 chars)
- [ ] 6.4 Test form submission flow end-to-end
- [ ] 6.5 Visual review on mobile (< 768px) and desktop viewports
