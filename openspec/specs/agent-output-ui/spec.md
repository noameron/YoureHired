# agent-output-ui Specification

## Purpose
TBD - created by archiving change add-agent-output-ui. Update Purpose after archive.
## Requirements
### Requirement: Agent Output Card Component

The system SHALL provide an AgentOutputCard component displaying individual agent status.

Props:
- `name` (string): Agent display name
- `status` (enum): 'pending' | 'running' | 'complete' | 'error'
- `output` (string, optional): Content to display when complete

Visual states:
- pending: Grayed out with "Waiting..." text
- running: Spinner animation with "Researching..." text
- complete: Green checkmark icon with output content
- error: Red X icon with error message

#### Scenario: Agent in pending state
- **WHEN** status is 'pending'
- **THEN** card displays grayed styling with "Waiting..." text

#### Scenario: Agent in running state
- **WHEN** status is 'running'
- **THEN** card displays spinner animation with "Researching..." text

#### Scenario: Agent completes successfully
- **WHEN** status is 'complete' and output is provided
- **THEN** card displays green checkmark and output content

---

### Requirement: Agent Carousel Component

The system SHALL provide an AgentCarousel component with swipeable slides.

Features:
- Displays 3 agent cards as slides
- Arrow buttons for desktop navigation (left/right)
- Dot indicators showing current slide (emerald active, gray inactive)
- Touch swipe support for mobile (50px threshold)
- Smooth CSS transitions (400ms ease-out)

#### Scenario: Navigate via arrow buttons
- **WHEN** user clicks right arrow
- **THEN** carousel transitions to next slide
- **AND** dot indicator updates

#### Scenario: Navigate via swipe
- **WHEN** user swipes left more than 50px on mobile
- **THEN** carousel transitions to next slide

#### Scenario: Navigate via dot click
- **WHEN** user clicks a dot indicator
- **THEN** carousel jumps to corresponding slide

---

### Requirement: Research Agent Progress Display

The system SHALL display research agent progress during drill generation loading phase.

Three agents displayed:
1. Company Research - shows company analysis progress
2. Role Analysis - shows role context progress
3. Drill Generation - shows drill candidate progress

Agent status updates based on stream events:
- Status events update relevant agent to 'running' with message
- Candidate events mark drill generation as progressing
- Complete event transitions all to 'complete'

#### Scenario: Stream event updates agent status
- **WHEN** drill generation stream emits a status event
- **THEN** corresponding agent card updates to 'running' with message

#### Scenario: All agents complete
- **WHEN** all three agents reach 'complete' status
- **THEN** transition arrow appears below carousel

---

### Requirement: Transition Arrow

The system SHALL display an animated arrow when all research agents complete.

- Appears below carousel when all agents complete
- 48px circular button with emerald border
- Chevron down icon
- Bounce animation (2s cycle)
- Clicking scrolls to drill card section

#### Scenario: Arrow appears on completion
- **WHEN** all research agents complete
- **THEN** arrow fades in with bounce animation

#### Scenario: Arrow click scrolls to drill
- **WHEN** user clicks the transition arrow
- **THEN** page scrolls smoothly to drill card section

---

