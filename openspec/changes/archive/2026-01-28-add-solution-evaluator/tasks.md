## 1. Backend: Data Models
- [x] 1.1 Create `backend/app/schemas/evaluation.py` with Pydantic models:
  - `StrengthItem`, `ImprovementItem`, `SolutionFeedback`
  - `EvaluationRequest`, `EvaluationResponse`, `EvaluationErrorResponse`
- [x] 1.2 Add validation for `summary_for_next_drill` max 500 chars

## 2. Backend: Solution Evaluator Agent
- [x] 2.1 Create `backend/app/agents/evaluation/` directory
- [x] 2.2 Create `solution_evaluator_agent.py` with evaluation logic
- [x] 2.3 Apply security guardrails (injection + leakage)
- [x] 2.4 Write unit tests for agent output structure

## 3. Backend: Feedback Persistence
- [x] 3.1 Create utility function to generate feedback file path with timestamp
- [x] 3.2 Create markdown template for feedback file
- [x] 3.3 Implement file writing with directory creation
- [x] 3.4 Handle duplicate filenames within same minute
- [x] 3.5 Write tests for file persistence

## 4. Backend: API Endpoint
- [x] 4.1 Create `POST /api/evaluate-solution/{session_id}` endpoint
- [x] 4.2 Validate session exists and solution is non-empty
- [x] 4.3 Call evaluator agent and persist feedback
- [x] 4.4 Return structured response with feedback and file path
- [x] 4.5 Write integration tests for endpoint

## 5. Backend: Drill Generation Integration
- [x] 5.1 Add `previous_feedback_summary` field to drill generation input
- [x] 5.2 Update generator agent prompts to incorporate feedback context
- [x] 5.3 Update drill generation API to accept optional feedback parameter
- [x] 5.4 Write tests for feedback-aware drill generation

## 6. Frontend: API Client
- [x] 6.1 Add `submitSolution` function to `frontend/src/services/api.ts`
- [x] 6.2 Add TypeScript types for evaluation request/response

## 7. Frontend: Feedback UI
- [x] 7.1 Create `FeedbackCard.vue` component with score badge, strengths, improvements
- [x] 7.2 Add color-coded score display (red/yellow/green)
- [x] 7.3 Add expandable sections for strengths and improvements
- [x] 7.4 Add "Practice Weak Areas" button

## 8. Frontend: Integration
- [x] 8.1 Update `usePractice.ts` to call evaluation API on submit
- [x] 8.2 Update `PracticeView.vue` to show feedback after submission
- [x] 8.3 Wire "Practice Weak Areas" button to trigger new drill with feedback context
- [x] 8.4 Add loading state during evaluation
