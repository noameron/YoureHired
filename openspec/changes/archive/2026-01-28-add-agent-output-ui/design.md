# Design: Agent Output UI

## Overview

Add a swipeable carousel UI to display research agent outputs during the drill generation loading phase. The existing drill card output remains unchanged.

## Component Architecture

```
PracticeView.vue (updated loading state)
├── AgentCarousel.vue (new)
│   ├── AgentOutputCard.vue (new) × 3
│   ├── Carousel navigation (arrows + dots)
│   └── Touch/swipe handling
├── TransitionArrow (inline, appears when research complete)
└── Drill card (existing, unchanged)
```

## Data Flow

### Current Stream Events
The backend already emits these events during drill generation:
- `status`: Progress messages
- `candidate`: When each generator completes (coding/debugging/system_design)
- `complete`: Final drill
- `error`: Failure message

### Research Agent Mapping
Map stream events to 3 research agent cards:

| Agent | Name | Triggered By |
|-------|------|--------------|
| 1 | Company Research | status messages containing "company" or "research" |
| 2 | Role Analysis | status messages containing "role" or "context" |
| 3 | Drill Generation | candidate events |

## Component Details

### AgentOutputCard.vue

Props:
```typescript
interface AgentCardProps {
  name: string
  status: 'pending' | 'running' | 'complete' | 'error'
  output: string | null
}
```

### AgentCarousel.vue

Features:
- 3 slides, one per agent
- Desktop: Arrow buttons
- Mobile: Touch swipe (50px threshold)
- Dot indicators (emerald active)
- 400ms transitions

## Styling

Uses existing design tokens: `--bg-secondary`, `--radius-2xl`, `--shadow-card`, `--accent-primary`

## Integration

Replace loading state in PracticeView with carousel + transition arrow. Drill card remains unchanged.
