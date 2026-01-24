from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Session:
    session_id: str
    company_name: str
    role: str
    role_description: str | None
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


session_store = SessionStore()
