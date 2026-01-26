export interface Role {
  id: string
  label: string
}

export interface RolesResponse {
  roles: Role[]
}

export interface UserSelectionRequest {
  company_name: string
  role: string
  role_description?: string
}

export interface UserSelectionData {
  company_name: string
  role: string
  role_description: string | null
  session_id: string
}

export interface UserSelectionResponse {
  success: true
  data: UserSelectionData
  next_step: string
}

export interface UserSelectionErrorDetails {
  code: string
  message: string
  details: Record<string, string>
}

export interface UserSelectionError {
  success: false
  error: UserSelectionErrorDetails
}

export type UserSelectionResult = UserSelectionResponse | UserSelectionError
