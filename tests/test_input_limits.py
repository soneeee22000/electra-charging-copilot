"""Request validation and error hygiene on the public HTTP surface."""

from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from app.main import MAX_CITY_CHARS, MAX_QUESTION_CHARS, app  # noqa: E402

client = TestClient(app)

VALID_ROUTE = {"origin": "Paris", "destination": "Bordeaux", "current_battery_pct": 70}


@pytest.mark.parametrize("start_pct", [-1, 101])
def test_route_rejects_out_of_range_battery(start_pct: int) -> None:
    """current_battery_pct outside 0-100 is a validation error."""
    resp = client.post("/route", json=VALID_ROUTE | {"current_battery_pct": start_pct})
    assert resp.status_code == 422


def test_route_rejects_oversized_city() -> None:
    """An oversized city name is rejected before it reaches the planner."""
    resp = client.post("/route", json=VALID_ROUTE | {"origin": "x" * (MAX_CITY_CHARS + 1)})
    assert resp.status_code == 422


def test_chat_rejects_oversized_question(monkeypatch: pytest.MonkeyPatch) -> None:
    """An oversized question is rejected without invoking the agent."""
    agent = pytest.importorskip("app.agent")

    def _must_not_run(question: str) -> str:
        raise AssertionError("agent invoked")

    monkeypatch.setattr(agent, "ask", _must_not_run)
    resp = client.post("/chat", json={"question": "q" * (MAX_QUESTION_CHARS + 1)})
    assert resp.status_code == 422


def test_chat_error_does_not_leak_exception_text(monkeypatch: pytest.MonkeyPatch) -> None:
    """A failing agent yields a 503 whose body does not echo internal error text."""
    agent = pytest.importorskip("app.agent")

    def _boom(question: str) -> str:
        raise RuntimeError("internal-detail-7f3a")

    monkeypatch.setattr(agent, "ask", _boom)
    resp = client.post("/chat", json={"question": "Is ELEC-PAR-01 free?"})
    assert resp.status_code == 503
    assert "internal-detail-7f3a" not in resp.text
