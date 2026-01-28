# Proposal: Add Agent Output UI

## Summary

Add a swipeable carousel for displaying real-time output from 3 research agents during drill generation, with an animated transition arrow leading to the existing drill output.

## Motivation

After pressing "Start Practice", users currently see minimal feedback during the research phase. This proposal adds visual feedback for the research agents while keeping the existing drill output unchanged.

1. **Transparency**: Shows what each research agent is doing in real-time
2. **Engagement**: Keeps users engaged during research with visual progress
3. **Mobile-First**: Swipeable carousel optimized for touch devices

## Scope

### In Scope

- `AgentOutputCard.vue` component for individual agent status/output
- `AgentCarousel.vue` component with swipe support and dot navigation
- Animated transition arrow between research and drill sections
- Loading states (spinner → content) per agent
- Match existing design system (dark theme, emerald accents, rounded corners)

### Out of Scope

- Changes to drill output display (stays as-is)
- Backend changes
- New API endpoints

## Approach

1. **New Components**:
   - `AgentOutputCard.vue`: Displays agent name, status indicator, and output content
   - `AgentCarousel.vue`: Swipeable container with 3 slides, arrow buttons, dot indicators

2. **View Integration**: Insert carousel + arrow above existing drill output in `PracticeView.vue`

3. **Swipe Support**: Use native touch events for mobile - no external library

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Carousel library | Native touch events | Zero dependencies, matches project simplicity |
| Drill output | Keep unchanged | User requirement |
| Arrow behavior | Appears when research completes | Visual transition cue |

## Success Criteria

- Swipeable carousel works on mobile (touch) and desktop (arrow buttons)
- Smooth transitions between slides (400ms ease-out)
- Loading → content transition for each agent independently
- Arrow appears with bounce animation when all research completes
- Existing drill output remains unchanged below the arrow
