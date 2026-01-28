# Tasks: Agent Output UI

## Implementation Order

### 1. Create AgentOutputCard component
- [x] Create `frontend/src/components/AgentOutputCard.vue`
- [x] Props: name, status, output
- [x] States: pending (gray), running (spinner), complete (checkmark), error (red)
- [x] Use design tokens for styling

### 2. Create AgentCarousel component
- [x] Create `frontend/src/components/AgentCarousel.vue`
- [x] Implement slide container with CSS transform transitions
- [x] Add left/right arrow buttons for desktop
- [x] Add dot indicators with active state
- [x] Implement touch swipe handling (touchstart/touchmove/touchend)
- [x] 50px swipe threshold, 400ms transition

### 3. Update PracticeView loading state
- [x] Import AgentCarousel component
- [x] Add researchAgents ref with 3 agent objects
- [x] Map stream events to agent status updates
- [x] Replace current loading UI with AgentCarousel
- [x] Add transition arrow (appears when all agents complete)
- [x] Keep drill card output unchanged

### 4. Add transition arrow styling
- [x] 48px circular button with emerald border
- [x] Chevron down icon
- [x] Bounce animation (2s infinite)
- [x] Fade-in when all research complete

## Dependencies

- Task 1 must complete before Task 3 ✓
- Task 2 must complete before Task 3 ✓
- Tasks 1 and 2 can be done in parallel ✓
