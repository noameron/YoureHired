# role-selection-ui Specification

## Purpose
TBD - created by archiving change update-role-selection-ui. Update Purpose after archive.
## Requirements
### Requirement: The role selection page MUST display form fields in distinct rounded card sections

The role selection form MUST present each input field group within its own visually distinct card container with rounded corners, creating a clean sectioned layout.

#### Scenario: Three card sections displayed vertically

**Given** the user navigates to the role selection page
**When** the page loads successfully
**Then** three distinct card sections are displayed vertically (top to bottom):
  1. Company Name section with text input
  2. Role section with dropdown select
  3. Role Description section with textarea
**And** each section has visible rounded borders and subtle shadows
**And** sections have consistent padding and vertical spacing between them

#### Scenario: Company Name section structure

**Given** the role selection page is displayed
**When** viewing the Company Name section
**Then** the section displays a "Company Name" label
**And** contains a text input field with placeholder "Enter company name"
**And** validation errors appear below the input when triggered

#### Scenario: Role section structure

**Given** the role selection page is displayed
**When** viewing the Role section
**Then** the section displays a "Role" label
**And** contains a dropdown select with "Select a role" as default
**And** dropdown options are populated from the backend API
**And** validation errors appear below the select when triggered

#### Scenario: Role Description section structure

**Given** the role selection page is displayed
**When** viewing the Role Description section
**Then** the section displays a "Role Description (Optional)" label
**And** contains a multi-line textarea
**And** displays a character count (e.g., "0 / 8000")
**And** validation errors appear below the textarea when triggered

---

### Requirement: The role selection page MUST display an animated background with floating tech icons

The page MUST include an animated background layer featuring tech-related SVG icons that move in orbital/circular paths, creating a hightech visual atmosphere.

#### Scenario: Floating tech icons are visible in background

**Given** the user navigates to the role selection page
**When** the page loads
**Then** multiple tech-themed SVG icons are visible in the background
**And** icons include representations such as keyboard, monitor, code symbols, mouse, or terminal
**And** icons have low opacity (10-20%) so they do not distract from form content
**And** icons are positioned behind the form content (lower z-index)

#### Scenario: Icons animate in orbital motion

**Given** the role selection page is displayed
**When** observing the background
**Then** icons move continuously in circular or orbital paths
**And** different icons have varying animation speeds and delays
**And** animation is smooth and uses CSS transforms

#### Scenario: Animation respects reduced motion preference

**Given** the user has enabled "prefers-reduced-motion" in their OS settings
**When** the page loads
**Then** the floating icon animations are paused or disabled
**And** icons may remain visible but static

---

### Requirement: The role selection page MUST follow a minimal hightech light mode design

The page design MUST use a clean, modern aesthetic with light backgrounds, subtle accents, and professional styling.

#### Scenario: Light mode color scheme applied

**Given** the role selection page is displayed
**When** viewing the page
**Then** the page background uses a light gray color
**And** card sections use white backgrounds
**And** text uses dark colors for readability
**And** the primary accent color (blue) is used for the submit button and focus states

#### Scenario: Interactive elements have visual feedback

**Given** the user is interacting with the form
**When** hovering over or focusing on input fields, dropdowns, or buttons
**Then** visual transitions indicate the interactive state
**And** focus states show a visible border or glow
**And** the submit button changes appearance on hover

---

### Requirement: The role selection page MUST maintain responsive design

The redesigned page MUST remain usable across different screen sizes.

#### Scenario: Mobile viewport display

**Given** the user views the page on a mobile device (width < 768px)
**When** the page loads
**Then** card sections stack vertically with appropriate spacing
**And** form inputs are full-width within their cards
**And** animated background icons are visible and scale appropriately

#### Scenario: Desktop viewport display

**Given** the user views the page on a desktop (width >= 768px)
**When** the page loads
**Then** the form is centered with a maximum width constraint
**And** card sections maintain comfortable reading width
**And** animated background covers the full viewport

