import re

from pydantic import BaseModel, Field, field_validator

from app.utils.sanitization import sanitize_input

EMOJI_PATTERN = re.compile(
    r"[\U0001F600-\U0001F64F"  # emoticons
    r"\U0001F300-\U0001F5FF"  # symbols & pictographs
    r"\U0001F680-\U0001F6FF"  # transport & map symbols
    r"\U0001F1E0-\U0001F1FF"  # flags
    r"\U00002702-\U000027B0"  # dingbats
    r"\U000024C2-\U0001F251"  # enclosed characters
    r"]+",
    flags=re.UNICODE,
)


class UserSelectionRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Company name (2-100 chars, no emojis)",
    )
    role: str = Field(..., description="Role ID from predefined roles")
    role_description: str | None = Field(
        None,
        description="Optional role description (30-8000 characters if provided)",
    )

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name is required")
        if EMOJI_PATTERN.search(v):
            raise ValueError("Company name cannot contain emojis")
        # Sanitize for LLM safety (normalize whitespace)
        return sanitize_input(v, max_length=100)

    @field_validator("role_description")
    @classmethod
    def validate_role_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if len(v) < 30:
            raise ValueError("Role description must be at least 30 characters")
        if len(v) > 8000:
            raise ValueError("Role description must be at most 8000 characters")
        return sanitize_input(v)


class UserSelectionData(BaseModel):
    company_name: str
    role: str
    role_description: str | None
    session_id: str


class UserSelectionResponse(BaseModel):
    success: bool = True
    data: UserSelectionData
    next_step: str = "/api/generate-tasks"


class ErrorDetails(BaseModel):
    code: str
    message: str
    details: dict[str, str]


class UserSelectionError(BaseModel):
    success: bool = False
    error: ErrorDetails
