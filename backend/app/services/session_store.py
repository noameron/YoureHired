from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.company_info import CompanySummary


@dataclass
class Session:
    session_id: str
    company_name: str
    role: str
    role_description: str | None
    company_summary: "CompanySummary | None" = None
    created_at: datetime = field(default_factory=datetime.utcnow)


class SessionStore:
    def __init__(self, ttl_hours: int = 24):
        self._sessions: dict[str, Session] = {}
        self._ttl = timedelta(hours=ttl_hours)

    def create(
        self,
        session_id: str,
        company_name: str,
        role: str,
        role_description: str | None = None,
    ) -> Session:
        session = Session(
            session_id=session_id,
            company_name=company_name,
            role=role,
            role_description=role_description,
        )
        self._sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        session = self._sessions.get(session_id)
        if session and datetime.utcnow() - session.created_at < self._ttl:
            return session
        return None

    def update_company_summary(
        self, session_id: str, company_summary: "CompanySummary"
    ) -> bool:
        """Update session with company research summary."""
        session = self.get(session_id)
        if session:
            session.company_summary = company_summary
            return True
        return False


session_store = SessionStore()
