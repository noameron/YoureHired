# CI Workflow Specification

## ADDED Requirements

### Requirement: CI Workflow Triggers
The CI workflow SHALL run on push events to the main branch and on all pull requests targeting the main branch.

#### Scenario: Push to main triggers CI
- **WHEN** code is pushed to the main branch
- **THEN** the CI workflow runs all validation jobs

#### Scenario: Pull request triggers CI
- **WHEN** a pull request is opened or updated targeting main
- **THEN** the CI workflow runs all validation jobs

---

### Requirement: Backend Linting
The CI workflow SHALL run ruff linting on the backend code and fail if any linting errors are found.

#### Scenario: Backend lint passes
- **WHEN** the backend lint step runs
- **AND** all code passes ruff checks
- **THEN** the step succeeds

#### Scenario: Backend lint fails
- **WHEN** the backend lint step runs
- **AND** ruff reports errors
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Backend Type Checking
The CI workflow SHALL run mypy type checking on the backend code and fail if any type errors are found.

#### Scenario: Backend type check passes
- **WHEN** the backend type check step runs
- **AND** mypy reports no errors
- **THEN** the step succeeds

#### Scenario: Backend type check fails
- **WHEN** the backend type check step runs
- **AND** mypy reports type errors
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Backend Tests
The CI workflow SHALL run pytest with coverage on the backend code and fail if any tests fail.

#### Scenario: Backend tests pass
- **WHEN** the backend test step runs
- **AND** all pytest tests pass
- **THEN** the step succeeds

#### Scenario: Backend tests fail
- **WHEN** the backend test step runs
- **AND** one or more pytest tests fail
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Frontend Linting
The CI workflow SHALL run ESLint on the frontend code and fail if any linting errors are found.

#### Scenario: Frontend lint passes
- **WHEN** the frontend lint step runs
- **AND** all code passes ESLint checks
- **THEN** the step succeeds

#### Scenario: Frontend lint fails
- **WHEN** the frontend lint step runs
- **AND** ESLint reports errors
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Frontend Type Checking
The CI workflow SHALL run vue-tsc type checking on the frontend code and fail if any type errors are found.

#### Scenario: Frontend type check passes
- **WHEN** the frontend type check step runs
- **AND** vue-tsc reports no errors
- **THEN** the step succeeds

#### Scenario: Frontend type check fails
- **WHEN** the frontend type check step runs
- **AND** vue-tsc reports type errors
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Frontend Tests
The CI workflow SHALL run vitest on the frontend code and fail if any tests fail.

#### Scenario: Frontend tests pass
- **WHEN** the frontend test step runs
- **AND** all vitest tests pass
- **THEN** the step succeeds

#### Scenario: Frontend tests fail
- **WHEN** the frontend test step runs
- **AND** one or more vitest tests fail
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Frontend Build Verification
The CI workflow SHALL verify the frontend builds successfully and fail if the build fails.

#### Scenario: Frontend build succeeds
- **WHEN** the frontend build step runs
- **AND** the build completes without errors
- **THEN** the step succeeds

#### Scenario: Frontend build fails
- **WHEN** the frontend build step runs
- **AND** the build encounters errors
- **THEN** the step fails and the job is marked as failed

---

### Requirement: Dependency Caching
The CI workflow SHALL cache npm and uv dependencies to reduce CI execution time on subsequent runs.

#### Scenario: Dependencies are cached
- **WHEN** the CI workflow runs
- **AND** the dependency cache exists from a previous run
- **THEN** cached dependencies are restored instead of being downloaded

#### Scenario: Cache miss
- **WHEN** the CI workflow runs
- **AND** no matching cache exists
- **THEN** dependencies are installed and cached for future runs

---

### Requirement: Parallel Job Execution
The CI workflow SHALL run backend and frontend jobs in parallel to minimize total execution time.

#### Scenario: Jobs run in parallel
- **WHEN** the CI workflow starts
- **THEN** the backend and frontend jobs start simultaneously
- **AND** the workflow completes when both jobs finish
