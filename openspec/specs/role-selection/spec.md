# role-selection Specification

## Purpose
TBD - created by archiving change add-role-selection. Update Purpose after archive.
## Requirements
### Requirement: The system MUST display predefined roles from backend configuration

The system MUST provide a list of predefined developer roles that users can select from. Roles are configured in the backend and fetched by the frontend.

#### Scenario: Frontend fetches available roles on page load

**Given** the user navigates to the role selection page
**When** the page loads
**Then** the frontend calls `GET /api/roles`
**And** displays all available roles in a dropdown/select component
**And** roles are shown with their human-readable labels

#### Scenario: Backend returns configured roles

**Given** the backend has predefined roles configured
**When** a client requests `GET /api/roles`
**Then** the response includes all configured roles with id and label
**And** the response format is:
```json
{
  "roles": [
    {"id": "frontend_developer", "label": "Frontend Developer"},
    {"id": "backend_developer", "label": "Backend Developer"}
  ]
}
```

---

### Requirement: The system MUST validate company name input

The company name field MUST be validated on both client and server side to ensure data quality and prevent abuse.

#### Scenario: Company name is required

**Given** the user is on the role selection form
**When** the user submits the form without entering a company name
**Then** the form displays an error: "Company name is required"
**And** the form is not submitted to the backend

#### Scenario: Company name exceeds maximum length

**Given** the user is on the role selection form
**When** the user enters a company name longer than 20 characters
**Then** the form displays an error: "Company name must be 20 characters or less"
**And** the form is not submitted to the backend

#### Scenario: Valid company name is accepted

**Given** the user is on the role selection form
**When** the user enters a company name between 1-20 characters
**Then** no validation error is shown for the company name field

#### Scenario: Backend validates company name

**Given** a POST request to `/api/user-selection`
**When** the company_name is empty or exceeds 20 characters
**Then** the response status is 422 (Unprocessable Entity)
**And** the response includes validation error details

---

### Requirement: The system MUST validate role selection

Users MUST select a role from the predefined list. Invalid or missing role selections are rejected.

#### Scenario: Role selection is required

**Given** the user is on the role selection form
**When** the user submits the form without selecting a role
**Then** the form displays an error: "Please select a role"
**And** the form is not submitted to the backend

#### Scenario: Invalid role is rejected by backend

**Given** a POST request to `/api/user-selection`
**When** the role value does not match any predefined role ID
**Then** the response status is 422 (Unprocessable Entity)
**And** the response includes: "Invalid role selected"

---

### Requirement: The system MUST accept optional role description

The system MUST accept an optional custom description to further specify the target role. This field is not required.

#### Scenario: Role description is optional

**Given** the user is on the role selection form
**When** the user submits the form without entering a role description
**Then** the form submits successfully (assuming other fields are valid)

#### Scenario: Role description has maximum length

**Given** the user is on the role selection form
**When** the user enters a role description longer than 500 characters
**Then** the form displays an error: "Description must be 500 characters or less"

#### Scenario: Role description is sanitized for prompt injection

**Given** a POST request to `/api/user-selection` with role_description
**When** the description contains potential prompt injection patterns
**Then** the backend sanitizes the input before storing
**And** excessive whitespace is normalized
**And** the sanitized value is returned in the response

---

### Requirement: The frontend MUST submit user selection to backend

When the user completes the form with valid data, the frontend MUST submit their selection to the backend for processing.

#### Scenario: Successful submission

**Given** the user has entered valid company name and selected a role
**When** the user submits the form
**Then** the frontend sends a POST request to `/api/user-selection`
**And** the request body contains:
```json
{
  "company_name": "Google",
  "role": "backend_developer",
  "role_description": "Optional description"
}
```
**And** on success, the user selection is stored in the Pinia store
**And** the response indicates the next step for task generation

#### Scenario: Backend returns success response

**Given** a valid POST request to `/api/user-selection`
**When** all validations pass
**Then** the response status is 200
**And** the response format is:
```json
{
  "success": true,
  "data": {
    "company_name": "Google",
    "role": "Backend Developer",
    "role_description": "...",
    "session_id": "uuid-string"
  },
  "next_step": "/api/generate-tasks"
}
```

#### Scenario: Backend returns validation errors

**Given** a POST request to `/api/user-selection`
**When** one or more validations fail
**Then** the response status is 422
**And** the response format is:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "field_name": "Error message for this field"
    }
  }
}
```

---

### Requirement: The system MUST display clear error messages

The system MUST provide clear, actionable feedback when validation fails.

#### Scenario: Multiple validation errors displayed

**Given** the user is on the role selection form
**When** the user submits with multiple invalid fields
**Then** all validation errors are displayed simultaneously
**And** each error is associated with its respective field

#### Scenario: Backend errors displayed to user

**Given** the user submits a valid form
**When** the backend returns an error response
**Then** the frontend displays the error message to the user
**And** the form remains editable for correction

---

### Requirement: The frontend MUST store selection in state

The frontend MUST store the user's selection in state for use in subsequent features (task generation).

#### Scenario: Selection stored after successful submission

**Given** the user submits the form successfully
**When** the backend returns a success response
**Then** the selection is stored in the userSelection Pinia store
**And** the store contains company_name, role, role_description, and session_id

#### Scenario: Store is accessible from other views

**Given** the user has completed role selection
**When** navigating to the task generation page (future feature)
**Then** the task generation view can access the stored selection

---

