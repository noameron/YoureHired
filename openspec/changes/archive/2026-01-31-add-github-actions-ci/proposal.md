# Change: Add GitHub Actions CI Workflow

## Why
The project currently lacks automated CI/CD. A GitHub Actions workflow will automatically validate code quality, run tests, and verify builds on every push and pull request, catching issues early and ensuring consistent quality standards.

## What Changes
- Add `.github/workflows/ci.yml` with comprehensive CI pipeline
- Backend validation: lint (ruff), type check (mypy), tests (pytest with coverage)
- Frontend validation: lint (eslint), type check (vue-tsc), tests (vitest), build verification
- Matrix strategy for multiple Python versions (optional)
- Caching for npm and uv dependencies for faster CI runs
- Clear job structure with parallelized independent jobs

## Impact
- Affected specs: None (new tooling capability)
- Affected code: New file `.github/workflows/ci.yml`
- No breaking changes to existing functionality
