import re

from pydantic import BaseModel, Field, field_validator


class UserSelectionRequest(BaseModel):
    company_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Company name (2-100 characters, no emojis or repeated symbols)",
    )
    role: str = Field(..., description="Role ID from predefined roles")
    role_description: str | None = Field(
        None,
        description="Optional role description (1-8000 characters if provided)",
    )

    @field_validator("company_name")
    @classmethod
    def validate_company_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Company name is required")
        if len(v) < 2:
            raise ValueError("Company name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Company name must be at most 100 characters")

        # Check for emojis (Unicode emoji ranges)
        emoji_pattern = re.compile(
            r"[\U0001F600-\U0001F64F"  # emoticons
            r"\U0001F300-\U0001F5FF"  # symbols & pictographs
            r"\U0001F680-\U0001F6FF"  # transport & map symbols
            r"\U0001F1E0-\U0001F1FF"  # flags
            r"\U00002702-\U000027B0"  # dingbats
            r"\U0001F900-\U0001F9FF"  # supplemental symbols
            r"\U0001FA00-\U0001FA6F"  # chess symbols
            r"\U0001FA70-\U0001FAFF"  # symbols extended-A
            r"\U00002600-\U000026FF"  # misc symbols
            r"]"
        )
        if emoji_pattern.search(v):
            raise ValueError("Company name cannot contain emojis")

        # Check for repeated symbols (3+ consecutive same non-alphanumeric character)
        if re.search(r"([^\w\s])\1{2,}", v):
            raise ValueError("Company name cannot contain repeated symbols")

        return v

    @field_validator("role_description")
    @classmethod
    def validate_role_description(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if len(v) < 1:
            raise ValueError("Role description must be at least 1 character")
        if len(v) > 8000:
            raise ValueError("Role description must be at most 8000 characters")
        return v


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
