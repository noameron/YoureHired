# Change: Add Role Selection Feature

## Why

This is the first feature of the YoureHired MVP. Users need to select their target company and role before the system can generate tailored coding practice tasks. Without role selection, the app cannot fulfill its core purpose of providing company- and role-specific practice.

## What Changes

- **NEW** Frontend form component for role selection with client-side validation
- **NEW** Backend endpoint `POST /api/user-selection` to receive and validate user selections
- **NEW** Backend configuration for predefined developer roles
- **NEW** Pinia store for managing user selection state
- **NEW** Router configuration for role selection page

## Impact

- Affected specs: `role-selection` (new capability)
- Affected code:
  - `frontend/src/views/` - New RoleSelectionView.vue
  - `frontend/src/stores/` - New userSelection store
  - `frontend/src/router/index.ts` - New route
  - `backend/app/api/` - New user_selection.py router
  - `backend/app/config.py` - Role configuration

## Decisions Made

Based on clarification with stakeholder:
1. **Roles**: Configurable via backend (stored in config, easy to update)
2. **Company Validation**: Skipped for MVP (accept any company name)
3. **API Design**: All parameters in JSON request body (cleaner REST pattern)

---

## Original Requirements Documents

### PRD.md (Product Requirements Document)

# Product Requirements Document (PRD)

## 1. **Purpose & Goals**
This app provides tailored coding practice for high-tech roles by generating company- and role-specific tasks. The goal is to help candidates prepare more effectively by aligning practice with their target job.

## 2. **Target Audience**
- Anyone applying for a developer or technical role in high-tech.
- Users can select difficulty levels: **Junior**, **Mid**, **Senior**.

## 3. **Key Features**
- **Role Selection**: Choose from predefined companies/roles or input a custom job description.
- **Task Generation**: LLM creates coding, debugging, and design tasks tailored to the role.
- **Feedback**: Users receive performance feedback after completing tasks.

## 4. **Requirements**
### Functional
- Users must select a role or input a custom job description.
- The system validates role/company or processes custom input.
- The LLM generates tailored tasks.
- Users complete tasks and receive feedback.

### Non-Functional
- Performance: Task generation should take no longer than X seconds.
- Security: Protect user data and LLM queries.

## 5. **User Stories**
- As a candidate, I want to select my target role so I get relevant practice tasks.
- As a user, I want feedback on my task performance so I know where to improve.

## 6. **Success Metrics**
- **User Satisfaction**: Measured through surveys or ratings.
- **Usage Growth**: Track the number of users over time.

## 7. **Constraints**
Currently, no fixed constraints on budget or timeline, allowing flexibility.

## 8. **Milestones**
- MVP: Role selection, basic task generation, feedback.
- Beta Launch: Expanded roles and company templates.
- Full Launch: User feedback loop and additional features.

---

### Technical.md (Role Selection Technical Plan)

# Role Selection – Technical Plan

## 1. Client-Side Validation

- **Mandatory Fields:**
  - **Company Name:** Must be filled and must be a string with a maximum length of 20 characters.
  - **Role Selection:** Must be chosen from the predefined roles.
  - **Role Description:** Optional free-text input.

- **Error Handling:**
  - If the user attempts to proceed without filling the mandatory fields, the client will display an error message specifying which fields are missing.

## 2. External Company Validation

- The client will use an external service (e.g., Google API or another provider) to validate the company name. This validation will happen on the client side before sending data to the backend.

> **MVP Decision**: External company validation is skipped for MVP. Any company name is accepted.

## 3. Backend Endpoint

- **Endpoint:** `/api/user-selection`
- **Method:** POST
- **Request Structure:**
  - **Request Body:** JSON containing company_name, role, and optional role_description

> **MVP Decision**: All parameters moved to request body for cleaner REST pattern.

- **Response Format:**
  - A standardized JSON response indicating success or failure.
  - If successful, it will include details about the company and the next steps for task generation.
  - If there's an error, the response will include a relevant error message.

## 4. Security Considerations

- **Prompt Injection Prevention:** Implement best practices to sanitize and validate inputs to protect against prompt injection vulnerabilities.

## 5. Testing and TDD

- The entire project will follow a Test-Driven Development approach, ensuring that all functionality is thoroughly tested from the outset.
