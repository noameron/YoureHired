## ADDED Requirements

### Requirement: Scout Page
The system SHALL provide a dedicated `/scout` page in the frontend for GitHub repository discovery and analysis.

#### Scenario: Page accessible without session
- **WHEN** a user navigates to `/scout`
- **THEN** the page loads without requiring an active YoureHired session (no company/role selection needed)

#### Scenario: Page layout
- **WHEN** the Scout page loads
- **THEN** it displays a search filter form, a developer profile section, and a results area (initially empty with a prompt to configure and search)

### Requirement: Search Filter Form
The system SHALL provide a form where users configure GitHub search parameters.

#### Scenario: Available filter inputs
- **WHEN** the filter form is displayed
- **THEN** the user can configure: programming languages (multi-select), star range (min/max number inputs), topics (comma-separated text input or tag input), minimum activity date (date picker defaulting to 6 months ago), and license preference (optional select)

#### Scenario: Search submission
- **WHEN** the user fills in at least one language and clicks "Search"
- **THEN** the frontend sends the filter configuration to the backend search API endpoint and begins displaying streaming progress

#### Scenario: Validation
- **WHEN** the user attempts to search without selecting any language
- **THEN** the form shows a validation error on the language field: "Select at least one language"

#### Scenario: Result cap warning
- **WHEN** a search returns 1,000 results from GitHub (maximum per query)
- **THEN** the UI displays a warning banner suggesting the user narrow their filters for more complete results

#### Scenario: Search in progress
- **WHEN** a search is running
- **THEN** the Search button is disabled, a progress indicator shows the current phase (Discovering → Filtering → Analyzing), and the user can cancel the search

### Requirement: Developer Profile Form
The system SHALL provide a form for users to configure their developer profile used for AI matching.

#### Scenario: Profile fields
- **WHEN** the profile form is displayed
- **THEN** the user can configure: known languages (multi-select), topics of interest (tag input), skill level (beginner/intermediate/advanced radio), and contribution goals (free-text textarea, max 500 characters)

#### Scenario: Profile persistence
- **WHEN** the user saves their profile
- **THEN** the profile is sent to the backend API and stored in SQLite, persisting across browser sessions

#### Scenario: Profile required for analysis
- **WHEN** the user starts a search without having saved a developer profile
- **THEN** the system prompts the user to fill in their profile before the AI analysis phase begins (discovery and filtering can proceed without a profile)

### Requirement: Search Results Display
The system SHALL display discovered and analyzed repositories in a ranked list.

#### Scenario: Result card content
- **WHEN** analysis results are available
- **THEN** each result is displayed as a card showing: repository name (linked to GitHub URL), description, fit score (visual indicator), primary language, star count, reason for the score, and suggested contributions as a bulleted list

#### Scenario: Sorting
- **WHEN** results are displayed
- **THEN** results are sorted by fit score descending (highest score first) by default, with rejected repos hidden

#### Scenario: Empty results
- **WHEN** a search completes with zero results after filtering
- **THEN** the results area shows a message suggesting the user broaden their search filters (fewer topics, wider star range, older activity date)

#### Scenario: Streaming progress display
- **WHEN** a search is in progress
- **THEN** the UI shows real-time updates: number of repos discovered, number passing filters, and analysis progress (e.g., "Analyzed 10/34 repos..." — updates per batch, not per repo)

### Requirement: Navigation Integration
The system SHALL integrate the Scout page into the application navigation.

#### Scenario: Route registration
- **WHEN** the Vue Router is configured
- **THEN** a `/scout` route exists pointing to the ScoutView component, lazy-loaded

#### Scenario: Navigation link
- **WHEN** the application is loaded
- **THEN** a navigation element (link or button) is visible allowing users to navigate to the Scout page from any other page
