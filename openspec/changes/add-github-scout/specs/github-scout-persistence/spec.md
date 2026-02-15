## ADDED Requirements

### Requirement: SQLite Database Initialization
The system SHALL initialize a SQLite database on startup for persisting Scout data.

#### Scenario: Database creation on first run
- **WHEN** the application starts and no SQLite database file exists at the configured path
- **THEN** the system creates the database file and runs all schema migrations to set up tables

#### Scenario: Database path configuration
- **WHEN** the `SCOUT_DB_PATH` setting is configured in the environment
- **THEN** the system uses that path for the SQLite database file; if not configured, defaults to `data/scout.db` relative to the backend root

#### Scenario: WAL mode enabled
- **WHEN** the database connection is established
- **THEN** the system enables WAL (Write-Ahead Logging) mode for better concurrent read performance

### Requirement: Developer Profile Storage
The system SHALL persist developer profiles in the SQLite database.

#### Scenario: Save new profile
- **WHEN** a developer profile is submitted via the API with languages, topics, skill level, and goals
- **THEN** the system stores the profile in the `developer_profiles` table with a generated UUID and `created_at` timestamp

#### Scenario: Update existing profile
- **WHEN** a profile update is submitted for an existing profile ID
- **THEN** the system updates the profile fields and sets the `updated_at` timestamp

#### Scenario: Retrieve profile
- **WHEN** a profile is requested by ID
- **THEN** the system returns the full profile including all fields and timestamps

#### Scenario: Single profile mode
- **WHEN** the system operates in single-user mode (V1)
- **THEN** only one developer profile exists at a time; saving a new profile replaces the previous one

### Requirement: Search Run Tracking
The system SHALL track each discovery-and-analysis run in the database.

#### Scenario: Record search run
- **WHEN** a search is initiated
- **THEN** the system creates a `search_runs` record with: run UUID, profile ID, filter configuration (JSON), status (`running`), and `started_at` timestamp

#### Scenario: Update search run status
- **WHEN** a search completes or fails
- **THEN** the system updates the run status to `completed` or `failed` and sets the `finished_at` timestamp and result summary (total discovered, total filtered, total analyzed)

### Requirement: Repository Storage
The system SHALL persist discovered repository metadata in the database, deduplicated by GitHub ID.

#### Scenario: Store discovered repositories
- **WHEN** repositories are discovered from GitHub
- **THEN** each repository is upserted into the `repositories` table using the GitHub numeric ID as the unique key, updating metadata if the repo already exists from a prior run

#### Scenario: Repository fields
- **WHEN** a repository is stored
- **THEN** the record includes: GitHub ID, owner, name, URL, description, primary language, all languages (JSON array), star count, fork count, open issue count, topics (JSON array), license, `pushed_at`, `created_at` (GitHub), and `last_seen_at` (local timestamp)

#### Scenario: Repository data cleanup
- **WHEN** the system runs a periodic cleanup (daily or on startup)
- **THEN** repositories not referenced by any analysis result and not seen in the last 30 days are deleted from the repositories table

### Requirement: Analysis Result Storage
The system SHALL persist AI analysis results linked to both the search run and repository.

#### Scenario: Store analysis result
- **WHEN** the AI agent completes analysis of a repository
- **THEN** the result is stored with: search run ID, repository ID, fit score, reason, contributions (JSON array), reject flag, reject reason, and `analyzed_at` timestamp

#### Scenario: Query results by search run
- **WHEN** results for a specific search run are requested
- **THEN** the system returns all analysis results for that run joined with repository metadata, sorted by fit score descending

### Requirement: Scout API Endpoints
The system SHALL expose REST API endpoints for Scout operations.

#### Scenario: POST /api/scout/profile
- **WHEN** a POST request with a developer profile payload is received
- **THEN** the system saves/updates the profile and returns the profile ID

#### Scenario: GET /api/scout/profile
- **WHEN** a GET request is received
- **THEN** the system returns the current developer profile, or 404 if none exists

#### Scenario: POST /api/scout/search
- **WHEN** a POST request with search filter configuration is received
- **THEN** the system initiates a search run and returns the run ID immediately; the search executes asynchronously

#### Scenario: GET /api/scout/search/{run_id}/stream
- **WHEN** a GET request for a search run's stream is received
- **THEN** the system returns an SSE stream with progress events for discovery, filtering, and analysis phases

#### Scenario: GET /api/scout/search/{run_id}/results
- **WHEN** a GET request for a search run's results is received after completion
- **THEN** the system returns the full analysis results sorted by fit score descending

#### Scenario: Rate limited search
- **WHEN** `POST /api/scout/search` is called while another search is active or the IP has exceeded 5 searches/hour
- **THEN** the system returns 429 Too Many Requests with appropriate messaging

#### Scenario: POST /api/scout/search/{run_id}/cancel
- **WHEN** a POST request to cancel a running search is received
- **THEN** the system cancels the active search, updates the run status to `cancelled`, and closes the SSE stream
