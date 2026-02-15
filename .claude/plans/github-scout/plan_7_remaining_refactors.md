# Plan 7 — Remaining Refactors

Deferred issues from full-review of `scout/07-orchestrator-and-search-api`.
All are non-blocking quality improvements — 284 tests pass, lint clean.

## All Done

- Extracted phase helpers in `scout_orchestrator.py` (123 → ~50 line main fn)
- Extracted `_row_to_analysis_result` / `_row_to_repo_metadata` in `github_repos_db.py`
- Added `SearchRunStatus` type annotation in orchestrator
- Fixed `_active_searches` race condition between `start_search` and `stream_search`
- Added 404 check in `cancel_search`
- Added `min(analyzed + bs, total)` to prevent overcount on batch failure
- Used `executemany` in `upsert_repositories` (replaced N execute → 1 executemany)
- Optimized `save_analysis_results` with `insert_analysis_with_lookup.sql` (combined lookup + insert, executemany)
- Extracted `_validate_stream_request()` in `scout.py` (stream_search handler 32 → ~15 lines)
- Extracted `_retry_request()` in `github_client.py` (_execute_query 46 → ~15 lines)
- Extracted `_format_repo_section()` in `scout_analysis.py` (_build_batch_input 51 → ~20 lines)
