## ADDED Requirements

### Requirement: GitHub GraphQL Client
The system SHALL provide an async client for querying GitHub's GraphQL API that handles authentication, rate limiting, and error recovery.

#### Scenario: Authenticated query execution
- **WHEN** a GraphQL query is submitted with a valid GitHub token
- **THEN** the client sends the query to `https://api.github.com/graphql` with the token in the `Authorization: Bearer` header and returns the parsed JSON response

#### Scenario: Rate limit awareness
- **WHEN** the remaining rate limit points fall below a configurable threshold (default: 100 points)
- **THEN** the client pauses requests and returns a rate-limit-exceeded signal to the caller with the reset timestamp

#### Scenario: Retry on transient failure
- **WHEN** a GraphQL request fails with a 502, 503, or network error
- **THEN** the client retries up to 3 times with exponential backoff (1s, 2s, 4s) and jitter before raising an error

#### Scenario: Missing or invalid token
- **WHEN** the GitHub token is empty or returns a 401 response
- **THEN** the client raises a configuration error with a clear message indicating the token is missing or invalid

### Requirement: Repository Discovery Search
The system SHALL discover public GitHub repositories matching user-defined search criteria using GitHub's GraphQL search API.

#### Scenario: Basic search with filters
- **WHEN** a user submits a search with language, star range, and minimum activity date
- **THEN** the system constructs a GitHub search query with the corresponding qualifiers (`language:X stars:min..max pushed:>date archived:false fork:false`) and returns matching repository metadata

#### Scenario: Topic-based search
- **WHEN** a user includes one or more topics in their search criteria
- **THEN** the system adds `topic:X` qualifiers to the search query for each specified topic

#### Scenario: Result count warning
- **WHEN** a search query returns 1,000 results (GitHub's maximum per query)
- **THEN** the system includes a warning in the SSE stream indicating results may be incomplete and suggests narrowing filters (fewer topics, smaller star range, more recent activity)

#### Scenario: Search returns metadata fields
- **WHEN** repositories are discovered via search
- **THEN** each result includes: repository name, owner, URL, description, primary language, all languages, star count, fork count, open issue count, topics, license, `pushedAt` timestamp, `createdAt` timestamp, and issue counts by label (specifically `good first issue` and `help wanted`)

### Requirement: README Fetching
The system SHALL fetch README content for repositories that pass client-side filtering, in a separate GraphQL pass from the initial discovery.

#### Scenario: Batch README fetch
- **WHEN** a list of repository owner/name pairs is provided (up to 20 per batch)
- **THEN** the system fetches the default-branch README for each repository in a single GraphQL query using aliases and returns the decoded text content

#### Scenario: Missing README
- **WHEN** a repository has no README file
- **THEN** the system returns `null` for that repository's README content without failing the batch

#### Scenario: README truncation
- **WHEN** a README exceeds 4,000 tokens (approximately 16,000 characters)
- **THEN** the system truncates to the first 4,000 tokens to keep AI agent context manageable

### Requirement: Client-Side Filtering
The system SHALL apply rule-based filters to discovered repositories before AI analysis to reduce the candidate set.

#### Scenario: Tutorial and awesome-list rejection
- **WHEN** a repository's name or description matches patterns indicating it is a tutorial, awesome-list, cheatsheet, or course material (e.g., name contains "awesome-", "tutorial", "learn-", "cheatsheet", or description contains "curated list of")
- **THEN** the system excludes that repository from the candidate set

#### Scenario: Minimum open issues filter
- **WHEN** a repository has zero open issues
- **THEN** the system excludes that repository (nothing to contribute to)

#### Scenario: Contribution-welcome signals
- **WHEN** a repository has issues labeled `good first issue` or `help wanted` with count > 0
- **THEN** the system boosts that repository's priority in the candidate list

#### Scenario: Configurable filter thresholds
- **WHEN** filter thresholds are defined (minimum stars, maximum stars, minimum days since push, minimum open issues)
- **THEN** the system applies all configured thresholds and excludes repositories that fail any threshold
