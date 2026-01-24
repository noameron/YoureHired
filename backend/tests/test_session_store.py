import pytest
from app.services.session_store import SessionStore, Session


class TestSessionStore:
    def test_create_session(self):
        store = SessionStore()
        session = store.create("id-1", "Google", "backend_developer")
        assert session.session_id == "id-1"
        assert session.company_name == "Google"

    def test_get_existing_session(self):
        store = SessionStore()
        store.create("id-1", "Google", "backend_developer")
        session = store.get("id-1")
        assert session is not None
        assert session.company_name == "Google"

    def test_get_nonexistent_session(self):
        store = SessionStore()
        assert store.get("nonexistent") is None
