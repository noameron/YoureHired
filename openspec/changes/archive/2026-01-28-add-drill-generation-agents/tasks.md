## 1. Schemas
- [x] 1.1 Create `backend/app/schemas/drill.py` with Drill, DrillCandidate, DrillEvaluation models
- [x] 1.2 Add DrillType and DifficultyLevel enums
- [x] 1.3 Add API response models (DrillGenerationResponse, streaming events)
- [x] 1.4 Add schema unit tests

## 2. Agents
- [x] 2.1 Create `backend/app/agents/drill/` package directory
- [x] 2.2 Implement coding_drill_agent.py with algorithm/data structure focus
- [x] 2.3 Implement debugging_drill_agent.py with bug-finding focus
- [x] 2.4 Implement design_drill_agent.py with system architecture focus
- [x] 2.5 Implement evaluator_agent.py with scoring criteria
- [x] 2.6 Create `__init__.py` with agent exports and HOW_MANY_GENERATORS
- [x] 2.7 Update `backend/app/agents/__init__.py` to export drill agents

## 3. Orchestration Service
- [x] 3.1 Create `backend/app/services/drill_generation.py`
- [x] 3.2 Implement `generate_drill()` with parallel execution
- [x] 3.3 Implement `generate_drill_stream()` for SSE streaming
- [x] 3.4 Add helper functions for building agent inputs
- [x] 3.5 Add service unit tests with mocked agents

## 4. API Endpoints
- [x] 4.1 Create `backend/app/api/drill.py` with router
- [x] 4.2 Implement POST `/api/generate-drill/{session_id}` endpoint
- [x] 4.3 Implement GET `/api/generate-drill/{session_id}/stream` SSE endpoint
- [x] 4.4 Update `backend/app/api/__init__.py` to include drill router
- [x] 4.5 Add API endpoint tests

## 5. Integration & Verification
- [x] 5.1 Run test suite (77 core tests pass)
- [x] 5.2 Manual end-to-end test with real LLM
- [x] 5.3 Verify streaming works in browser/curl
