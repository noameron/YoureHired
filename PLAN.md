# Streaming Agent Updates Implementation Plan

## Goal
Stream planner, search, and summarizer agent updates to the frontend after "Start Practice" button click.

## Design Decisions
- **UI Behavior**: Current status only (replace each message)
- **Error Handling**: Show error with retry button if agent times out
- **Route Guard**: Redirect to `/` if no sessionId
- **Loading UI**: Simple centered spinner + text
- **Agent Timeout**: 60 seconds per operation

---

# GROUP 1: Backend Schemas (Isolated)

**Files to modify:** `backend/app/schemas/company_info.py`

**Task:** Add streaming event Pydantic models to the existing schema file.

**Context:** This file already contains `CompanySummary`, `SearchPlan`, `SearchQuery` models. Add new streaming event types at the end.

**Code to add:**

```python
# Add this import at the top
from typing import Literal

# Add these classes at the end of the file

class StreamStatusEvent(BaseModel):
    """Event for streaming status updates to frontend."""
    type: Literal["status"] = "status"
    message: str


class StreamCompleteEvent(BaseModel):
    """Event for streaming final result to frontend."""
    type: Literal["complete"] = "complete"
    data: CompanySummary


class StreamErrorEvent(BaseModel):
    """Event for streaming errors to frontend."""
    type: Literal["error"] = "error"
    message: str
```

**Verification:** Run `cd backend && uv run python -c "from app.schemas.company_info import StreamStatusEvent, StreamCompleteEvent, StreamErrorEvent; print('OK')"`

---

# GROUP 2: Backend Streaming Service (Isolated)

**Files to modify:** `backend/app/services/company_research.py`

**Task:** Add a new async generator function `research_company_stream` that yields status updates for each agent operation.

**Context:**
- This file has: `from agents import Runner`
- Existing agents: `planner_agent`, `search_agent`, `summarizer_agent`
- Existing types: `SearchPlan`, `SearchQuery`, `CompanySummary`
- Keep the existing `research_company` function unchanged

**Code to add:**

```python
# Add these imports at the top
import asyncio
from typing import AsyncGenerator

# Add this constant
AGENT_TIMEOUT = 60  # seconds

# Add this new function (keep existing research_company function)
async def research_company_stream(
    company_name: str,
    role: str
) -> AsyncGenerator[dict, None]:
    """
    Stream research progress and final results with timeout.
    Yields dict events: {"type": "status"|"complete"|"error", ...}
    """
    try:
        # Step 1: Plan searches
        yield {"type": "status", "message": "Planning research strategy..."}
        plan_input = f"Company: {company_name}\nRole: {role}"
        plan_result = await asyncio.wait_for(
            Runner.run(planner_agent, plan_input),
            timeout=AGENT_TIMEOUT
        )
        search_plan: SearchPlan = plan_result.final_output
        yield {"type": "status", "message": f"Found {len(search_plan.searches)} areas to research"}

        # Step 2: Execute searches sequentially, streaming each one
        search_results = []
        for i, item in enumerate(search_plan.searches, 1):
            yield {"type": "status", "message": f"Searching ({i}/{len(search_plan.searches)}): {item.reason}"}
            try:
                search_input = f"Search term: {item.query}\nReason: {item.reason}"
                result = await asyncio.wait_for(
                    Runner.run(search_agent, search_input),
                    timeout=AGENT_TIMEOUT
                )
                search_results.append(result.final_output)
            except asyncio.TimeoutError:
                yield {"type": "status", "message": f"Search {i} timed out, continuing..."}
            except Exception:
                yield {"type": "status", "message": f"Search {i} failed, continuing..."}

        if not search_results:
            yield {"type": "error", "message": "All searches failed. Please try again."}
            return

        # Step 3: Summarize
        yield {"type": "status", "message": "Analyzing findings..."}
        combined = "\n\n".join(search_results)
        summary_input = f"Company: {company_name}\nRole: {role}\n\nResearch:\n{combined}"
        summary_result = await asyncio.wait_for(
            Runner.run(summarizer_agent, summary_input),
            timeout=AGENT_TIMEOUT
        )

        # Final result
        yield {"type": "complete", "data": summary_result.final_output.model_dump()}

    except asyncio.TimeoutError:
        yield {"type": "error", "message": "Research timed out. Please try again."}
    except Exception as e:
        yield {"type": "error", "message": f"Research failed: {str(e)}"}
```

**Verification:** Run `cd backend && uv run python -c "from app.services.company_research import research_company_stream; print('OK')"`

---

# GROUP 3: Backend SSE Endpoint (Isolated)

**Files to modify:** `backend/app/api/company_info.py`

**Task:** Add a new SSE streaming endpoint `/company-research/{session_id}/stream`.

**Context:**
- File already imports: `APIRouter`, `HTTPException`, `session_store`
- File already has router: `router = APIRouter(tags=["company-info"])`
- Session store has `.get(session_id)` returning object with `.company_name` and `.role`
- Need to import the new `research_company_stream` function

**Code to add:**

```python
# Add these imports at the top
from fastapi.responses import StreamingResponse
import json

# Add this import for the streaming function
from app.services.company_research import research_company_stream

# Add this new endpoint
@router.get("/company-research/{session_id}/stream")
async def stream_company_research(session_id: str):
    """Stream company research progress via Server-Sent Events."""
    session = session_store.get(session_id)

    if not session:
        async def error_gen():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
        return StreamingResponse(
            error_gen(),
            media_type="text/event-stream",
        )

    async def event_generator():
        async for event in research_company_stream(session.company_name, session.role):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

**Verification:** Run `cd backend && uv run uvicorn app.main:app --reload` and test with `curl -N http://localhost:8000/api/company-research/test-session/stream`

---

# GROUP 4: Frontend Types & API (Isolated)

**Files to modify:**
- `frontend/src/types/api.ts`
- `frontend/src/services/api.ts`

**Task:** Add TypeScript types for streaming events and CompanySummary, plus add async generator function for consuming SSE stream.

### File 1: `frontend/src/types/api.ts`

**Context:** This file has existing types like `Role`, `UserSelectionRequest`, etc. Add new types at the end.

**Code to add:**

```typescript
// Company research types
export interface TechStack {
  languages: string[]
  frameworks: string[]
  tools: string[]
}

export interface CompanySummary {
  name: string
  industry: string | null
  description: string
  size: string | null
  tech_stack: TechStack | null
  engineering_culture: string | null
  recent_news: string[]
  interview_tips: string | null
  sources: string[]
}

// Streaming event types
export interface StreamStatusEvent {
  type: 'status'
  message: string
}

export interface StreamCompleteEvent {
  type: 'complete'
  data: CompanySummary
}

export interface StreamErrorEvent {
  type: 'error'
  message: string
}

export type StreamEvent = StreamStatusEvent | StreamCompleteEvent | StreamErrorEvent
```

### File 2: `frontend/src/services/api.ts`

**Context:** This file has `const API_BASE = '/api'` and existing functions. Add new function at the end.

**Code to add:**

```typescript
// Add this import at the top
import type { StreamEvent } from '@/types/api'

// Add this function at the end
/**
 * Stream company research progress via Server-Sent Events.
 * Yields events as they arrive from the backend.
 */
export async function* streamCompanyResearch(
  sessionId: string
): AsyncGenerator<StreamEvent> {
  const response = await fetch(`${API_BASE}/company-research/${sessionId}/stream`)

  if (!response.ok) {
    throw new Error(`Stream failed: ${response.status}`)
  }

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || '' // Keep incomplete line in buffer

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        yield JSON.parse(line.slice(6)) as StreamEvent
      }
    }
  }
}
```

**Verification:** Run `cd frontend && npm run build` (should compile without errors)

---

# GROUP 5: Frontend Views & Router (Isolated)

**Files to modify:**
- `frontend/src/views/PracticeView.vue` (CREATE)
- `frontend/src/router/index.ts`
- `frontend/src/views/RoleSelectionView.vue`

**Task:** Create PracticeView component, add route with guard, update RoleSelectionView to navigate on success.

### File 1: `frontend/src/views/PracticeView.vue` (CREATE NEW FILE)

**Context:**
- Import `streamCompanyResearch` from `@/services/api`
- Import `useUserSelectionStore` from `@/stores/userSelection` (has `.sessionId`, `.companyName`, `.role`)
- Import `CompanySummary` type from `@/types/api`

**Full file content:**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'
import { streamCompanyResearch } from '@/services/api'
import type { CompanySummary } from '@/types/api'

const router = useRouter()
const store = useUserSelectionStore()

const currentStatus = ref<string>('Connecting...')
const summary = ref<CompanySummary | null>(null)
const error = ref<string | null>(null)
const isComplete = ref(false)

async function startResearch() {
  if (!store.sessionId) {
    router.push('/')
    return
  }

  error.value = null
  isComplete.value = false
  currentStatus.value = 'Starting research...'

  try {
    for await (const event of streamCompanyResearch(store.sessionId)) {
      if (event.type === 'status') {
        currentStatus.value = event.message
      } else if (event.type === 'complete') {
        summary.value = event.data
        isComplete.value = true
      } else if (event.type === 'error') {
        error.value = event.message
      }
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Connection failed'
  }
}

function retry() {
  startResearch()
}

onMounted(() => {
  startResearch()
})
</script>

<template>
  <div class="practice-view">
    <div class="content">
      <!-- Loading state -->
      <div v-if="!isComplete && !error" class="loading-state">
        <div class="spinner"></div>
        <p class="status">{{ currentStatus }}</p>
        <p class="context">Researching {{ store.companyName }} for {{ store.role }}</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="error-state">
        <p class="error-message">{{ error }}</p>
        <button @click="retry" class="retry-button">Try Again</button>
      </div>

      <!-- Complete state - show summary -->
      <div v-else-if="summary" class="summary-state">
        <h1>{{ summary.name }}</h1>
        <p class="description">{{ summary.description }}</p>

        <div v-if="summary.tech_stack" class="section">
          <h3>Tech Stack</h3>
          <p v-if="summary.tech_stack.languages.length">
            <strong>Languages:</strong> {{ summary.tech_stack.languages.join(', ') }}
          </p>
          <p v-if="summary.tech_stack.frameworks.length">
            <strong>Frameworks:</strong> {{ summary.tech_stack.frameworks.join(', ') }}
          </p>
          <p v-if="summary.tech_stack.tools.length">
            <strong>Tools:</strong> {{ summary.tech_stack.tools.join(', ') }}
          </p>
        </div>

        <div v-if="summary.engineering_culture" class="section">
          <h3>Engineering Culture</h3>
          <p>{{ summary.engineering_culture }}</p>
        </div>

        <div v-if="summary.interview_tips" class="section">
          <h3>Interview Tips</h3>
          <p>{{ summary.interview_tips }}</p>
        </div>

        <div v-if="summary.recent_news.length" class="section">
          <h3>Recent News</h3>
          <ul>
            <li v-for="(news, idx) in summary.recent_news" :key="idx">{{ news }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.practice-view {
  min-height: 100vh;
  background: #f0f2f5;
  display: flex;
  justify-content: center;
  padding: 2rem;
}

.content {
  max-width: 700px;
  width: 100%;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e0e0e0;
  border-top-color: #0066ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.status {
  font-size: 1.25rem;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.context {
  color: #6c757d;
  font-size: 0.9rem;
}

.error-state {
  text-align: center;
  padding: 4rem 2rem;
}

.error-message {
  color: #dc3545;
  margin-bottom: 1.5rem;
}

.retry-button {
  background: #0066ff;
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
}

.retry-button:hover {
  background: #0052cc;
}

.summary-state {
  background: white;
  border-radius: 16px;
  padding: 2rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.summary-state h1 {
  margin: 0 0 1rem;
  color: #1a1a2e;
}

.description {
  color: #4a5568;
  line-height: 1.6;
  margin-bottom: 2rem;
}

.section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.summary-state h3 {
  color: #1a1a2e;
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
}

.summary-state p {
  color: #4a5568;
  margin: 0.5rem 0;
}

.summary-state ul {
  color: #4a5568;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}
</style>
```

### File 2: `frontend/src/router/index.ts` (REPLACE ENTIRE FILE)

**Full file content:**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useUserSelectionStore } from '@/stores/userSelection'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'role-selection',
    component: () => import('@/views/RoleSelectionView.vue')
  },
  {
    path: '/practice',
    name: 'practice',
    component: () => import('@/views/PracticeView.vue'),
    beforeEnter: (to, from, next) => {
      const store = useUserSelectionStore()
      if (!store.sessionId) {
        next('/')
      } else {
        next()
      }
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

### File 3: `frontend/src/views/RoleSelectionView.vue` (MODIFY)

**Context:** Find the `<script setup>` section and make these changes:

**Change 1:** Add router import at top of script:
```typescript
import { useRouter } from 'vue-router'
```

**Change 2:** Add router initialization after `const store = useUserSelectionStore()`:
```typescript
const router = useRouter()
```

**Change 3:** In `handleSubmit()` function, after `isSuccess.value = true`, add:
```typescript
router.push('/practice')
```

**Verification:**
1. Run `cd frontend && npm run dev`
2. Fill form, click "Start Practice"
3. Should navigate to `/practice` and show streaming status

---

# Verification (Full Flow)

1. Start backend: `cd backend && uv run uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Test happy path: Fill form → Click "Start Practice" → See streaming updates → See final summary
4. Test route guard: Navigate to `localhost:3000/practice` directly → Should redirect to `/`
5. Run tests: `cd backend && uv run pytest` and `cd frontend && npm run test:run`
