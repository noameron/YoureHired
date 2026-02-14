## ADDED Requirements

### Requirement: Repo Analyst Agent
The system SHALL provide an AI agent that evaluates a batch of repositories' fit for a specific developer profile and returns structured analyses.

#### Scenario: Successful batch analysis
- **WHEN** the agent receives a batch of 5-10 repositories (each with README content and metadata) and a developer profile
- **THEN** the agent returns a JSON array of objects, one per repository, each with: `repo` (owner/name identifier), `fit_score` (0-10 float), `reason` (1-2 sentence explanation), `contributions` (list of 1-3 specific contribution suggestions), and `reject` (boolean)

#### Scenario: Partial batch failure
- **WHEN** the agent returns results for some but not all repositories in a batch
- **THEN** the system accepts the partial results for repos that were analyzed and marks the remaining repos as skipped with an appropriate log entry

#### Scenario: Rejection of noise repos
- **WHEN** the agent determines a repository is a tutorial, awesome-list, documentation-only project, or clearly outside the developer's domain despite passing filters
- **THEN** the agent sets `reject: true` with a `reject_reason` explaining why, and `fit_score: 0`

#### Scenario: Scoring rubric
- **WHEN** the agent scores a repository
- **THEN** the score follows this rubric: 9-10 = perfect tech stack match + active issues in developer's domain; 7-8 = strong match with some relevant issues; 5-6 = partial tech stack overlap or limited contribution opportunities; 3-4 = weak match; 1-2 = marginal relevance; 0 = rejected

#### Scenario: Agent uses guardrails
- **WHEN** the agent processes input
- **THEN** it runs through the standard injection and leakage guardrails used by all YoureHired agents

#### Scenario: Missing README fallback
- **WHEN** a repository has no README content
- **THEN** the agent bases its analysis on metadata only (description, languages, topics, issue counts) and notes the limited data in its reason

### Requirement: Developer Profile Matching
The system SHALL match repositories against a developer profile that includes languages, topics of interest, skill level, and contribution goals.

#### Scenario: Language match
- **WHEN** a repository's primary or secondary languages overlap with the developer's listed languages
- **THEN** the agent weights this positively in the fit score

#### Scenario: Topic match
- **WHEN** a repository's topics overlap with the developer's topics of interest
- **THEN** the agent weights this positively in the fit score

#### Scenario: Skill level consideration
- **WHEN** the developer profile indicates a skill level (beginner, intermediate, advanced)
- **THEN** the agent considers project complexity and availability of beginner-friendly issues when scoring

#### Scenario: Contribution goal alignment
- **WHEN** the developer specifies goals (e.g., "learn testing", "improve system design", "contribute to ML tools")
- **THEN** the agent evaluates whether the repository offers opportunities aligned with those goals

### Requirement: Batch Analysis Orchestration
The system SHALL orchestrate AI analysis across multiple repositories in batches with progress streaming.

#### Scenario: Batched concurrent analysis with progress
- **WHEN** a batch of filtered repositories is submitted for analysis
- **THEN** the system groups repos into batches of 5-10, sends each batch to the agent in a single call, and runs batches concurrently using `asyncio.as_completed`
- SSE progress events emit after each batch completes (not per-repo)
- Progress format: "Analyzed 10/34 repos..."

#### Scenario: Batch analysis timeout
- **WHEN** a batch analysis exceeds the configured timeout (default: 60 seconds for a batch of up to 10)
- **THEN** the system skips that batch, logs the timeout, emits an SSE event noting the skipped repos, and continues with remaining batches

#### Scenario: Analysis cap
- **WHEN** the number of filtered repositories exceeds the configured maximum (default: 50)
- **THEN** the system analyzes only the top 50 repositories (sorted by contribution-welcome signals) and informs the user that results were capped

### Requirement: Search Rate Limiting
The system SHALL enforce rate limits on the search endpoint to prevent runaway AI spend.

#### Scenario: Concurrent search limit
- **WHEN** a search is initiated while another search is already running
- **THEN** the system rejects the new search with a 429 status and message indicating an active search exists

#### Scenario: Search throttle
- **WHEN** more than 5 searches are initiated from the same IP within one hour
- **THEN** the system rejects the search with a 429 status and retry-after header

### Requirement: Partial Result Recovery
The system SHALL recover gracefully when batch analysis partially fails.

#### Scenario: Batch failure with prior results
- **WHEN** an agent batch fails but previous batches completed successfully
- **THEN** the system returns all successfully analyzed repos as partial results, marks the search run as `partial`, and includes an SSE event listing which repos could not be analyzed
