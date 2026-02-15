from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import TypedDict


class RoleDict(TypedDict):
    id: str
    label: str


PREDEFINED_ROLES: list[RoleDict] = [
    {"id": "frontend_developer", "label": "Frontend Developer"},
    {"id": "backend_developer", "label": "Backend Developer"},
    {"id": "fullstack_developer", "label": "Full Stack Developer"},
    {"id": "devops_engineer", "label": "DevOps Engineer"},
    {"id": "qa_engineer", "label": "QA Engineer"},
    {"id": "data_engineer", "label": "Data Engineer"},
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Google Gemini Configuration (free tier fallback)
    google_api_key: str = ""
    gemini_model: str = "litellm/gemini/gemini-2.5-flash"

    # Agent Timeouts (seconds)
    company_research_agent_timeout: float = 60.0
    drill_generation_agent_timeout: float = 90.0

    # GitHub Scout Configuration
    github_token: str = ""  # Personal access token with public_repo read access
    scout_db_path: str = "data/scout.db"  # SQLite DB; dir auto-created by GitHubReposDB
    scout_analysis_timeout: float = 60.0  # Seconds per LLM analysis batch
    scout_max_repos: int = 50  # Max repos returned from GitHub search
    scout_max_daily_analyses: int = 100  # Rate limit: analyses per day
    scout_batch_size: int = 10  # Repos analyzed per LLM call


settings = Settings()
